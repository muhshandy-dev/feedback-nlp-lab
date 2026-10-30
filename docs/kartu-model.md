# Kartu model

## 1. TF-IDF + regresi logistik (dipakai di website)

- **Tugas**: klasifikasi sentimen 3 kelas (negatif, netral, positif) untuk ulasan berbahasa Indonesia.
- **Fitur**: TF-IDF n-gram karakter 2-5 dalam batas kata (`char_wb`), `min_df = 2`, sublinear TF, normalisasi L2. Teks dinormalisasi: huruf kecil, selain a-z dan 0-9 menjadi spasi.
- **Klasifier**: regresi logistik multinomial, `C = 5`, bobot kelas seimbang.
- **Pemilihan**: 21 konfigurasi (kata 1-2 / karakter 2-5 / gabungan × 7 nilai C), 5-fold stratified CV di 500 ulasan latih. CV macro-F1 terpilih 0,782; validasi 0,784.
- **Hasil uji (400)**: macro-F1 0,772 (95% CI 0,729 sampai 0,813), akurasi 78,0%. F1 negatif 0,747, netral 0,711, positif 0,859.
- **Di browser**: kosakata, idf, dan koefisien diekspor ke `model.json` (sekitar 520 KB). Probabilitas JavaScript sama dengan scikit-learn untuk 400 ulasan uji (selisih < 1e-5, diuji di CI).
- **Penjelasan**: kontribusi per kata = (bobot kelas − rata-rata bobot kelas lain) × nilai TF-IDF, dijumlahkan dari n-gram yang berasal dari kata itu. Jumlah kontribusi sama dengan selisih skor (diuji).
- **Kegagalan yang diketahui**: negasi ("tidak kecewa" ditebak negatif), keluhan bernada faktual ditebak netral, ulasan campuran yang didominasi kosakata positif. Lihat `docs/laporan-evaluasi.md`.

## 2. IndoBERT base, fine-tuned

- **Model dasar**: `indobenchmark/indobert-base-p1` (MIT), revisi `c2cd0b51ddce6580eb35263b39b0a1e5fb0a39e2`, 124,5 juta parameter, pra-latih Indo4B.
- **Konfigurasi terkunci**: max length 128, batch 16, AdamW lr 2e-5, weight decay 0,01, 8 epoch, warmup linear 10%, gradient clipping 1,0; seed 11, 22, 33; epoch dan seed final dipilih dengan macro-F1 validasi.
- **Dijalankan di**: GitHub Actions run 41083480509 (CPU, torch 2.15.0, transformers 5.22.1, Python 3.12), 30 Oktober 2026, 38 menit untuk 3 seed. Bukan Kaggle. Hasil mentah: `reports/encoder_run.json` (kurva per epoch, probabilitas validasi dan uji tiap seed).
- **Seed**: 11 (epoch terbaik 5, validasi 0,908, uji 0,888), 22 (epoch 2, validasi 0,926, uji 0,879), 33 (epoch 4, validasi 0,926, uji 0,900). Seed 33 terpilih karena validasinya tertinggi (0,92632 vs 0,92584).
- **Hasil uji (400)**: macro-F1 0,900 (95% CI 0,868 sampai 0,929), akurasi 90,8%. F1 negatif 0,919, netral 0,845, positif 0,935. Dibanding TF-IDF: +0,127 (95% CI 0,086 sampai 0,168), McNemar 60 vs 9, p < 0,001.
- **Kegagalan yang diketahui**: berita atau cerita faktual tentang kejadian buruk berlabel netral ditebak negatif (12 dari 37 kesalahan), ulasan restoran panjang yang campuran ditebak negatif, keluhan faktual pendek ("Saya kapok menggunakan jasa lion air") tetap ditebak netral. Negasi sederhana ("tidak kecewa") sudah benar.
- **Penggunaan di website**: prediksi untuk 400 ulasan uji ditampilkan sebagai hasil precomputed berlabel. Tidak dijalankan di browser (bobot sekitar 500 MB).

## 3. Topik: NMF

- TF-IDF kata (kata henti Indonesia dibuang, token ≥ 3 huruf, `min_df = 3`, `max_df = 0,5`), NMF inisialisasi acak, dilatih pada 600 ulasan latih + validasi.
- k = 4 (aturan: NPMI held-out tertinggi di antara k dengan stabilitas ≥ 0,5; k = 4 sampai 12 diuji).
- NPMI held-out −0,078 vs topik acak −0,912; stabilitas 1,000; keragaman 93%. Topik 3 (NPMI −0,76) adalah campuran isu publik dan operator seluler, ditandai di website.

## Penggunaan yang tidak disarankan

Keputusan otomatis tentang individu, moderasi konten, atau domain di luar data latih tanpa evaluasi ulang.
