// Inferensi TF-IDF + regresi logistik di browser, meniru scikit-learn persis.
// Paritas dengan Python diuji di tests/model.test.js pada seluruh 400 ulasan test.

export function normalize(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

// Sama dengan TfidfVectorizer(analyzer="word", token_pattern=r"\b\w\w+\b"): setelah normalize,
// teks hanya berisi a-z, 0-9 dan spasi, jadi token = potongan spasi dengan panjang minimal 2.
// Mengembalikan daftar [ngram, indeksKata]; indeks merujuk ke semua kata (termasuk yang 1 huruf)
// supaya sama dengan indeks pada analyzer char_wb dan kontribusi bisa dikembalikan ke kata asalnya.
export function wordNgrams(norm, [minN, maxN]) {
  const words = norm.split(' ').filter(Boolean);
  const toks = words.map((w, i) => [w, i]).filter(([w]) => w.length >= 2);
  const out = [];
  for (let n = minN; n <= Math.min(maxN, toks.length); n++) {
    for (let i = 0; i + n <= toks.length; i++) {
      out.push([toks.slice(i, i + n).map((t) => t[0]).join(' '), toks[i][1]]);
    }
  }
  return { grams: out, words };
}

// Salinan sklearn _char_wb_ngrams, termasuk aturan "kata pendek hanya dihitung sekali".
export function charWbNgrams(norm, [minN, maxN]) {
  const words = norm.split(/\s+/).filter(Boolean);
  const out = [];
  words.forEach((word, wi) => {
    const w = ` ${word} `;
    for (let n = minN; n <= maxN; n++) {
      let offset = 0;
      out.push([w.slice(offset, offset + n), wi]);
      while (offset + n < w.length) {
        offset += 1;
        out.push([w.slice(offset, offset + n), wi]);
      }
      if (offset === 0) break;
    }
  });
  return { grams: out, words };
}

export function prepare(model) {
  return {
    ...model,
    analyzers: model.analyzers.map((a, k) => {
      const offset = model.analyzers.slice(0, k).reduce((s, b) => s + b.terms.length, 0);
      return { ...a, offset, index: new Map(a.terms.map((t, i) => [t, i])) };
    }),
  };
}

function vectorizeOne(a, norm) {
  const { grams, words } = a.analyzer === 'char_wb' ? charWbNgrams(norm, a.ngram_range) : wordNgrams(norm, a.ngram_range);
  const counts = new Map();
  const owners = new Map(); // indeks fitur -> Map(indeksKata -> jumlah)
  for (const [g, wi] of grams) {
    const j = a.index.get(g);
    if (j === undefined) continue;
    counts.set(j, (counts.get(j) || 0) + 1);
    if (!owners.has(j)) owners.set(j, new Map());
    const o = owners.get(j);
    o.set(wi, (o.get(wi) || 0) + 1);
  }
  const vals = new Map();
  let ss = 0;
  for (const [j, c] of counts) {
    const tf = a.sublinear_tf ? 1 + Math.log(c) : c;
    const v = tf * a.idf[j];
    vals.set(j, v);
    ss += v * v;
  }
  const norm2 = Math.sqrt(ss);
  if (norm2 > 0) for (const [j, v] of vals) vals.set(j, v / norm2);
  return { vals, owners, counts, words };
}

function softmax(z) {
  const m = Math.max(...z);
  const e = z.map((v) => Math.exp(v - m));
  const s = e.reduce((x, y) => x + y, 0);
  return e.map((v) => v / s);
}

export function predict(pm, text) {
  const norm = normalize(text);
  const parts = pm.analyzers.map((a) => ({ a, ...vectorizeOne(a, norm) }));
  const scores = pm.labels.map((_, c) => {
    let s = pm.intercept[c];
    for (const p of parts) for (const [j, v] of p.vals) s += pm.coef[c][p.a.offset + j] * v;
    return s;
  });
  const probs = softmax(scores);
  const best = probs.indexOf(Math.max(...probs));
  return { label: pm.labels[best], probs, scores, parts, norm, matched: parts.reduce((s, p) => s + p.vals.size, 0) };
}

// Kontribusi per kata terhadap kelas terpilih dibanding rata-rata kelas lain.
// Fitur n-gram dibagi ke kata pemiliknya sebanding jumlah kemunculannya di kata itu.
export function explain(pm, result, cls = result.label) {
  const c = pm.labels.indexOf(cls);
  const others = pm.labels.map((_, k) => k).filter((k) => k !== c);
  const parts = result.parts;
  const words = parts.length ? parts[0].words : [];
  const contrib = new Map();
  for (const p of parts) {
    for (const [j, v] of p.vals) {
      const col = p.a.offset + j;
      const w = pm.coef[c][col] - others.reduce((s, k) => s + pm.coef[k][col], 0) / others.length;
      const total = p.counts.get(j);
      for (const [wi, n] of p.owners.get(j)) {
        const word = p.words[wi];
        contrib.set(wi, { word, value: (contrib.get(wi)?.value || 0) + (w * v * n) / total });
      }
    }
  }
  return { words, contributions: [...contrib.entries()].map(([i, o]) => ({ index: i, ...o })) };
}
