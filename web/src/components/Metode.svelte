<script>
  import { LABEL_ID, dec, int } from '../lib/format.js';

  let { data } = $props();
  const r = $derived(data.results);
  const d = $derived(r.dataset);
  const enc = $derived(r.encoder);
  const piiTotal = $derived(Object.values(d.pii_removed).reduce((s, x) => s + x.documents_with_pii, 0));
</script>

<section class="stack">
  <h1>Metode dan batas klaim</h1>
  <p class="muted">Apa yang sebenarnya dilakukan, dari mana datanya, dan apa yang belum bisa diklaim.</p>
</section>

<div class="grid two cols">
  <section class="card stack">
    <h2 class="h3">Data</h2>
    <p class="small">{d.dataset}, {d.citation}. Lisensi {d.license}. Diambil dari <code>{d.repo}</code> pada commit <code>{d.commit.slice(0, 12)}</code> dan dicocokkan dengan checksum SHA-256.</p>
    <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
    <div class="table-scroll" tabindex="0" role="region" aria-label="Tabel data, bisa digeser">
      <table class="small">
        <thead><tr><th>Split</th><th class="r">Ulasan</th>{#each r.labels as l}<th class="r">{LABEL_ID[l]}</th>{/each}</tr></thead>
        <tbody>{#each Object.keys(d.sizes) as s}<tr><td>{s}</td><td class="r num">{d.sizes[s]}</td>{#each r.labels as l}<td class="r num">{d.label_counts[s][l]}</td>{/each}</tr>{/each}</tbody>
      </table>
    </div>
    <p class="small">Split resmi dari penyusun dataset dipakai apa adanya. Program memeriksa bahwa tidak ada teks yang sama di dua split.</p>
    <p class="small">Data pribadi: setiap teks melewati penghapus URL, email, akun @, nomor telepon Indonesia, dan deretan angka 10 digit atau lebih (NIK, rekening) sebelum dipakai. Pada NusaX ditemukan {int(piiTotal)} ulasan berisi pola tersebut, karena penyusunnya sudah membersihkan data. Penghapus tetap diuji dengan unit test.</p>
  </section>

  <section class="card stack">
    <h2 class="h3">Protokol evaluasi</h2>
    <ol class="small steps">
      <li>Baseline paling sederhana: selalu menebak kelas mayoritas data latih.</li>
      <li>TF-IDF (n-gram kata 1-2, n-gram karakter 2-5, atau gabungan) + regresi logistik berbobot kelas. 21 konfigurasi dipilih dengan 5-fold CV di 500 ulasan latih saja.</li>
      <li>Encoder <code>indobenchmark/indobert-base-p1</code> (MIT), hanya bobot pra-latih, di-fine-tune pada data latih yang sama; epoch dipilih dengan macro-F1 validasi; 3 seed. Model yang sudah dilatih pada SmSA sengaja tidak dipakai karena teks NusaX berasal dari SmSA (bocor).</li>
      <li>Test set 400 ulasan hanya dipakai sekali di akhir. Metrik utama macro-F1 dengan 95% CI bootstrap (2.000 sampel), ditambah confusion matrix dan F1 per kelas.</li>
      <li>Beda antar model diuji berpasangan: bootstrap selisih macro-F1 dan uji McNemar eksak.</li>
      <li>Topik: NMF pada TF-IDF kata, k = 4 sampai 12. Konsistensi = NPMI kata top-10 pada ulasan uji (held-out), stabilitas Jaccard antar 5 seed, dan keragaman kata; dibandingkan dengan topik acak.</li>
    </ol>
  </section>

  <section class="card stack">
    <h2 class="h3">Yang berjalan di browser</h2>
    <p class="small">Model TF-IDF diekspor lengkap (kosakata, idf, koefisien) dan dihitung ulang dengan JavaScript. Tes otomatis memastikan probabilitas browser sama dengan scikit-learn untuk seluruh 400 ulasan uji (selisih di bawah 0,00001).</p>
    <p class="small">IndoBERT tidak dijalankan di browser. {enc.status === 'dijalankan' ? 'Prediksinya untuk ulasan uji ditampilkan sebagai hasil precomputed.' : 'Hasilnya belum ada, sehingga situs tidak menampilkan angka IndoBERT apa pun.'}</p>
  </section>

  <section class="card stack">
    <h2 class="h3">Batas klaim</h2>
    <ul class="small steps">
      <li>Korpus kecil (1.000 ulasan) dan campuran domain: restoran, wisata, operator seluler, bank, isu publik. Angka tidak berlaku untuk ulasan produk e-commerce tanpa diuji ulang.</li>
      <li>Hanya bahasa Indonesia; NusaX juga berisi bahasa daerah yang tidak dipakai di sini.</li>
      <li>Kata kunci per sentimen bersifat deskriptif (log-odds dengan prior Dirichlet di seluruh korpus), bukan bukti sebab.</li>
      <li>Topik dengan NPMI rendah ditandai sebagai campuran.</li>
      {#if enc.status === 'dijalankan'}
        <li>IndoBERT di-fine-tune satu kali (3 seed) di runner CPU GitHub Actions, bukan di Kaggle. Skor uji antar seed {enc.seeds.map((s) => dec(s.test_macro_f1)).join(', ')}; {enc.seeds.every((s) => s.test_macro_f1 > r.tfidf.test.macro_f1) ? 'semuanya di atas TF-IDF' : 'tidak semuanya di atas TF-IDF'}, tetapi angka utama adalah satu seed yang dipilih dengan validasi.</li>
        <li>Bobot pra-latih IndoBERT dilatih pada korpus web Indonesia yang besar. Kemungkinan sebagian teks ulasan pernah muncul di korpus itu (tanpa label) tidak bisa disingkirkan sepenuhnya.</li>
        <li>Tab Uji kalimat hanya menjalankan TF-IDF secara langsung. Prediksi IndoBERT tersedia untuk 400 ulasan uji sebagai hasil precomputed.</li>
      {:else}
        <li><strong>Pembanding encoder belum dijalankan.</strong> Kode dan notebook Kaggle sudah ada, tetapi bobot IndoBERT belum bisa diunduh dari lingkungan pembuatan. Proyek belum memenuhi kriteria "TF-IDF vs encoder" sampai bagian ini selesai.</li>
      {/if}
    </ul>
  </section>
</div>

<section class="card stack repro">
  <h2 class="h3">Reproduksi</h2>
  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <pre tabindex="0" aria-label="Perintah reproduksi"><code>pip install -e ".[dev]"
feedbacklab data fetch      # unduh NusaX pada commit terkunci + cek checksum
feedbacklab run             # baseline, topik, evaluasi, ekspor ke web/public/data
pip install -e ".[encoder]"
feedbacklab encoder         # fine-tune IndoBERT (GPU disarankan), lalu jalankan `run` lagi</code></pre>
  <p class="small muted">CI menjalankan ulang pipeline dan memastikan <code>results.json</code> sama persis dengan yang dipublikasikan.</p>
</section>

<style>
  .cols { margin-top: 18px; }
  .repro { margin-top: 16px; }
  .steps { padding-left: 20px; margin: 0; display: grid; gap: 6px; }
  pre { background: var(--surface-2); border-radius: 8px; padding: 12px; overflow-x: auto; font-size: 0.85rem; margin: 0; }
  pre code { background: none; padding: 0; }
</style>
