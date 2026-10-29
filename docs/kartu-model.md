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

## 2. IndoBERT base, fine-tuned (belum dijalankan)

- **Model dasar**: `indobenchmark/indobert-base-p1` (MIT), revisi `c2cd0b51ddce6580eb35263b39b0a1e5fb0a39e2`, 124,5 juta parameter, pra-latih Indo4B.
- **Konfigurasi terkunci**: max length 128, batch 16, AdamW lr 2e-5, weight decay 0,01, 8 epoch, warmup linear 10%, gradient clipping 1,0; seed 11, 22, 33; epoch dan seed final dipilih dengan macro-F1 validasi.
- **Status**: kode (`src/feedbacklab/encoder.py`), tes jalur kode dengan BERT mini acak, dan notebook Kaggle sudah ada. **Belum ada hasil** karena bobot model belum bisa diunduh dari lingkungan pembuatan (host CDN Hugging Face diblokir). Tidak ada angka encoder yang diklaim.
- **Penggunaan di website**: bila sudah dijalankan, prediksinya untuk ulasan uji ditampilkan sebagai hasil precomputed berlabel. Tidak dijalankan di browser.

## 3. Topik: NMF

- TF-IDF kata (kata henti Indonesia dibuang, token ≥ 3 huruf, `min_df = 3`, `max_df = 0,5`), NMF inisialisasi acak, dilatih pada 600 ulasan latih + validasi.
- k = 4 (aturan: NPMI held-out tertinggi di antara k dengan stabilitas ≥ 0,5; k = 4 sampai 12 diuji).
- NPMI held-out −0,078 vs topik acak −0,912; stabilitas 1,000; keragaman 93%. Topik 3 (NPMI −0,76) adalah campuran isu publik dan operator seluler, ditandai di website.

## Penggunaan yang tidak disarankan

Keputusan otomatis tentang individu, moderasi konten, atau domain di luar data latih tanpa evaluasi ulang.
