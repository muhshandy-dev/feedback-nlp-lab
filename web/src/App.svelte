<script>
  import { onMount } from 'svelte';
  import { prepare } from './lib/tfidf.js';
  import Ringkasan from './components/Ringkasan.svelte';
  import Uji from './components/Uji.svelte';
  import Topik from './components/Topik.svelte';
  import Model from './components/Model.svelte';
  import Jelajah from './components/Jelajah.svelte';
  import Metode from './components/Metode.svelte';

  const TABS = [
    { id: 'ringkasan', name: 'Ringkasan' },
    { id: 'uji', name: 'Uji ulasan' },
    { id: 'topik', name: 'Topik' },
    { id: 'model', name: 'Model' },
    { id: 'jelajah', name: 'Jelajah ulasan' },
    { id: 'metode', name: 'Metode' },
  ];

  let tab = $state('ringkasan');
  let data = $state(null);
  let error = $state('');
  let theme = $state('auto');

  function fromHash() {
    const h = location.hash.replace('#', '');
    tab = TABS.some((t) => t.id === h) ? h : 'ringkasan';
  }

  function go(id) {
    if (location.hash !== `#${id}`) history.pushState(null, '', `#${id}`);
    tab = id;
    document.getElementById('konten')?.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }

  function onTabKey(e, i) {
    const k = e.key;
    if (k !== 'ArrowRight' && k !== 'ArrowLeft') return;
    e.preventDefault();
    const next = TABS[(i + (k === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length];
    go(next.id);
    document.getElementById(`tab-${next.id}`)?.focus();
  }

  function setTheme(t) {
    theme = t;
    if (t === 'auto') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('tema', t); } catch { /* penyimpanan bisa diblokir */ }
  }

  onMount(async () => {
    try { setTheme(localStorage.getItem('tema') || 'auto'); } catch { setTheme('auto'); }
    fromHash();
    addEventListener('popstate', fromHash);
    addEventListener('hashchange', fromHash);
    try {
      const get = (f) => fetch(`data/${f}?v=1`).then((r) => {
        if (!r.ok) throw new Error(`${f}: ${r.status}`);
        return r.json();
      });
      const [results, predictions, model] = await Promise.all([
        get('results.json'), get('test_predictions.json'), get('model.json'),
      ]);
      data = { results, predictions, model: prepare(model) };
    } catch (e) {
      error = `Data gagal dimuat (${e.message}). Muat ulang halaman.`;
    }
  });
</script>

<a class="skip" href="#konten">Lewati ke konten</a>
<header class="top">
  <div class="wrap bar">
    <div class="brand">
      <svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true"><rect width="32" height="32" rx="7" class="mark-bg"/><rect x="7" y="9" width="12" height="4" rx="2" class="m-neg"/><rect x="7" y="15" width="18" height="4" rx="2" class="m-pos"/><rect x="7" y="21" width="8" height="4" rx="2" class="m-neu"/></svg>
      <div>
        <p class="name">Feedback NLP Lab</p>
        <p class="tag muted small">Sentimen dan topik ulasan berbahasa Indonesia</p>
      </div>
    </div>
    <div class="theme" role="group" aria-label="Tema tampilan">
      {#each [['auto', 'Otomatis'], ['light', 'Terang'], ['dark', 'Gelap']] as [t, n]}
        <button class="btn sm" aria-pressed={theme === t} onclick={() => setTheme(t)}>{n}</button>
      {/each}
    </div>
  </div>
  <nav class="wrap" aria-label="Bagian">
    <div class="tabs" role="tablist">
      {#each TABS as t, i}
        <button
          id="tab-{t.id}"
          role="tab"
          aria-selected={tab === t.id}
          aria-controls="konten"
          tabindex={tab === t.id ? 0 : -1}
          onclick={() => go(t.id)}
          onkeydown={(e) => onTabKey(e, i)}>{t.name}</button>
      {/each}
    </div>
  </nav>
</header>

<main id="konten" class="wrap" tabindex="-1">
<div role="tabpanel" aria-labelledby="tab-{tab}">
  {#if error}
    <p class="card" role="alert">{error}</p>
  {:else if !data}
    <p class="muted loading" aria-live="polite">Memuat hasil evaluasi…</p>
  {:else if tab === 'ringkasan'}
    <Ringkasan {data} {theme} {go} />
  {:else if tab === 'uji'}
    <Uji {data} />
  {:else if tab === 'topik'}
    <Topik {data} {theme} />
  {:else if tab === 'model'}
    <Model {data} {theme} />
  {:else if tab === 'jelajah'}
    <Jelajah {data} />
  {:else}
    <Metode {data} />
  {/if}
</div>
</main>

<footer class="wrap foot muted small">
  <p>Data: NusaX-Senti bahasa Indonesia (Winata dkk., EACL 2023), lisensi CC BY-SA 4.0. Kode MIT. Semua angka dihitung dari test set resmi 400 ulasan.</p>
  <p><a href="https://github.com/muhshandy-dev/feedback-nlp-lab">Kode sumber di GitHub</a></p>
</footer>

<style>
  .skip { position: absolute; left: -999px; top: 8px; background: var(--ink); color: var(--bg); padding: 8px 12px; border-radius: 6px; z-index: 10; }
  .skip:focus { left: 8px; }
  .top { position: sticky; top: 0; z-index: 5; background: var(--bg); border-bottom: 1px solid var(--line); }
  .bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-top: 12px; padding-bottom: 8px; flex-wrap: wrap; }
  .brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
  .name { font-family: var(--display); font-weight: 600; font-size: 1.1rem; line-height: 1.2; }
  .tag { line-height: 1.3; }
  .mark-bg { fill: var(--ink); }
  .m-neg { fill: var(--neg); }
  .m-pos { fill: var(--pos); }
  .m-neu { fill: var(--neu); }
  .theme { display: flex; gap: 4px; }
  .btn.sm { min-height: 32px; padding: 4px 10px; font-size: 0.82rem; }
  .tabs { display: flex; gap: 2px; overflow-x: auto; scrollbar-width: none; margin: 0 -4px; }
  .tabs::-webkit-scrollbar { display: none; }
  .tabs button {
    font: inherit; font-size: 0.93rem; font-weight: 500; color: var(--muted);
    background: none; border: 0; border-bottom: 2px solid transparent;
    padding: 10px 10px 9px; cursor: pointer; white-space: nowrap; min-height: 44px;
  }
  .tabs button:hover { color: var(--ink); }
  .tabs button[aria-selected='true'] { color: var(--ink); border-bottom-color: var(--ink); }
  main { padding-top: 24px; padding-bottom: 40px; outline: none; }
  .loading { padding: 40px 0; }
  .foot { border-top: 1px solid var(--line); padding-top: 16px; padding-bottom: 28px; display: grid; gap: 4px; }
</style>
