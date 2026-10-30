# Serah terima Feedback NLP Lab

Diperbarui 30 Oktober 2026. Status: **model dan evaluasi lengkap, situs belum dideploy**. Langkah 1 dan 2 sudah selesai; yang tersisa hanya deploy (langkah 3) dan pemeriksaan visual oleh pemilik.

## Sudah selesai dan teruji

| Bagian | Bukti |
|---|---|
| Data NusaX terkunci + checksum, cek kebocoran lintas split | `tests/test_data.py`, `tests/test_realdata.py` |
| Penghapus data pribadi | `tests/test_pii.py` |
| Baseline TF-IDF, pemilihan 5-fold CV, test macro-F1 0,772 | `reports/results.json`, `docs/laporan-evaluasi.md` |
| Topik NMF + NPMI held-out + stabilitas + pembanding acak | `tests/test_topics.py` |
| Hasil bisa direproduksi byte demi byte | `test_pipeline_reproduces_committed_results_exactly` |
| Pemeriksaan independen angka website | `tools/verify_published.py` |
| Kode fine-tuning IndoBERT + jalur evaluasinya | `tests/test_encoder.py` (BERT mini acak) |
| Fine-tuning IndoBERT sungguhan, test macro-F1 0,900 vs TF-IDF 0,772 | GitHub Actions run 41083480509, `reports/encoder_run.json` |
| Website Svelte + ECharts, model TF-IDF di browser | `web/tests/model.test.js` paritas 400/400; e2e 137 pemeriksaan |

## Langkah pemilik repo

1. ~~Buat repo kosong~~ (selesai 30 Oktober 2026). **Buat repo kosong** `muhshandy-dev/feedback-nlp-lab` (public, tanpa README) dan pasang Claude GitHub App. Setelah itu Claude mendorong kode dan membuka PR draft.
2. ~~Jalankan IndoBERT~~ (selesai: workflow Fine-tune IndoBERT, run 41083480509). Pilihan yang tersedia:
   - (disarankan, tanpa ubah pengaturan) GitHub, tab Actions, workflow **Fine-tune IndoBERT**, Run workflow pada branch PR. Sekitar 1 jam di CPU runner, hasil mentah di-commit otomatis ke branch itu.
   - atau izinkan host `us.aws.cdn.hf.co` di pengaturan jaringan environment, lalu Claude menjalankan `tools/selesaikan_encoder.sh` di sesi.
   - atau jalankan `notebooks/kaggle_encoder.ipynb` di Kaggle (GPU, Internet on) dan unggah `encoder_run.json`.
3. **Deploy** Cloudflare Pages sesuai `docs/DEPLOY_CLOUDFLARE.md`, lalu jalankan workflow **Periksa situs live**.

Setelah langkah 2, `feedbacklab run` dijalankan ulang, laporan diperbarui, dan kriteria K4 sampai K6 dibandingkan ulang (lihat `docs/laporan-evaluasi.md`).

## Opsional

- PRDECT-ID (5.400 ulasan Tokopedia, CC BY 4.0) butuh host `data.mendeley.com`. Belum ada kode pemuatnya karena format berkas aslinya belum bisa diperiksa; bukan syarat Master.

## Yang tidak boleh diklaim saat ini

Hasil Kaggle (IndoBERT dilatih di GitHub Actions), situs live, dan PRDECT-ID.
