// Hitung ulang metrik dari prediksi mentah, terpisah dari angka yang ditulis Python.

export function confusion(rows, key, labels) {
  const m = labels.map(() => labels.map(() => 0));
  for (const r of rows) m[labels.indexOf(r.label)][labels.indexOf(r[key])] += 1;
  return m;
}

export function perClass(m, labels) {
  return labels.map((lab, i) => {
    const tp = m[i][i];
    const support = m[i].reduce((a, b) => a + b, 0);
    const predicted = m.reduce((s, row) => s + row[i], 0);
    const precision = predicted ? tp / predicted : 0;
    const recall = support ? tp / support : 0;
    const f1 = precision + recall ? (2 * precision * recall) / (precision + recall) : 0;
    return { label: lab, precision, recall, f1, support };
  });
}

export function macroF1(m, labels) {
  const pc = perClass(m, labels);
  return pc.reduce((s, c) => s + c.f1, 0) / pc.length;
}

export function accuracy(m) {
  const n = m.flat().reduce((a, b) => a + b, 0);
  return m.reduce((s, row, i) => s + row[i], 0) / n;
}
