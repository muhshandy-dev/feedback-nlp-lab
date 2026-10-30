// Uji e2e: semua halaman di 4 lebar, tema terang dan gelap, CSP, aksesibilitas (axe), interaksi.
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { predict, prepare } from '../src/lib/tfidf.js';
import { startServer } from './serve.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const OUT = process.env.SHOT_DIR || join(here, '..', '..', 'screenshots');
mkdirSync(OUT, { recursive: true });
const WIDTHS = process.env.WIDTHS ? process.env.WIDTHS.split(',').map(Number) : [320, 375, 768, 1440];
const VIEWS = ['ringkasan', 'uji', 'topik', 'model', 'jelajah', 'metode'];
const CHARTS = { ringkasan: 1, topik: 1, model: 3 };
const dataDir = join(here, '..', 'public', 'data');
const results = JSON.parse(readFileSync(join(dataDir, 'results.json')));
const preds = JSON.parse(readFileSync(join(dataDir, 'test_predictions.json')));
const model = prepare(JSON.parse(readFileSync(join(dataDir, 'model.json'))));

const failures = [];
let checks = 0;
const ok = (cond, msg) => { checks++; if (!cond) { failures.push(msg); console.error('GAGAL:', msg); } };

const server = await startServer();
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});

function watch(page, problems) {
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) problems.push(`${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('requestfailed', (r) => problems.push(`requestfailed: ${r.url()}`));
  page.on('request', (r) => { if (!r.url().startsWith(base)) problems.push(`permintaan luar: ${r.url()}`); });
}

async function open(page, view) {
  await page.goto(`${base}/#${view}`);
  await page.waitForSelector(`#tab-${view}[aria-selected="true"]`);
  await page.waitForSelector('main h1');
  const n = CHARTS[view] || 0;
  if (n) await page.waitForFunction((k) => document.querySelectorAll('main .chart canvas').length >= k, n);
  await page.waitForTimeout(450);
}

const schemes = (w) => (w === 375 || w === 1440 ? ['light', 'dark'] : ['light']);

for (const width of WIDTHS) {
  for (const scheme of schemes(width)) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme, reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    const problems = [];
    watch(page, problems);
    for (const view of VIEWS) {
      await open(page, view);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (overflow > 0) {
        const culprits = await page.evaluate(() => [...document.querySelectorAll('body *')]
          .filter((el) => el.getBoundingClientRect().right > window.innerWidth + 0.5 && !el.closest('.table-scroll, .tabs, .sr-only'))
          .slice(0, 4).map((el) => `${el.tagName.toLowerCase()}.${String(el.className.baseVal ?? el.className).split(' ')[0]}`).join(', '));
        ok(false, `${view} @${width}: geser horizontal ${overflow}px (${culprits})`);
      }
      const text = await page.evaluate(() => document.body.innerText);
      ok(!/[—–]/.test(text), `${view} @${width}: ada tanda pisah panjang`);
      ok(!/\b(AI05|NaN|undefined|null)\b/.test(text), `${view} @${width}: teks internal atau nilai kosong terlihat`);
      ok(!/[a-z]_[a-z]/.test(text), `${view} @${width}: garis bawah terlihat`);
      await page.screenshot({ path: join(OUT, `${view}-${width}-${scheme === 'dark' ? 'gelap' : 'terang'}.png`), fullPage: true });
      if (width === 1440 || width === 375) {
        const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
        for (const v of axe.violations) ok(false, `axe ${view} @${width} ${scheme}: ${v.id} (${v.nodes.length}) ${v.help}`);
      }
    }
    ok(problems.length === 0, `@${width} ${scheme}: ${problems.slice(0, 5).join(' | ')}`);
    await ctx.close();
  }
}

// Interaksi pada satu konteks desktop.
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const problems = [];
  watch(page, problems);

  // Uji ulasan: label dan probabilitas di layar sama dengan inferensi JS yang paritasnya sudah diuji.
  await open(page, 'uji');
  const samples = [
    'Pelayanannya buruk sekali, makanannya dingin dan mahal. Saya kecewa.',
    'Tempatnya nyaman, makanannya enak, pelayannya ramah. Pasti kembali lagi!',
    'Besok saya akan ke kantor cabang untuk mengurus kartu.',
  ];
  for (const s of samples) {
    await page.fill('#ulasan', s);
    await page.waitForTimeout(100);
    const shown = await page.textContent('.verdict .big');
    const exp = predict(model, s);
    const name = { negative: 'Negatif', neutral: 'Netral', positive: 'Positif' }[exp.label];
    ok(shown.includes(name), `uji: layar "${shown.trim()}" tetapi model JS ${name} untuk "${s}"`);
    const marks = await page.locator('.hl mark').count();
    ok(marks === s.split(/\s+/).filter(Boolean).length, `uji: jumlah kata disorot ${marks}`);
  }
  await page.fill('#ulasan', '');
  ok(await page.isVisible('text=Tulis ulasan untuk melihat prediksi.'), 'uji: keadaan kosong tidak tampil');
  await page.click('.ex-btn >> nth=0');
  ok((await page.inputValue('#ulasan')).length > 0, 'uji: contoh tidak mengisi textarea');
  ok(await page.isVisible('text=Ulasan ini ada di test set.'), 'uji: contoh test set tidak dikenali');
  await page.click('.seg button >> nth=2');
  ok(await page.getAttribute('.seg button >> nth=2', 'aria-pressed') === 'true', 'uji: tombol kelas tidak aktif');

  // Jelajah: filter "salah" sama dengan jumlah kesalahan di data.
  await open(page, 'jelajah');
  const wrong = preds.rows.filter((r) => r.label !== r.tfidf).length;
  await page.getByLabel('Status').selectOption('salah');
  ok((await page.textContent('.count')).includes(String(wrong)), `jelajah: hitungan salah bukan ${wrong}`);
  if (results.encoder.status === 'dijalankan') {
    const wrongEnc = preds.rows.filter((r) => r.label !== r.encoder).length;
    await page.getByLabel('Model').selectOption('encoder');
    ok((await page.textContent('.count')).includes(String(wrongEnc)), `jelajah: hitungan salah IndoBERT bukan ${wrongEnc}`);
    await page.getByLabel('Model').selectOption('tfidf');
  }
  await page.click('.pair >> nth=0');
  const pairCount = await page.textContent('.pair >> nth=0 >> .strong');
  ok((await page.textContent('.count')).includes(pairCount.trim()), 'jelajah: filter pasangan kesalahan tidak cocok');
  await page.click('text=Atur ulang');
  ok((await page.textContent('.count')).includes('400'), 'jelajah: atur ulang tidak mengembalikan 400');
  await page.fill('input[type=search]', 'zzzzqq');
  ok(await page.isVisible('text=Tidak ada ulasan yang cocok'), 'jelajah: keadaan kosong tidak tampil');

  // Model: tabel confusion untuk pembaca layar sama dengan hasil.
  await open(page, 'model');
  const cells = await page.$$eval('table.sr-only tbody td', (tds) => tds.map((td) => Number(td.textContent)));
  ok(JSON.stringify(cells) === JSON.stringify(results.tfidf.test.confusion.flat()), 'model: confusion matrix tidak cocok');
  const f1Text = await page.textContent('table tbody tr >> nth=1');
  ok(f1Text.includes(results.tfidf.test.macro_f1.toFixed(3).replace('.', ',')), 'model: macro-F1 TF-IDF tidak tampil');
  if (results.encoder.status !== 'dijalankan') ok(await page.isVisible('tr.pending'), 'model: status encoder belum dijalankan tidak tampil');
  else {
    const encRow = await page.textContent('table tbody tr >> nth=2');
    ok(encRow.includes(results.encoder.test.macro_f1.toFixed(3).replace('.', ',')), 'model: macro-F1 IndoBERT tidak tampil');
    await page.click('button:has-text("IndoBERT")');
    const encCells = await page.$$eval('table.sr-only tbody td', (tds) => tds.map((td) => Number(td.textContent)));
    ok(JSON.stringify(encCells) === JSON.stringify(results.encoder.test.confusion.flat()), 'model: confusion matrix IndoBERT tidak cocok');
    ok(await page.isVisible('text=p < 0,001') || results.encoder.vs_tfidf.mcnemar.p_value >= 0.001, 'model: p McNemar tidak tampil');
  }

  // Navigasi keyboard pada tab dan tema.
  await page.focus('#tab-model');
  await page.keyboard.press('ArrowRight');
  ok(await page.getAttribute('#tab-jelajah', 'aria-selected') === 'true', 'tab: panah kanan tidak pindah');
  await page.click('.theme button >> nth=2');
  ok(await page.evaluate(() => document.documentElement.dataset.theme) === 'dark', 'tema gelap tidak aktif');

  ok(problems.length === 0, `interaksi: ${problems.slice(0, 5).join(' | ')}`);
  await ctx.close();
}

await browser.close();
server.close();
console.log(`${checks} pemeriksaan, ${failures.length} gagal`);
if (failures.length) process.exit(1);
