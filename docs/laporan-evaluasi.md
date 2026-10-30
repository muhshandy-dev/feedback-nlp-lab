# Laporan evaluasi Feedback NLP Lab

Tanggal: 29 Oktober 2026, diperbarui 30 Oktober 2026 dengan hasil IndoBERT. Semua angka dari `reports/results.json`, dihasilkan oleh `feedbacklab run` dan diperiksa ulang secara independen oleh `tools/verify_published.py`.

## 1. Klasifikasi sentimen (test resmi, 400 ulasan)

| Model | Macro-F1 | 95% CI | Akurasi | F1 neg | F1 net | F1 pos |
|---|---|---|---|---|---|---|
| Kelas mayoritas | 0,184 | 0,167 sampai 0,200 | 38,3% | 0,553 | 0,000 | 0,000 |
| TF-IDF karakter 2-5 + LR (C = 5) | 0,772 | 0,729 sampai 0,813 | 78,0% | 0,747 | 0,711 | 0,859 |
| IndoBERT base fine-tuned (seed 33) | **0,900** | 0,868 sampai 0,929 | 90,8% | 0,919 | 0,845 | 0,935 |

TF-IDF dibanding kelas mayoritas: selisih macro-F1 +0,588 (95% CI bootstrap berpasangan 0,541 sampai 0,634); McNemar 197 ulasan hanya benar di TF-IDF vs 38 hanya benar di mayoritas, p < 0,001.

IndoBERT dibanding TF-IDF: selisih macro-F1 **+0,127** (95% CI bootstrap berpasangan 0,086 sampai 0,168, tidak memuat nol); McNemar 60 ulasan hanya benar di IndoBERT vs 9 hanya benar di TF-IDF, p < 0,001. IndoBERT lebih baik secara meyakinkan pada test set ini.

Confusion matrix (baris = asli, kolom = prediksi; negatif, netral, positif):

```
             TF-IDF            IndoBERT
negatif  115  25  13       147   6   0
netral    21  69   6        12  79   5
positif   19   4 128         8   6 137
```

### Fine-tuning IndoBERT

Dijalankan di GitHub Actions run [41083480509](https://github.com/muhshandy-dev/feedback-nlp-lab/actions/runs/41083480509), runner CPU, 38 menit untuk 3 seed (torch 2.15.0, transformers 5.22.1). Bukan di Kaggle: Kaggle dan CDN bobot Hugging Face tidak bisa dijangkau dari lingkungan pembuatan, sedangkan runner GitHub bisa. Model, revisi, data, konfigurasi, dan aturan pemilihan sama persis dengan protokol yang dikunci sebelumnya; hanya tempat menjalankannya yang berbeda.

| Seed | Epoch terbaik | Macro-F1 validasi | Macro-F1 uji |
|---|---|---|---|
| 11 | 5 | 0,908 | 0,888 |
| 22 | 2 | 0,926 | 0,879 |
| **33 (terpilih)** | 4 | 0,926 | 0,900 |

Seed 33 dipilih karena validasinya tertinggi (0,92632 vs 0,92584 untuk seed 22, selisih yang praktis sama). Skor uji seed lain 0,879 sampai 0,888, jadi angka 0,900 sedikit beruntung, tetapi ketiga seed tetap jauh di atas TF-IDF (0,772).

### Pemilihan hyperparameter

Tiga jenis fitur hampir setara di CV (kata 1-2 C = 0,5: 0,782; karakter 2-5 C = 5: 0,782; gabungan C = 0,5: 0,781). Perbedaannya jauh di bawah ketidakpastian, jadi pilihan fitur tidak boleh dibaca sebagai temuan. Skor validasi resmi (100 ulasan) bergerak 0,77 sampai 0,80 untuk konfigurasi yang sama baiknya di CV, yang menunjukkan validasi terlalu kecil untuk memilih model.

### Analisis kesalahan (88 dari 400 salah)

| Pola | Contoh (dipotong) | Asli → prediksi |
|---|---|---|
| Negasi tidak terbaca | "Saya tidak kecewa dengan produk apple" | positif → negatif |
| Negasi tidak terbaca | "Untuk daerah banda aceh dan sekitarnya masih lancar, tidak ada gangguan sama sekali." | netral → negatif |
| Keluhan bernada faktual | "Saya kapok menggunakan jasa lion air" | negatif → netral |
| Keluhan bernada faktual | "Saya melakukan 5 transaksi … smuanya decline nyatanya terdebit …" | negatif → netral |
| Ulasan campuran | "The peak … lokasi yang sangat baik namun jalan untuk mencapai tempat ini sangat berkelok …" | negatif → positif |
| Pujian singkat / slang | "Anw indomie pertama di 2018 ku semalam ternyata nikmat" | positif → netral |

Kelas netral paling sulit (F1 0,711): paling sedikit contohnya dan sering berisi kata keluhan tanpa sentimen ("sinyal", "kartu").

IndoBERT memperbaiki kedua contoh negasi di atas serta contoh ulasan campuran dan slang. Kesalahannya (37 dari 400) punya pola lain:

| Pola IndoBERT | Contoh (dipotong) | Asli → prediksi |
|---|---|---|
| Cerita faktual tentang kejadian buruk (12 kasus netral → negatif) | "Sebuah musibah baru saja menimpa kampung adat di bajawa, flores …" | netral → negatif |
| Ulasan restoran panjang yang campuran (8 kasus positif → negatif) | "Enak lumayan, tapi harganya mahal karena porsinya sedikit kecil …" | positif → negatif |
| Keluhan faktual pendek tetap terbaca netral | "Saya kapok menggunakan jasa lion air" | negatif → netral |

28 ulasan salah di kedua model; sebagian labelnya memang ambigu (misalnya cerita kejadian buruk yang dilabeli netral).

## 2. Topik

| k | NPMI held-out | NPMI topik acak | Stabilitas 5 seed | Keragaman |
|---|---|---|---|---|
| **4 (dipilih)** | **−0,078** | −0,912 | 1,000 | 0,93 |
| 5 | −0,207 | −0,907 | 0,872 | 0,92 |
| 6 | −0,241 | −0,908 | 0,758 | 0,90 |
| 8 | −0,372 | −0,910 | 0,726 | 0,90 |
| 12 | −0,413 | −0,908 | 0,671 | 0,88 |

| Topik | Ukuran | NPMI | Kata teratas | Sentimen (neg / net / pos) |
|---|---|---|---|---|
| 1 | 229 | 0,237 | enak, makan, makanannya, tempatnya, teman, harganya, nyaman | 53 / 19 / 157 |
| 2 | 231 | 0,185 | malam, hari, tempat, pemandangan, bagus, suasana, restoran | 78 / 62 / 91 |
| 3 | 167 | −0,763 | orang, sulit, melihat, jalan, pulsa, macet, warga | 94 / 56 / 17 |
| 4 | 353 | 0,027 | harga, rasa, pelayanan, makanan, menu, goreng, mahal | 150 / 90 / 113 |

20 ulasan tidak memuat kata topik sama sekali (tidak diberi topik).

Tafsiran jujur: topik 1, 2, 4 koheren (kuliner dan tempat), jauh di atas topik acak. Topik 3 adalah campuran isu publik, lalu lintas, dan operator seluler dengan NPMI −0,76, dan ditandai sebagai campuran di website. Makin banyak topik, koherensi turun karena korpus 1.000 ulasan pendek dari banyak domain tidak cukup untuk tema yang lebih halus. Dataset yang lebih besar dan seragam (PRDECT-ID) diharapkan membantu, belum diuji.

Catatan proses: saat eksplorasi saya juga melihat NPMI top-5 dan NPMI pada seluruh korpus untuk memahami skala angka. Aturan pemilihan k tetap memakai NPMI top-10 held-out seperti rencana awal; tidak ada parameter yang diubah setelah melihat angka itu.

## 3. Perbandingan dengan kriteria penerimaan

| No | Kriteria | Status | Bukti |
|---|---|---|---|
| K1 | Dataset berizin, data card, checksum | **Lulus sebagian** | NusaX CC BY-SA 4.0, `docs/kartu-data.md`, SHA-256 di manifest. PRDECT-ID belum bisa diunduh (host diblokir). |
| K2 | PII scrub teruji + laporan | Lulus | `tests/test_pii.py` (5 tes), `dataset.pii_removed` di results.json |
| K3 | Baseline TF-IDF, pemilihan tanpa test | Lulus | `baseline.py`, `tests/test_realdata.py::test_test_split_not_used_for_selection`, verify_published |
| K4 | Encoder Indonesia pra-latih dievaluasi pada test yang sama | Lulus | IndoBERT base p1 di-fine-tune (GitHub Actions run 41083480509), `reports/encoder_run.json`; urutan test_ids dicek sama dengan TF-IDF di `pipeline.py` |
| K5 | Macro-F1 + CI, per kelas, confusion untuk kedua model | Lulus | Bagian 1; dihitung ulang secara independen oleh `tools/verify_published.py` (2 model) |
| K6 | Uji beda berpasangan TF-IDF vs encoder | Lulus | +0,127 (CI 0,086 sampai 0,168), McNemar 60 vs 9, p < 0,001; `results.json` bagian `encoder.vs_tfidf` |
| K7 | Topic model + NPMI + stabilitas 5 seed | Lulus | `topics.py`, `tests/test_topics.py`, tabel di atas |
| K8 | Analisis kesalahan | Lulus | Bagian 1, halaman Jelajah ulasan (pola kesalahan dapat difilter) |
| K9 | Reproduksi identik + notebook Kaggle | **Lulus sebagian** | Evaluasi (termasuk IndoBERT dari `encoder_run.json`) direproduksi byte demi byte oleh `test_pipeline_reproduces_committed_results_exactly`. Fine-tuning dijalankan di GitHub Actions, bukan Kaggle; notebook Kaggle ada tetapi belum dijalankan. Melatih ulang IndoBERT di perangkat lain bisa memberi angka sedikit berbeda. |
| K10 | Website coral + lilac, model browser teruji paritas, encoder berlabel | Lulus (lokal) | Svelte 5 + ECharts; `web/tests/model.test.js` paritas 400/400; IndoBERT diberi label "hasil precomputed"; e2e 137 pemeriksaan lulus (CSP ketat, axe WCAG AA, 320/375/768/1440 px, terang dan gelap). Situs live belum diverifikasi. |
| K11 | Model card, README batas klaim, responsif | Lulus | `docs/kartu-model.md`, README, screenshot e2e |

**Kesimpulan: inti spesifikasi Master terpenuhi** ("TF-IDF vs encoder; macro-F1, topic consistency, confusion matrix"): kedua model dilatih dan dievaluasi pada test yang sama, dengan uji beda berpasangan. Penyimpangan yang perlu disetujui Shandy: fine-tuning dijalankan di GitHub Actions (CPU), bukan Kaggle (K9 sebagian), dan PRDECT-ID tidak dipakai (K1 sebagian). Proyek belum selesai sampai website dideploy, diverifikasi live, dan disetujui Shandy.
