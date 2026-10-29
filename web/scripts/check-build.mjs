// Pastikan build statis lengkap dan di bawah batas Cloudflare Pages (25 MiB per berkas).
import { readdirSync, statSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const dist = new URL('../dist/', import.meta.url).pathname;
const must = ['index.html', '_headers', 'favicon.svg', 'data/results.json', 'data/test_predictions.json', 'data/model.json'];
let fail = false;
for (const f of must) if (!existsSync(join(dist, f))) { console.error(`hilang: ${f}`); fail = true; }
let total = 0;
const walk = (d) => readdirSync(d).forEach((f) => {
  const p = join(d, f);
  const s = statSync(p);
  if (s.isDirectory()) return walk(p);
  total += s.size;
  if (s.size > 25 * 1024 * 1024) { console.error(`terlalu besar: ${p}`); fail = true; }
});
walk(dist);
console.log(`build: ${(total / 1024).toFixed(0)} KiB`);
if (fail) process.exit(1);
