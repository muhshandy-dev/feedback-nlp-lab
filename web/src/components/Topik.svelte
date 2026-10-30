<script>
  import Chart from './Chart.svelte';
  import { LABEL_ID, dec, int, pct } from '../lib/format.js';

  let { data, theme } = $props();
  const T = $derived(data.results.topics);
  const L = $derived(data.results.labels);
  const chosen = $derived(T.grid.find((g) => g.k === T.k));

  const sweepOption = $derived((c) => ({
    grid: { left: 44, right: 40, top: 76, bottom: 40 },
    legend: { top: 0, left: 0, textStyle: { color: c.muted }, itemWidth: 14, itemHeight: 8 },
    tooltip: { trigger: 'axis', valueFormatter: (v) => dec(v, 3) },
    xAxis: { type: 'category', name: 'k', nameLocation: 'middle', nameGap: 26, data: T.grid.map((g) => g.k), axisLabel: { color: c.muted }, axisLine: { lineStyle: { color: c.line } } },
    yAxis: [
      { type: 'value', min: -1, max: 0.25, axisLabel: { color: c.muted }, splitLine: { lineStyle: { color: c.grid } } },
      { type: 'value', min: 0, max: 1, axisLabel: { color: c.muted }, splitLine: { show: false } },
    ],
    series: [
      { name: 'NPMI held-out', type: 'line', data: T.grid.map((g) => g.npmi_heldout), itemStyle: { color: c.positive }, lineStyle: { width: 2.5 }, symbolSize: 7,
        markLine: { symbol: 'none', label: { formatter: `k = ${T.k} dipilih`, color: c.ink, position: 'insideEndTop' }, lineStyle: { color: c.ink, type: 'dashed' }, data: [{ xAxis: String(T.k) }] } },
      { name: 'NPMI topik acak', type: 'line', data: T.grid.map((g) => g.npmi_random), itemStyle: { color: c.neutral }, lineStyle: { type: 'dotted', width: 2 }, symbolSize: 5 },
      { name: 'Stabilitas 5 seed', type: 'line', yAxisIndex: 1, data: T.grid.map((g) => g.stability), itemStyle: { color: c.negative }, lineStyle: { width: 2 }, symbolSize: 6 },
    ],
  }));
</script>

<section class="stack">
  <h1>Topik yang dibicarakan</h1>
  <p class="muted">
    NMF di atas TF-IDF kata (kata henti dibuang) dilatih pada 600 ulasan latih dan validasi.
    Jumlah topik dipilih dengan aturan yang dikunci sebelumnya: koherensi NPMI tertinggi pada 400 ulasan uji (tidak dipakai untuk melatih), di antara k yang stabilitasnya minimal 0,5.
  </p>
</section>

<section class="grid three kpis" aria-label="Konsistensi topik">
  <div class="card"><p class="muted small">NPMI held-out (k = {T.k})</p><p class="kpi num">{dec(chosen.npmi_heldout)}</p><p class="small muted">Topik acak: {dec(chosen.npmi_random)}. Skala −1 sampai 1.</p></div>
  <div class="card"><p class="muted small">Stabilitas antar 5 seed</p><p class="kpi num">{dec(chosen.stability)}</p><p class="small muted">Jaccard kata top-10 setelah topik dipasangkan.</p></div>
  <div class="card"><p class="muted small">Keragaman kata</p><p class="kpi num">{pct(chosen.diversity, 0)}</p><p class="small muted">Kata top-10 yang unik antar topik.</p></div>
</section>

<section class="grid two topic-grid">
  {#each T.topics as t}
    {@const total = L.reduce((s, l) => s + t.sentiment[l], 0)}
    <article class="card topic">
      <header class="row">
        <h2 class="h3">Topik {t.id + 1}</h2>
        <span class="muted small num">{int(t.size)} ulasan · NPMI {dec(t.npmi_heldout, 2)}</span>
      </header>
      <ul class="words" aria-label="Kata teratas dan bobot relatifnya">
        {#each t.words as w}
          <li><span class="w">{w.word}</span><span class="wt"><span class="wf" style:width="{w.weight * 100}%"></span></span></li>
        {/each}
      </ul>
      <p class="small lbl">Campuran sentimen (label asli)</p>
      <div class="stackbar" role="img" aria-label={L.map((l) => `${LABEL_ID[l]} ${pct(t.sentiment[l] / total, 0)}`).join(', ')}>
        {#each L as l}<span class={l} style:width="{(t.sentiment[l] / total) * 100}%"></span>{/each}
      </div>
      <p class="small muted legend">{#each L as l}<span><span class="dot {l}"></span> {LABEL_ID[l]} {pct(t.sentiment[l] / total, 0)}</span>{/each}</p>
      <details>
        <summary class="small">Ulasan paling mewakili</summary>
        <ul class="small examples">{#each t.examples as e}<li>{e}</li>{/each}</ul>
      </details>
      {#if t.npmi_heldout < -0.3}
        <p class="small warn">Koherensi rendah: kata-katanya jarang muncul bersama di ulasan uji. Anggap topik ini campuran, bukan tema yang jelas.</p>
      {/if}
    </article>
  {/each}
</section>

<section class="card">
  <h2 class="h3">Pemilihan jumlah topik</h2>
  <p class="muted small">NPMI di atas garis topik acak berarti kata-kata dalam topik memang sering muncul bersama. Makin banyak topik, makin kecil korpus per topik, sehingga koherensi turun. Sumbu kiri: NPMI (−1 sampai 0,25). Sumbu kanan: stabilitas (0 sampai 1).</p>
  <Chart option={sweepOption} {theme} height={300} label="NPMI held-out, NPMI topik acak, dan stabilitas untuk k = 4 sampai 12" />
  <p class="small muted">Catatan jujur: korpus hanya 1.000 ulasan pendek dari beberapa domain, jadi topik yang lebih halus tidak koheren. Dataset yang lebih besar dan seragam (misalnya PRDECT-ID) diharapkan menghasilkan topik yang lebih tajam, tetapi belum diuji.</p>
</section>

<style>
  section + section { margin-top: 18px; }
  .kpi { font-family: var(--display); font-size: 1.9rem; font-weight: 600; margin: 4px 0; }
  .row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; flex-wrap: wrap; }
  .words { list-style: none; padding: 0; margin: 12px 0; display: grid; gap: 5px; }
  .words li { display: grid; grid-template-columns: minmax(90px, 40%) 1fr; gap: 10px; align-items: center; }
  .w { font-weight: 500; overflow-wrap: anywhere; }
  .wt { height: 8px; background: var(--surface-2); border-radius: 99px; overflow: hidden; }
  .wf { display: block; height: 100%; background: var(--ink); opacity: 0.55; border-radius: 99px; }
  .lbl { font-weight: 600; margin-top: 6px; }
  .stackbar { display: flex; height: 12px; border-radius: 99px; overflow: hidden; margin: 6px 0; background: var(--surface-2); }
  .stackbar .negative { background: var(--neg); }
  .stackbar .neutral { background: var(--neu); }
  .stackbar .positive { background: var(--pos); }
  .legend { display: flex; gap: 12px; flex-wrap: wrap; }
  .legend > span { display: inline-flex; align-items: center; gap: 5px; }
  details { margin-top: 10px; }
  summary { cursor: pointer; font-weight: 500; }
  .examples { padding-left: 18px; display: grid; gap: 6px; margin: 8px 0 0; }
  .warn { margin-top: 10px; border-left: 3px solid var(--neg); padding-left: 10px; }
</style>
