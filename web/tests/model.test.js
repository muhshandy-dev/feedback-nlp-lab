// Paritas inferensi browser dengan scikit-learn pada seluruh ulasan test.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { charWbNgrams, explain, normalize, predict, prepare, wordNgrams } from '../src/lib/tfidf.js';

const load = (f) => JSON.parse(readFileSync(new URL(`../public/data/${f}`, import.meta.url), 'utf8'));
const model = prepare(load('model.json'));
const preds = load('test_predictions.json');

test('normalisasi sama dengan Python', () => {
  assert.equal(normalize('  Enak BANGET!!! harga: Rp15.000  '), 'enak banget harga rp15 000');
  assert.equal(normalize('[URL] café'), 'url caf');
});

test('char_wb meniru sklearn, termasuk kata pendek', () => {
  assert.deepEqual(charWbNgrams('ok', [2, 5]).grams.map((g) => g[0]), [' o', 'ok', 'k ', ' ok', 'ok ', ' ok ']);
  assert.deepEqual(charWbNgrams('a', [2, 5]).grams.map((g) => g[0]), [' a', 'a ', ' a ']);
});

test('n-gram kata 1-2', () => {
  assert.deepEqual(wordNgrams('tidak enak x sekali', [1, 2]).grams.map((g) => g[0]), [
    'tidak', 'enak', 'sekali', 'tidak enak', 'enak sekali',
  ]);
});

test('probabilitas browser = scikit-learn untuk 400 ulasan test (toleransi 1e-5)', () => {
  let maxDiff = 0;
  for (const r of preds.rows) {
    const out = predict(model, r.text);
    assert.equal(out.label, r.tfidf, `id ${r.id}`);
    out.probs.forEach((p, i) => { maxDiff = Math.max(maxDiff, Math.abs(p - r.tfidf_probs[i])); });
  }
  assert.ok(maxDiff < 1e-5, `selisih maksimum ${maxDiff}`);
});

test('kontribusi kata menjumlah ke selisih skor kelas terpilih', () => {
  const r = predict(model, 'Makanannya enak sekali, tapi pelayanannya lambat dan mengecewakan.');
  const e = explain(model, r);
  const c = model.labels.indexOf(r.label);
  const others = [0, 1, 2].filter((k) => k !== c);
  const expected = r.scores[c] - model.intercept[c]
    - others.reduce((s, k) => s + r.scores[k] - model.intercept[k], 0) / others.length;
  const sum = e.contributions.reduce((s, x) => s + x.value, 0);
  assert.ok(Math.abs(sum - expected) < 1e-9, `${sum} vs ${expected}`);
});

test('teks kosong tidak error', () => {
  const r = predict(model, '');
  assert.equal(r.probs.length, 3);
  assert.equal(r.matched, 0);
});
