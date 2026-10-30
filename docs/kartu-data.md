# Kartu data: NusaX-Senti (bahasa Indonesia)

| Butir | Isi |
|---|---|
| Sumber | `IndoNLP/nusax`, `datasets/sentiment/indonesian/{train,valid,test}.csv`, commit `75b0be5d982348332509f296e10d9bf9cb66d60f` |
| Rujukan | Winata dkk., *NusaX: Multilingual Parallel Sentiment Dataset for 10 Indonesian Local Languages*, EACL 2023 |
| Lisensi | CC BY-SA 4.0 (data), Apache-2.0 (kode penyusun) |
| Ukuran | 500 latih, 100 validasi, 400 uji (split resmi, tidak diubah) |
| Label | negatif 383, netral 239, positif 378 (seluruh korpus) |
| Asal teks | Diambil dari SmSA (IndoNLU): ulasan dan komentar daring tentang restoran, tempat wisata, operator seluler, bank, layanan transportasi, isu publik |
| Integritas | SHA-256 tiap berkas dicek setiap kali dimuat (`data/nusax_manifest.json`) |
| Kebocoran | Program memeriksa tidak ada teks identik (setelah huruf kecil dan trim) di dua split |

## Data pribadi

Sebelum dipakai model atau ditampilkan, setiap teks melewati `feedbacklab.pii.scrub`: URL, email, akun `@`, nomor HP Indonesia (`08…`, `+62 8…`, `62 8…`, dengan pemisah spasi, titik, strip), dan deretan 10 digit atau lebih (NIK, rekening, kartu) diganti token `[URL]`, `[EMAIL]`, `[AKUN]`, `[TELEPON]`, `[NOMOR]`. Harga, tahun, dan "4G" tidak tersentuh. Jumlah yang dihapus dicatat per split di `reports/results.json` (`dataset.pii_removed`): pada versi ini 0, karena penyusun dataset sudah membersihkannya.

Nama orang dan merek di dalam teks (misalnya "lion air", "indosat") tidak dihapus: itu entitas publik yang menjadi objek ulasan, bukan data pribadi pengulas.

## Keterbatasan

- Kecil (1.000 ulasan) dan beragam domain, sehingga topik halus sulit dipelajari.
- Sebagian label ambigu (misalnya kalimat faktual tentang keluhan diberi label negatif, kalimat netral berisi kata "tidak ada gangguan").
- Hanya bahasa Indonesia baku dan semi-baku; bahasa daerah NusaX tidak dipakai.
