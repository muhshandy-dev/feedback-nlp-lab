<script>
  import { explain, predict } from '../lib/tfidf.js';
  import { LABEL_ID, dec, pct } from '../lib/format.js';

  let { data } = $props();
  const pm = $derived(data.model);
  const L = $derived(pm.labels);
  const rows = $derived(data.predictions.rows);

  // Contoh tetap dari test set: satu benar per kelas, lalu dua kesalahan.
  const examples = $derived.by(() => {
    const out = [];
    for (const lab of L) {
      const r = rows.find((x) => x.label === lab && x.tfidf === lab && x.text.length < 160);
      if (r) out.push({ ...r, why: `${LABEL_ID[lab]}, ditebak benar` });
    }
    rows.filter((x) => x.label !== x.tfidf && x.text.length < 170).slice(0, 2)
      .forEach((r) => out.push({ ...r, why: `Kesalahan: ${LABEL_ID[r.label]} ditebak ${LABEL_ID[r.tfidf]}` }));
    return out;
  });

  let text = $state('Makanannya enak dan harganya terjangkau, tapi pelayanannya lambat sekali.');
  let focusClass = $state(null);

  const result = $derived(predict(pm, text));
  const shown = $derived(focusClass || result.label);
  const expl = $derived(explain(pm, result, shown));
  const maxAbs = $derived(Math.max(1e-9, ...expl.contributions.map((c) => Math.abs(c.value))));
  const byIndex = $derived(new Map(expl.contributions.map((c) => [c.index, c.value])));
  const known = $derived(rows.find((r) => r.text.trim() === text.trim()));
  const top = $derived(
    [...expl.contributions].sort((a, b) => b.value - a.value).filter((c) => c.value > 0).slice(0, 5),
  );
  const against = $derived(
    [...expl.contributions].sort((a, b) => a.value - b.value).filter((c) => c.value < 0).slice(0, 3),
  );

  // Kekuatan sorotan 0..1; warna dan batas kontras diatur CSS per tema.
  const strength = (v) => (v > 0 ? 0.12 + 0.88 * (v / maxAbs) : 0);
</script>

<section class="stack">
  <h1>Uji ulasan Anda sendiri</h1>
  <p class="muted">Model TF-IDF + regresi logistik dihitung langsung di perangkat Anda. Tidak ada teks yang dikirim ke server.</p>
</section>

<div class="layout">
  <section class="card stack" aria-label="Masukan">
    <label for="ulasan" class="lbl">Tulis atau tempel ulasan</label>
    <textarea id="ulasan" rows="6" bind:value={text} maxlength="2000" spellcheck="false"></textarea>
    <p class="muted small num">{text.length} karakter · {result.matched} fitur n-gram dikenali model</p>
    <div>
      <p class="small lbl">Contoh dari test set</p>
      <ul class="ex">
        {#each examples as e}
          <li>
            <button class="btn ex-btn" onclick={() => { text = e.text; focusClass = null; }}>
              <span class="small muted">{e.why}</span>
              <span class="ex-text">{e.text}</span>
            </button>
          </li>
        {/each}
      </ul>
    </div>
  </section>

  <section class="card stack" aria-label="Hasil" aria-live="polite">
    {#if !text.trim()}
      <p class="muted">Tulis ulasan untuk melihat prediksi.</p>
    {:else}
      <div class="verdict">
        <p class="muted small">Prediksi TF-IDF</p>
        <p class="big"><span class="dot {result.label}"></span> {LABEL_ID[result.label]}</p>
      </div>
      <ul class="probs" aria-label="Probabilitas per kelas">
        {#each L as lab, i}
          <li>
            <span class="pl">{LABEL_ID[lab]}</span>
            <span class="track"><span class="fill {lab}" style:width="{result.probs[i] * 100}%"></span></span>
            <span class="num pv">{pct(result.probs[i])}</span>
          </li>
        {/each}
      </ul>
      {#if result.matched === 0}
        <p class="small note">Tidak ada n-gram yang dikenali, jadi prediksi hanya mengikuti bias model. Jangan percayai hasil ini.</p>
      {/if}

      <div>
        <div class="row">
          <p class="small lbl">Kata yang mendorong ke kelas</p>
          <div class="seg" role="group" aria-label="Pilih kelas yang dijelaskan">
            {#each L as lab}
              <button class="btn xs" aria-pressed={shown === lab} onclick={() => (focusClass = lab)}>{LABEL_ID[lab]}</button>
            {/each}
          </div>
        </div>
        <p class="hl {shown}" aria-label="Teks dengan sorotan kontribusi kata">
          {#each expl.words as w, i}<mark style:--a={strength(byIndex.get(i) || 0)} title={byIndex.has(i) ? `kontribusi ${dec(byIndex.get(i), 3)}` : 'tidak dikenali'}>{w}</mark>{' '}{/each}
        </p>
        <div class="grid two why">
          <div>
            <p class="small lbl">Paling mendukung {LABEL_ID[shown]}</p>
            <ol class="small">{#each top as c}<li>{c.word} <span class="muted num">+{dec(c.value, 3)}</span></li>{:else}<li class="muted">tidak ada</li>{/each}</ol>
          </div>
          <div>
            <p class="small lbl">Paling menentang</p>
            <ol class="small">{#each against as c}<li>{c.word} <span class="muted num">{dec(c.value, 3)}</span></li>{:else}<li class="muted">tidak ada</li>{/each}</ol>
          </div>
        </div>
        <p class="muted small">Kontribusi = bobot n-gram karakter untuk kelas ini dikurangi rata-rata kelas lain, dikali nilai TF-IDF-nya, lalu dijumlahkan per kata.</p>
      </div>

      {#if known}
        <div class="known small">
          <p><strong>Ulasan ini ada di test set.</strong> Label asli: {LABEL_ID[known.label]}.</p>
          {#if known.encoder}
            <p>IndoBERT (precomputed): {LABEL_ID[known.encoder]}, {pct(Math.max(...known.encoder_probs))}.</p>
          {:else}
            <p class="muted">Prediksi IndoBERT belum tersedia.</p>
          {/if}
        </div>
      {/if}
    {/if}
  </section>
</div>

<p class="muted small limit">Batas: model dilatih pada 500 ulasan (restoran, tempat wisata, operator seluler, layanan bank, isu publik). Ulasan di luar domain itu, bahasa daerah, sarkasme, dan teks sangat pendek sering salah ditebak.</p>

<style>
  .layout { display: grid; gap: 16px; margin-top: 18px; }
  @media (min-width: 900px) { .layout { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); align-items: start; } }
  .lbl { font-weight: 600; }
  textarea {
    width: 100%; font: inherit; color: var(--ink); background: var(--bg);
    border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; resize: vertical;
  }
  .ex { list-style: none; padding: 0; margin: 6px 0 0; display: grid; gap: 6px; }
  .ex-btn { width: 100%; text-align: left; display: grid; gap: 2px; font-weight: 400; }
  .ex-text { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .big { font-family: var(--display); font-size: 2rem; font-weight: 600; display: flex; align-items: center; gap: 10px; }
  .big .dot { width: 14px; height: 14px; }
  .probs { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
  .probs li { display: grid; grid-template-columns: 70px 1fr 56px; align-items: center; gap: 10px; }
  .track { height: 10px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }
  .fill { display: block; height: 100%; border-radius: 99px; }
  .fill.negative { background: var(--neg); }
  .fill.neutral { background: var(--neu); }
  .fill.positive { background: var(--pos); }
  .pv { text-align: right; }
  .note { border-left: 3px solid var(--neg); padding-left: 10px; }
  .row { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
  .seg { display: flex; gap: 4px; }
  .btn.xs { min-height: 32px; padding: 3px 9px; font-size: 0.8rem; }
  .hl { line-height: 2; margin-top: 8px; overflow-wrap: anywhere; }
  mark {
    color: inherit; border-radius: 4px; padding: 1px 2px;
    background: color-mix(in srgb, var(--c) calc(var(--a, 0) * var(--hl-max) * 1%), transparent);
  }
  .hl { --hl-max: 62; }
  :global(:root[data-theme='dark']) .hl { --hl-max: 40; }
  @media (prefers-color-scheme: dark) { :global(:root:not([data-theme='light'])) .hl { --hl-max: 40; } }
  .hl.negative { --c: var(--neg); }
  .hl.neutral { --c: var(--neu); }
  .hl.positive { --c: var(--pos); }
  .why ol { margin: 4px 0 0; padding-left: 20px; }
  .why { gap: 10px; margin-top: 8px; }
  .known { background: var(--surface-2); border-radius: 8px; padding: 10px 12px; display: grid; gap: 4px; }
  .limit { margin-top: 16px; }
</style>
