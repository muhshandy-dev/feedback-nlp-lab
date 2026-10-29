# Laporan evaluasi Feedback NLP Lab

Tanggal: 29 Oktober 2026. Semua angka dari `reports/results.json`, dihasilkan oleh `feedbacklab run` dan diperiksa ulang secara independen oleh `tools/verify_published.py`.

## 1. Klasifikasi sentimen (test resmi, 400 ulasan)

| Model | Macro-F1 | 95% CI | Akurasi | F1 neg | F1 net | F1 pos |
|---|---|---|---|---|---|---|
| Kelas mayoritas | 0,184 | 0,167 sampai 0,200 | 38,3% | 0,553 | 0,000 | 0,000 |
| TF-IDF karakter 2-5 + LR (C = 5) | 0,772 | 0,729 sampai 0,813 | 78,0% | 0,747 | 0,711 | 0,859 |
| IndoBERT base fine-tuned | belum dijalankan | | | | | |

TF-IDF dibanding kelas mayoritas: selisih macro-F1 +0,588 (95% CI bootstrap berpasangan 0,541 sampai 0,634); McNemar 197 ulasan hanya benar di TF-IDF vs 38 hanya benar di mayoritas, p < 0,001.

Confusion matrix TF-IDF (baris = asli, kolom = prediksi; negatif, netral, positif):

```
negatif  115  25  13
netral    21  69   6
positif   19   4 128
```

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

Kelas netral paling sulit (F1 0,711): paling sedikit contohnya dan sering berisi kata keluhan tanpa sentimen ("sinyal", "kartu"). Pola negasi dan kontras ("namun", "tapi") adalah alasan utama mengapa encoder kontekstual diharapkan lebih baik; itu belum terbukti sampai fine-tuning dijalankan.

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
| K4 | Encoder Indonesia pra-latih dievaluasi pada test yang sama | **BELUM** | Kode + tes jalur kode (`tests/test_encoder.py`) + notebook Kaggle ada; belum dijalankan karena bobot tidak bisa diunduh |
| K5 | Macro-F1 + CI, per kelas, confusion untuk kedua model | **Lulus sebagian** | Lengkap untuk TF-IDF dan mayoritas; encoder menunggu K4 |
| K6 | Uji beda berpasangan TF-IDF vs encoder | **BELUM** | `metrics.paired_comparison` teruji, dipakai untuk TF-IDF vs mayoritas; vs encoder menunggu K4 (`tests/test_encoder.py::test_pipeline_reads_encoder_run` membuktikan jalurnya) |
| K7 | Topic model + NPMI + stabilitas 5 seed | Lulus | `topics.py`, `tests/test_topics.py`, tabel di atas |
| K8 | Analisis kesalahan | Lulus | Bagian 1, halaman Jelajah ulasan (pola kesalahan dapat difilter) |
| K9 | Reproduksi identik + notebook Kaggle | **Lulus sebagian** | `test_pipeline_reproduces_committed_results_exactly` lulus; notebook ada tetapi belum dijalankan di Kaggle (kaggle.com diblokir dari lingkungan pembuatan) |
| K10 | Website coral + lilac, model browser teruji paritas, encoder berlabel | Lulus untuk TF-IDF | Svelte 5 + ECharts; `web/tests/model.test.js` paritas 400/400; e2e 134 pemeriksaan lulus (CSP ketat, axe WCAG AA, 320/375/768/1440 px, terang dan gelap) |
| K11 | Model card, README batas klaim, responsif | Lulus | `docs/kartu-model.md`, README, screenshot e2e |

**Kesimpulan: proyek BELUM memenuhi spesifikasi Master.** Inti "TF-IDF vs encoder" baru separuh: encoder belum dijalankan (K4, K6). Website belum dideploy dan belum diverifikasi live.
