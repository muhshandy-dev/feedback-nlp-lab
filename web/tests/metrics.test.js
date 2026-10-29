// Angka di results.json dihitung ulang dari prediksi mentah, terpisah dari Python.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { accuracy, confusion, macroF1, perClass } from '../src/lib/metrics.js';

const load = (f) => JSON.parse(readFileSync(new URL(`../public/data/${f}`, import.meta.url), 'utf8'));
const results = load('results.json');
const preds = load('test_predictions.json');
const L = results.labels;

for (const key of ['tfidf', 'encoder']) {
  test(`metrik ${key} cocok dengan results.json`, { skip: results[key].status === 'belum_dijalankan' }, () => {
    const m = confusion(preds.rows, key, L);
    assert.deepEqual(m, results[key].test.confusion);
    assert.ok(Math.abs(macroF1(m, L) - results[key].test.macro_f1) < 1e-6);
    assert.ok(Math.abs(accuracy(m) - results[key].test.accuracy) < 1e-6);
    perClass(m, L).forEach((c) => {
      assert.ok(Math.abs(c.f1 - results[key].test.per_class[c.label].f1) < 1e-6);
    });
  });
}

test('topik setiap ulasan test valid', () => {
  const k = results.topics.k;
  for (const r of preds.rows) assert.ok(r.topic >= -1 && r.topic < k);
});
