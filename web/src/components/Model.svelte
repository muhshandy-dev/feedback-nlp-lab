<script>
  import Chart from './Chart.svelte';
  import { LABEL_ID, ci, dec, int, pct } from '../lib/format.js';

  let { data, theme } = $props();
  const r = $derived(data.results);
  const L = $derived(r.labels);
  const enc = $derived(r.encoder);
  const hasEnc = $derived(enc.status === 'dijalankan');

  const models = $derived([
    { key: 'majority', name: 'Kelas mayoritas', rep: r.majority.test },
    { key: 'tfidf', name: `TF-IDF (${r.tfidf.selected.features === 'char' ? 'n-gram karakter 2-5' : r.tfidf.selected.features}) + regresi logistik`, rep: r.tfidf.test },
    ...(hasEnc ? [{ key: 'encoder', name: 'IndoBERT base, fine-tuned', rep: enc.test }] : []),
  ]);

  // Skala netral (tinta transparan) supaya tidak tertukar dengan warna kelas Positif.
  function tint(hex, a) {
    const h = hex.replace('#', '');
    const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
    return `rgba(${r}, ${g}, ${b}, ${a.toFixed(3)})`;
  }

  let cm = $state('tfidf');
  const cmRep = $derived(cm === 'encoder' && hasEnc ? enc.test : r.tfidf.test);

  const heatOption = $derived((c) => {
    const m = cmRep.confusion;
    const pts = [];
    m.forEach((row, i) => {
      const n = row.reduce((a, b) => a + b, 0);
      row.forEach((v, j) => pts.push({ value: [j, i, n ? v / n : 0, v], itemStyle: { color: tint(c.ink, 0.06 + 0.32 * (n ? v / n : 0)) } }));
    });
    const names = L.map((l) => LABEL_ID[l]);
    return {
      grid: { left: 78, right: 12, top: 26, bottom: 46 },
      tooltip: { formatter: (p) => `Asli ${names[p.value[1]]}, ditebak ${names[p.value[0]]}: ${p.value[3]} ulasan (${pct(p.value[2])} dari baris)` },
      xAxis: { type: 'category', data: names, name: 'Prediksi', nameLocation: 'middle', nameGap: 30, axisLabel: { color: c.ink }, nameTextStyle: { color: c.muted }, axisTick: { show: false }, axisLine: { show: false } },
      yAxis: { type: 'category', data: names, inverse: true, axisLabel: { color: c.ink }, nameTextStyle: { color: c.muted }, axisTick: { show: false }, axisLine: { show: false } },
      series: [{
        type: 'heatmap',
        data: pts,
        label: { show: true, formatter: (p) => `${p.value[3]}\n${pct(p.value[2], 0)}`, color: c.ink, fontSize: 13, lineHeight: 17 },
        itemStyle: { borderColor: c.surface, borderWidth: 3, borderRadius: 6 },
        emphasis: { disabled: true },
      }],
    };
  });

  const perClassOption = $derived((c) => ({
    grid: { left: 64, right: 16, top: 34, bottom: 28 },
    legend: { top: 0, left: 0, textStyle: { color: c.muted }, itemWidth: 12, itemHeight: 10 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v) => dec(v, 3) },
    xAxis: { type: 'value', min: 0, max: 1, axisLabel: { color: c.muted }, splitLine: { lineStyle: { color: c.grid } } },
    yAxis: { type: 'category', inverse: true, data: L.map((l) => LABEL_ID[l]), axisLabel: { color: c.ink }, axisTick: { show: false }, axisLine: { lineStyle: { color: c.line } } },
    series: models.filter((m) => m.key !== 'majority').map((m, i) => ({
      name: m.key === 'tfidf' ? 'TF-IDF' : 'IndoBERT',
      type: 'bar',
      barGap: '20%',
      barMaxWidth: 16,
      itemStyle: { color: i === 0 ? c.ink : c.positive, borderRadius: [0, 4, 4, 0] },
      data: L.map((l) => m.rep.per_class[l].f1),
    })),
  }));

  const gridOption = $derived((c) => {
    const feats = ['word', 'char', 'word+char'];
    const featName = { word: 'kata 1-2', char: 'karakter 2-5', 'word+char': 'kata + karakter' };
    const colors = [c.neutral, c.ink, c.negative];
    const Cs = [...new Set(r.tfidf.grid.map((g) => g.C))];
    return {
      grid: { left: 48, right: 16, top: 36, bottom: 40 },
      legend: { top: 0, left: 0, textStyle: { color: c.muted }, itemWidth: 14, itemHeight: 8 },
      tooltip: { trigger: 'axis', valueFormatter: (v) => dec(v, 3) },
      xAxis: { type: 'category', name: 'C (kebalikan regularisasi)', nameLocation: 'middle', nameGap: 26, data: Cs.map(String), axisLabel: { color: c.muted }, nameTextStyle: { color: c.muted } },
      yAxis: { type: 'value', min: 0.6, max: 0.85, axisLabel: { color: c.muted }, splitLine: { lineStyle: { color: c.grid } } },
      series: feats.map((f, i) => ({
        name: featName[f],
        type: 'line',
        symbolSize: 6,
        itemStyle: { color: colors[i] },
        data: Cs.map((C) => r.tfidf.grid.find((g) => g.features === f && g.C === C).cv_macro_f1),
      })),
    };
  });
</script>

<section class="stack">
  <h1>Perbandingan model</h1>
  <p class="muted">Semua model dilatih di 500 ulasan latih yang sama dan diuji sekali di 400 ulasan uji resmi. Interval 95% dari 2.000 sampel bootstrap.</p>
</section>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->

<section class="card table-scroll" tabindex="0" aria-label="Tabel, bisa digeser">
  <table>
    <caption>Hasil pada test set (n = {r.tfidf.test.n})</caption>
    <thead><tr><th>Model</th><th class="r">Macro-F1</th><th class="r">95% CI</th><th class="r">Akurasi</th>{#each L as l}<th class="r">F1 {LABEL_ID[l]}</th>{/each}</tr></thead>
    <tbody>
      {#each models as m}
        <tr><td>{m.name}</td><td class="r num strong">{dec(m.rep.macro_f1)}</td><td class="r num">{ci(m.rep.macro_f1_ci95)}</td><td class="r num">{pct(m.rep.accuracy)}</td>{#each L as l}<td class="r num">{dec(m.rep.per_class[l].f1)}</td>{/each}</tr>
      {/each}
      {#if !hasEnc}
        <tr class="pending"><td>IndoBERT base, fine-tuned</td><td colspan={3 + L.length}>Belum dievaluasi. {enc.reason}</td></tr>
      {/if}
    </tbody>
  </table>
</section>

<section class="grid two">
  <article class="card">
    <div class="row">
      <h2 class="h3">Confusion matrix</h2>
      {#if hasEnc}
        <div class="seg" role="group" aria-label="Pilih model">
          <button class="btn xs" aria-pressed={cm === 'tfidf'} onclick={() => (cm = 'tfidf')}>TF-IDF</button>
          <button class="btn xs" aria-pressed={cm === 'encoder'} onclick={() => (cm = 'encoder')}>IndoBERT</button>
        </div>
      {/if}
    </div>
    <p class="muted small">Baris = label asli, kolom = prediksi. Persen dihitung per baris (recall).</p>
    <Chart option={heatOption} {theme} height={300} label="Confusion matrix {cm === 'encoder' ? 'IndoBERT' : 'TF-IDF'}" />
    <table class="sr-only">
      <caption>Confusion matrix {cm === 'encoder' ? 'IndoBERT' : 'TF-IDF'}</caption>
      <thead><tr><th>Asli \ Prediksi</th>{#each L as l}<th>{LABEL_ID[l]}</th>{/each}</tr></thead>
      <tbody>{#each cmRep.confusion as row, i}<tr><th>{LABEL_ID[L[i]]}</th>{#each row as v}<td>{v}</td>{/each}</tr>{/each}</tbody>
    </table>
  </article>
  <article class="card">
    <h2 class="h3">F1 per kelas</h2>
    <p class="muted small">Kelas netral paling sulit: paling sedikit contohnya dan sering bercampur dengan negatif.</p>
    <Chart option={perClassOption} {theme} height={300} label="F1 per kelas untuk setiap model" />
  </article>
</section>

<section class="grid two">
  <article class="card stack">
    <h2 class="h3">Apakah selisihnya nyata?</h2>
    <p class="small">TF-IDF dibanding kelas mayoritas: selisih macro-F1 <strong class="num">{dec(r.tfidf.vs_majority.delta_macro_f1)}</strong> (95% CI {ci(r.tfidf.vs_majority.delta_ci95)}).</p>
    {#if hasEnc}
      {@const v = enc.vs_tfidf}
      <p class="small">IndoBERT dibanding TF-IDF: selisih <strong class="num">{dec(v.delta_macro_f1)}</strong> (95% CI {ci(v.delta_ci95)}). McNemar: {v.mcnemar.only_b_correct} ulasan hanya benar di IndoBERT, {v.mcnemar.only_a_correct} hanya benar di TF-IDF, p = {dec(v.mcnemar.p_value, 4)}.</p>
      <p class="small muted">{v.delta_ci95[0] > 0 ? 'Interval tidak memuat nol: IndoBERT lebih baik secara meyakinkan pada test set ini.' : 'Interval memuat nol: belum ada bukti IndoBERT lebih baik pada test set ini.'}</p>
    {:else}
      <p class="small muted">Uji beda IndoBERT vs TF-IDF (bootstrap berpasangan dan McNemar) sudah disiapkan dan akan terisi otomatis begitu fine-tuning dijalankan.</p>
    {/if}
  </article>
  <article class="card">
    <h2 class="h3">Pemilihan hyperparameter TF-IDF</h2>
    <p class="muted small">21 konfigurasi, dinilai dengan 5-fold CV di data latih saja. Terpilih: {r.tfidf.selected.features}, C = {r.tfidf.selected.C} (CV {dec(r.tfidf.cv_macro_f1)}, validasi {dec(r.tfidf.valid.macro_f1)}).</p>
    <Chart option={gridOption} {theme} height={260} label="Macro-F1 cross-validation untuk tiap jenis fitur dan nilai C" />
  </article>
</section>

{#if hasEnc}
  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <section class="card table-scroll" tabindex="0" aria-label="Tabel, bisa digeser">
    <table>
      <caption>Fine-tuning IndoBERT per seed ({enc.environment.device}{enc.environment.gpu ? `, ${enc.environment.gpu}` : ''}). Seed terpilih berdasarkan validasi: {enc.selected_seed}.</caption>
      <thead><tr><th>Seed</th><th class="r">Epoch terbaik</th><th class="r">Macro-F1 validasi</th><th class="r">Macro-F1 uji</th></tr></thead>
      <tbody>{#each enc.seeds as s}<tr><td>{s.seed}</td><td class="r num">{s.best_epoch}</td><td class="r num">{dec(s.valid_macro_f1)}</td><td class="r num">{dec(s.test_macro_f1)}</td></tr>{/each}</tbody>
    </table>
  </section>
{/if}

<style>
  section + section { margin-top: 18px; }
  .row { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
  .seg { display: flex; gap: 4px; }
  .btn.xs { min-height: 32px; padding: 3px 9px; font-size: 0.8rem; }
  .strong { font-weight: 600; }
  tr.pending td { color: var(--muted); font-style: italic; }
  .table-scroll table { min-width: 640px; }
</style>
