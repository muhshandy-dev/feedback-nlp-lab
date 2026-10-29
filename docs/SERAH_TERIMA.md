# Serah terima Feedback NLP Lab

Tanggal: 29 Oktober 2026. Status: **belum selesai**. Semua bagian yang tidak butuh akses tambahan sudah dikerjakan dan diuji. Yang tersisa bergantung pada tiga langkah pemilik repo.

## Sudah selesai dan teruji

| Bagian | Bukti |
|---|---|
| Data NusaX terkunci + checksum, cek kebocoran lintas split | `tests/test_data.py`, `tests/test_realdata.py` |
| Penghapus data pribadi | `tests/test_pii.py` |
| Baseline TF-IDF, pemilihan 5-fold CV, test macro-F1 0,772 | `reports/results.json`, `docs/laporan-evaluasi.md` |
| Topik NMF + NPMI held-out + stabilitas + pembanding acak | `tests/test_topics.py` |
| Hasil bisa direproduksi byte demi byte | `test_pipeline_reproduces_committed_results_exactly` |
| Pemeriksaan independen angka website | `tools/verify_published.py` |
| Kode fine-tuning IndoBERT + jalur evaluasinya | `tests/test_encoder.py` (BERT mini acak, bukan hasil IndoBERT) |
| Website Svelte + ECharts, model TF-IDF di browser | `web/tests/model.test.js` paritas 400/400; e2e 134 pemeriksaan |

## Langkah pemilik repo

1. **Buat repo kosong** `muhshandy-dev/feedback-nlp-lab` (public, tanpa README) dan pasang Claude GitHub App. Setelah itu Claude mendorong kode dan membuka PR draft.
2. **Jalankan IndoBERT**, pilih salah satu:
   - (disarankan, tanpa ubah pengaturan) GitHub, tab Actions, workflow **Fine-tune IndoBERT**, Run workflow pada branch PR. Sekitar 1 jam di CPU runner, hasil mentah di-commit otomatis ke branch itu.
   - atau izinkan host `us.aws.cdn.hf.co` di pengaturan jaringan environment, lalu Claude menjalankan `tools/selesaikan_encoder.sh` di sesi.
   - atau jalankan `notebooks/kaggle_encoder.ipynb` di Kaggle (GPU, Internet on) dan unggah `encoder_run.json`.
3. **Deploy** Cloudflare Pages sesuai `docs/DEPLOY_CLOUDFLARE.md`, lalu jalankan workflow **Periksa situs live**.

Setelah langkah 2, Claude menjalankan `feedbacklab run`, memperbarui laporan, dan membandingkan ulang dengan kriteria K4 dan K6. Hasil IndoBERT dilaporkan apa adanya, termasuk bila tidak lebih baik dari TF-IDF.

## Opsional

- PRDECT-ID (5.400 ulasan Tokopedia, CC BY 4.0) butuh host `data.mendeley.com`. Belum ada kode pemuatnya karena format berkas aslinya belum bisa diperiksa; bukan syarat Master.

## Yang tidak boleh diklaim saat ini

Hasil IndoBERT, hasil Kaggle, situs live, dan PRDECT-ID.
