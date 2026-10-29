# Kartu portofolio: Feedback NLP Lab

**Status: dalam pengerjaan.** Jangan tampilkan sebagai proyek selesai sampai pembanding IndoBERT dijalankan dan situs dideploy.

- **Judul**: Feedback NLP Lab
- **Satu kalimat**: Analisis sentimen dan topik ulasan berbahasa Indonesia, dengan baseline TF-IDF yang berjalan di browser dan pembanding encoder IndoBERT pada test set yang sama.
- **Bidang**: NLP bahasa Indonesia, klasifikasi teks, topic modeling, evaluasi model.
- **Data**: NusaX-Senti (Indonesia), 1.000 ulasan, CC BY-SA 4.0.
- **Angka utama (sudah dijalankan)**: TF-IDF + regresi logistik macro-F1 0,772 (95% CI 0,729 sampai 0,813) pada 400 ulasan uji, dibanding 0,184 untuk tebakan kelas mayoritas. 4 topik NMF dengan NPMI held-out −0,078 (topik acak −0,912).
- **Belum dijalankan**: fine-tuning IndoBERT dan uji beda TF-IDF vs IndoBERT.
- **Keahlian yang ditunjukkan**: pemilihan model tanpa menyentuh test, interval kepercayaan bootstrap dan uji McNemar, metrik konsistensi topik, penghapusan data pribadi, inferensi model di browser yang paritasnya diuji, website statis aman (CSP ketat) dan aksesibel.
- **Stack**: Python, scikit-learn, PyTorch + Transformers (encoder), Svelte 5, Vite, ECharts, Playwright, GitHub Actions, Cloudflare Pages.
- **Tautan**: repo `github.com/muhshandy-dev/feedback-nlp-lab` (belum dibuat), demo `feedback-nlp-lab.pages.dev` (belum dideploy).
