<script>
  import Chart from './Chart.svelte';
  import { LABEL_ID, ci, dec, int, pct } from '../lib/format.js';

  let { data, theme, go } = $props();
  const r = $derived(data.results);
  const L = $derived(r.labels);
  const totals = $derived(
    Object.fromEntries(L.map((lab) => [lab, Object.values(r.dataset.label_counts).reduce((s, c) => s + c[lab], 0)])),
  );
  const N = $derived(Object.values(totals).reduce((a, b) => a + b, 0));
  const enc = $derived(r.encoder);

  const splitName = { train: 'Latih', valid: 'Validasi', test: 'Uji' };
  const distOption = $derived((c) => ({
    grid: { left: 70, right: 16, top: 30, bottom: 28 },
    legend: { top: 0, left: 0, textStyle: { color: c.muted }, itemWidth: 12, itemHeight: 10 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'value', max: 1, axisLabel: { formatter: (v) => `${Math.round(v * 100)}%`, color: c.muted }, splitLine: { lineStyle: { color: c.grid } } },
    yAxis: { type: 'category', inverse: true, data: Object.keys(r.dataset.sizes).map((s) => `${splitName[s]} (${r.dataset.sizes[s]})`), axisLabel: { color: c.ink }, axisLine: { lineStyle: { color: c.line } }, axisTick: { show: false } },
    series: L.map((lab) => ({
      name: LABEL_ID[lab],
      type: 'bar',
      stack: 'x',
      barWidth: 18,
      itemStyle: { color: c[lab] },
      data: Object.keys(r.dataset.sizes).map((s) => r.dataset.label_counts[s][lab] / r.dataset.sizes[s]),
      tooltip: { valueFormatter: (v) => pct(v) },
    })),
  }));
</script>

<section class="stack">
  <h1>Apa yang dikatakan ulasan berbahasa Indonesia?</h1>
  <p class="lead">
    Laboratorium kecil untuk mengklasifikasikan sentimen ulasan (negatif, netral, positif) dan menemukan topik yang dibicarakan.
    Baseline TF-IDF dilatih sungguhan dan berjalan langsung di browser Anda; pembanding encoder IndoBERT dievaluasi pada test set yang sama.
  </p>
  <div class="badges">
    <span class="badge">Data: {int(N)} ulasan NusaX-Senti</span>
    <span class="badge">TF-IDF: dihitung di browser</span>
    {#if enc.status === 'dijalankan'}
      <span class="badge">IndoBERT: hasil precomputed</span>
    {:else}
      <span class="badge warn">IndoBERT: belum dievaluasi</span>
    {/if}
  </div>
</section>

<section class="grid three cards" aria-label="Kartu sentimen">
  {#each L as lab}
    <article class="card sent {lab}">
      <header class="row">
        <h2 class="h3"><span class="dot {lab}"></span> {LABEL_ID[lab]}</h2>
        <span class="num big">{pct(totals[lab] / N, 0)}</span>
      </header>
      <div class="meter" aria-hidden="true"><span class="fill {lab}" style:width="{(totals[lab] / N) * 100}%"></span></div>
      <p class="muted small num">{int(totals[lab])} dari {int(N)} ulasan berlabel</p>
      <p class="small kw-title">Kata paling khas</p>
      <ul class="kw">
        {#each r.keywords[lab].slice(0, 6) as k}
          <li><span>{k.word}</span><span class="muted num">z {dec(k.z, 1)}</span></li>
        {/each}
      </ul>
    </article>
  {/each}
</section>

<section class="grid three metrics" aria-label="Hasil utama">
  <article class="card">
    <p class="muted small">TF-IDF + regresi logistik</p>
    <p class="metric num">{dec(r.tfidf.test.macro_f1)}</p>
    <p class="small">macro-F1 pada 400 ulasan uji</p>
    <p class="muted small num">95% CI {ci(r.tfidf.test.macro_f1_ci95)}</p>
  </article>
  <article class="card">
    <p class="muted small">Encoder IndoBERT (fine-tuned)</p>
    {#if enc.status === 'dijalankan'}
      <p class="metric num">{dec(enc.test.macro_f1)}</p>
      <p class="small">macro-F1 pada 400 ulasan uji</p>
      <p class="muted small num">95% CI {ci(enc.test.macro_f1_ci95)}</p>
    {:else}
      <p class="metric pending">Belum ada</p>
      <p class="small">Belum dievaluasi. Angka tidak ditampilkan sampai fine-tuning benar-benar dijalankan.</p>
    {/if}
  </article>
  <article class="card">
    <p class="muted small">Pembanding paling sederhana</p>
    <p class="metric num">{dec(r.majority.test.macro_f1)}</p>
    <p class="small">macro-F1 jika selalu menebak "{LABEL_ID[r.majority.predicts]}"</p>
    <p class="muted small">Batas bawah: model yang berguna harus jauh di atas ini.</p>
  </article>
</section>

<section class="grid two">
  <article class="card">
    <h2 class="h3">Distribusi label per split</h2>
    <p class="muted small">Proporsi kelas dijaga serupa di latih, validasi, dan uji.</p>
    <Chart option={distOption} {theme} height={170} label="Proporsi negatif, netral, positif pada split latih, validasi, dan uji" />
  </article>
  <article class="card">
    <h2 class="h3">{r.topics.k} topik yang ditemukan</h2>
    <p class="muted small">NMF di atas TF-IDF; jumlah topik dipilih dengan koherensi pada data yang tidak dilihat.</p>
    <ol class="topics">
      {#each r.topics.topics as t}
        <li>
          <span class="tw">{t.words.slice(0, 4).map((w) => w.word).join(', ')}</span>
          <span class="muted num small">{int(t.size)} ulasan</span>
        </li>
      {/each}
    </ol>
    <button class="btn" onclick={() => go('topik')}>Lihat topik</button>
  </article>
</section>

<style>
  section + section { margin-top: 20px; }
  .lead { font-size: 1.04rem; color: var(--muted); }
  .badges { display: flex; flex-wrap: wrap; gap: 6px; }
  .badge.warn { border-style: dashed; }
  .h3 { font-size: 1.08rem; display: flex; align-items: center; gap: 8px; }
  .row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .big { font-family: var(--display); font-size: 1.7rem; font-weight: 600; }
  .meter { height: 8px; background: var(--surface-2); border-radius: 99px; overflow: hidden; margin: 10px 0 6px; }
  .fill { display: block; height: 100%; border-radius: 99px; }
  .fill.negative { background: var(--neg); }
  .fill.neutral { background: var(--neu); }
  .fill.positive { background: var(--pos); }
  .kw-title { margin-top: 12px; font-weight: 600; }
  .kw { list-style: none; padding: 0; margin: 6px 0 0; display: grid; gap: 4px; }
  .kw li { display: flex; justify-content: space-between; gap: 8px; border-bottom: 1px dashed var(--line); padding-bottom: 3px; }
  .sent.negative { border-top: 3px solid var(--neg); }
  .sent.neutral { border-top: 3px solid var(--neu); }
  .sent.positive { border-top: 3px solid var(--pos); }
  .metric { font-family: var(--display); font-size: 2.1rem; font-weight: 600; line-height: 1.15; margin: 4px 0; }
  .metric.pending { font-size: 1.5rem; color: var(--muted); }
  .topics { margin: 10px 0 14px; padding-left: 20px; display: grid; gap: 6px; }
  .topics li { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
  .tw { font-weight: 500; }
</style>
