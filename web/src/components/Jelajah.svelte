<script>
  import { LABEL_ID, int, pct } from '../lib/format.js';

  let { data } = $props();
  const rows = $derived(data.predictions.rows);
  const L = $derived(data.results.labels);
  const K = $derived(data.results.topics.k);
  const hasEnc = $derived(data.results.encoder.status === 'dijalankan');

  let model = $state('tfidf');
  let truth = $state('');
  let pred = $state('');
  let status = $state('');
  let topic = $state('');
  let q = $state('');
  let limit = $state(25);

  const key = $derived(model === 'encoder' && hasEnc ? 'encoder' : 'tfidf');
  const filtered = $derived(
    rows.filter((r) =>
      (!truth || r.label === truth)
      && (!pred || r[key] === pred)
      && (!status || (status === 'benar') === (r.label === r[key]))
      && (topic === '' || r.topic === Number(topic))
      && (!q || r.text.toLowerCase().includes(q.toLowerCase()))),
  );
  const wrong = $derived(rows.filter((r) => r.label !== r[key]).length);

  // Pasangan kesalahan terbanyak untuk analisis kesalahan.
  const pairs = $derived.by(() => {
    const m = new Map();
    for (const r of rows) {
      if (r.label === r[key]) continue;
      const k = `${r.label}>${r[key]}`;
      m.set(k, (m.get(k) || 0) + 1);
    }
    return [...m.entries()].sort((a, b) => b[1] - a[1]).map(([k, n]) => ({ truth: k.split('>')[0], pred: k.split('>')[1], n }));
  });

  function showPair(p) {
    truth = p.truth;
    pred = p.pred;
    status = '';
    limit = 25;
  }

  function reset() {
    truth = pred = status = topic = q = '';
    limit = 25;
  }

  const conf = (r) => Math.max(...r[`${key}_probs`]);
</script>

<section class="stack">
  <h1>Jelajah 400 ulasan uji</h1>
  <p class="muted">Setiap ulasan uji beserta label asli dan prediksi model. Gunakan filter untuk mempelajari di mana model salah.</p>
</section>

<section class="card stack">
  <h2 class="h3">Pola kesalahan {key === 'tfidf' ? 'TF-IDF' : 'IndoBERT'}</h2>
  <p class="small muted num">{int(wrong)} dari {int(rows.length)} ulasan salah ditebak ({pct(wrong / rows.length)}). Klik untuk memfilter.</p>
  <div class="pairs">
    {#each pairs as p}
      <button class="btn pair" onclick={() => showPair(p)}>
        <span><span class="dot {p.truth}"></span> {LABEL_ID[p.truth]} → <span class="dot {p.pred}"></span> {LABEL_ID[p.pred]}</span>
        <span class="num strong">{p.n}</span>
      </button>
    {/each}
  </div>
</section>

<section class="card filters" aria-label="Filter">
  {#if hasEnc}
    <label>Model<select bind:value={model}><option value="tfidf">TF-IDF</option><option value="encoder">IndoBERT</option></select></label>
  {/if}
  <label>Label asli<select bind:value={truth}><option value="">Semua</option>{#each L as l}<option value={l}>{LABEL_ID[l]}</option>{/each}</select></label>
  <label>Prediksi<select bind:value={pred}><option value="">Semua</option>{#each L as l}<option value={l}>{LABEL_ID[l]}</option>{/each}</select></label>
  <label>Status<select bind:value={status}><option value="">Semua</option><option value="benar">Benar</option><option value="salah">Salah</option></select></label>
  <label>Topik<select bind:value={topic}><option value="">Semua</option>{#each Array.from({ length: K }, (_, i) => i) as t}<option value={String(t)}>Topik {t + 1}</option>{/each}</select></label>
  <label class="q">Cari kata<input type="search" bind:value={q} placeholder="misal: sinyal" /></label>
  <button class="btn" onclick={reset}>Atur ulang</button>
</section>

<p class="small muted count num" aria-live="polite">{int(filtered.length)} ulasan cocok</p>
<ul class="list">
  {#each filtered.slice(0, limit) as r (r.id)}
    {@const ok = r.label === r[key]}
    <li class="card item" class:bad={!ok}>
      <p class="txt">{r.text}</p>
      <p class="meta small">
        <span class="badge"><span class="dot {r.label}"></span> Asli: {LABEL_ID[r.label]}</span>
        <span class="badge"><span class="dot {r[key]}"></span> Prediksi: {LABEL_ID[r[key]]} · {pct(conf(r), 0)}</span>
        <span class="badge">{ok ? 'Benar' : 'Salah'}</span>
        {#if r.topic >= 0}<span class="badge">Topik {r.topic + 1}</span>{/if}
        <span class="muted">id {r.id}</span>
      </p>
    </li>
  {:else}
    <li class="muted">Tidak ada ulasan yang cocok dengan filter.</li>
  {/each}
</ul>
{#if filtered.length > limit}
  <button class="btn more" onclick={() => (limit += 25)}>Tampilkan 25 lagi</button>
{/if}

<style>
  section + section { margin-top: 16px; }
  .pairs { display: grid; gap: 6px; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); }
  .pair { display: flex; justify-content: space-between; gap: 8px; align-items: center; font-weight: 400; }
  .pair > span:first-child { display: inline-flex; align-items: center; gap: 5px; flex-wrap: wrap; }
  .strong { font-weight: 600; }
  .filters { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: end; }
  .filters label { display: grid; gap: 3px; font-size: 0.82rem; font-weight: 600; color: var(--muted); min-width: 0; }
  .filters .q { flex: 1 1 180px; }
  select, input {
    font: inherit; font-size: 0.92rem; color: var(--ink); background: var(--bg);
    border: 1px solid var(--line); border-radius: 8px; padding: 7px 9px; min-height: 38px; max-width: 100%;
  }
  .count { margin: 14px 0 8px; }
  .list { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
  .item.bad { border-left: 3px solid var(--neg); }
  .txt { overflow-wrap: anywhere; }
  .meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-top: 8px; }
  .more { margin-top: 12px; }
</style>
