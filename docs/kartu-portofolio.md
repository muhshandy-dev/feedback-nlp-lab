# Kartu portofolio: Feedback NLP Lab

**Status: model dan evaluasi lengkap; situs belum dideploy.** Jangan tampilkan sebagai proyek selesai sampai situs live diperiksa dan Shandy menyetujuinya.

- **Judul**: Feedback NLP Lab
- **Satu kalimat**: Analisis sentimen dan topik ulasan berbahasa Indonesia, dengan baseline TF-IDF yang berjalan di browser dan pembanding encoder IndoBERT pada test set yang sama.
- **Bidang**: NLP bahasa Indonesia, klasifikasi teks, topic modeling, evaluasi model.
- **Data**: NusaX-Senti (Indonesia), 1.000 ulasan, CC BY-SA 4.0.
- **Angka utama (sudah dijalankan)**: TF-IDF + regresi logistik macro-F1 0,772 (95% CI 0,729 sampai 0,813) pada 400 ulasan uji, dibanding 0,184 untuk tebakan kelas mayoritas. 4 topik NMF dengan NPMI held-out −0,078 (topik acak −0,912).
- **IndoBERT (fine-tuned di GitHub Actions, CPU)**: macro-F1 0,900 (95% CI 0,868 sampai 0,929), lebih baik dari TF-IDF sebesar +0,127 (95% CI 0,086 sampai 0,168, McNemar p < 0,001).
- **Belum dijalankan**: notebook Kaggle (pelatihan dilakukan di GitHub Actions).
- **Keahlian yang ditunjukkan**: pemilihan model tanpa menyentuh test, interval kepercayaan bootstrap dan uji McNemar, metrik konsistensi topik, penghapusan data pribadi, inferensi model di browser yang paritasnya diuji, website statis aman (CSP ketat) dan aksesibel.
- **Stack**: Python, scikit-learn, PyTorch + Transformers (encoder), Svelte 5, Vite, ECharts, Playwright, GitHub Actions, Cloudflare Pages.
- **Tautan**: repo `github.com/muhshandy-dev/feedback-nlp-lab`, demo `feedback-nlp-lab.pages.dev` (belum dideploy).
