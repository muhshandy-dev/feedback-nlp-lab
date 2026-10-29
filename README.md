# Feedback NLP Lab

Analisis sentimen dan topik ulasan berbahasa Indonesia. Baseline TF-IDF + regresi logistik dilatih sungguhan, berjalan langsung di browser, dan dibandingkan dengan encoder IndoBERT pada test set yang sama. Topik ditemukan dengan NMF dan dinilai konsistensinya.

> **Status: belum selesai.** Pembanding encoder IndoBERT sudah punya kode, tes jalur kode, dan notebook Kaggle, tetapi **belum dijalankan** karena bobot model belum bisa diunduh dari lingkungan pembuatan. Situs tidak menampilkan angka IndoBERT apa pun sampai fine-tuning benar-benar dijalankan. Cara menjalankannya (workflow GitHub Actions **Fine-tune IndoBERT**, notebook Kaggle, atau lokal) ada di [`docs/SERAH_TERIMA.md`](docs/SERAH_TERIMA.md).

## Hasil saat ini (test set resmi, 400 ulasan)

| Model | Macro-F1 | 95% CI (bootstrap 2.000) | Akurasi |
|---|---|---|---|
| Kelas mayoritas (selalu "negatif") | 0,184 | 0,167 sampai 0,200 | 38,3% |
| TF-IDF n-gram karakter 2-5 + regresi logistik (C = 5) | **0,772** | 0,729 sampai 0,813 | 78,0% |
| IndoBERT base, fine-tuned | belum dijalankan | | |

F1 per kelas TF-IDF: negatif 0,747, netral 0,711, positif 0,859. Kesalahan terbanyak: negatif ditebak netral (25) dan netral ditebak negatif (21).

Topik (NMF, k = 4 dipilih dengan aturan yang dikunci): NPMI held-out −0,078 (topik acak −0,912), stabilitas antar 5 seed 1,000, keragaman kata 93%. Satu dari empat topik (NPMI −0,76) ditandai sebagai campuran di situs.

Angka lengkap: [`reports/results.json`](reports/results.json). Laporan: [`docs/laporan-evaluasi.md`](docs/laporan-evaluasi.md).

## Data

NusaX-Senti subset bahasa Indonesia (Winata dkk., EACL 2023), 500 latih / 100 validasi / 400 uji, label negatif, netral, positif. Lisensi **CC BY-SA 4.0**. Diunduh dari `IndoNLP/nusax` pada commit terkunci `75b0be5d98` dan dicocokkan dengan SHA-256 di [`data/nusax_manifest.json`](data/nusax_manifest.json). Data card: [`docs/kartu-data.md`](docs/kartu-data.md).

Setiap teks melewati penghapus data pribadi (URL, email, akun @, nomor HP Indonesia, deretan 10 digit atau lebih) sebelum dipakai. Pada NusaX tidak ditemukan pola tersebut; penghapus diuji dengan unit test.

## Protokol

1. Hyperparameter TF-IDF (jenis fitur × C, 21 konfigurasi) dipilih dengan 5-fold stratified CV di data latih saja. Validasi resmi (100 ulasan) dilaporkan, tidak dipakai memilih.
2. Encoder: `indobenchmark/indobert-base-p1` (MIT) revisi `c2cd0b51dd`, hanya bobot pra-latih, fine-tune 3 seed, epoch dipilih dengan macro-F1 validasi. Model yang sudah dilatih pada SmSA sengaja tidak dipakai karena teks NusaX berasal dari SmSA.
3. Test hanya dipakai sekali. Macro-F1 + CI bootstrap, confusion matrix, F1 per kelas, uji beda berpasangan (bootstrap selisih macro-F1 dan McNemar eksak).
4. Topik: NMF di atas TF-IDF kata (kata henti dibuang), dilatih pada latih + validasi. Koherensi NPMI kata top-10 dihitung pada ulasan uji (held-out), stabilitas = Jaccard topik yang dipasangkan (Hungaria) antar 5 seed, dibandingkan dengan topik acak. k dipilih: NPMI held-out tertinggi di antara k dengan stabilitas ≥ 0,5.
5. Kata kunci per sentimen: weighted log-odds dengan prior Dirichlet (Monroe dkk., 2008), deskriptif.

## Reproduksi

```bash
pip install -e ".[dev]"
feedbacklab data fetch   # unduh + verifikasi checksum
feedbacklab run          # latih, evaluasi, tulis reports/ dan web/public/data/
pytest                   # termasuk tes: hasil ulang sama persis dengan reports/results.json
python tools/verify_published.py   # hitung ulang angka website dari CSV asli

# Encoder (GPU disarankan; atau notebooks/kaggle_encoder.ipynb di Kaggle)
pip install -e ".[encoder]"
feedbacklab encoder      # menulis reports/encoder_run.json
feedbacklab run          # evaluasi encoder + uji beda ikut terisi
```

Website (Svelte 5 + Vite + ECharts):

```bash
cd web && npm ci
npm test          # paritas probabilitas browser vs scikit-learn untuk 400 ulasan uji
npm run build     # hasil statis di web/dist
npm run e2e       # Playwright: 4 lebar layar, terang/gelap, CSP, axe, interaksi
```

## Deploy (Cloudflare Pages)

Root directory `web`, build command `npm ci && npm run build`, output `dist`, `NODE_VERSION=22`. Langkah lengkap: [`docs/DEPLOY_CLOUDFLARE.md`](docs/DEPLOY_CLOUDFLARE.md). Situs sepenuhnya statis, tidak tidur saat idle. Header keamanan dan cache di [`web/public/_headers`](web/public/_headers).

## Batas klaim

- Korpus kecil (1.000 ulasan) dan campuran domain (restoran, wisata, operator seluler, bank, isu publik). Angka tidak berlaku untuk ulasan e-commerce tanpa diuji ulang. PRDECT-ID (5.400 ulasan Tokopedia) direncanakan tetapi belum bisa diunduh dari lingkungan pembuatan.
- Hasil Kaggle tidak diklaim sebelum notebook benar-benar dijalankan.
- Model card: [`docs/kartu-model.md`](docs/kartu-model.md).

## Lisensi

Kode MIT ([LICENSE](LICENSE)). Teks ulasan dan berkas turunan yang memuat teks (`reports/test_predictions.json`, `web/public/data/*.json`) mengikuti lisensi NusaX, CC BY-SA 4.0.
