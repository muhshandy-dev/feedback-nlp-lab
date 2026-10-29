# Deploy ke Cloudflare Pages

Website statis hasil build Vite. Yang dipublikasikan adalah folder `web/dist`.

## Langkah (di dashboard Cloudflare milik pemilik repo)

1. Workers and Pages, Create, Pages, Connect to Git, pilih `feedback-nlp-lab`.
2. Project name: `feedback-nlp-lab` (alamat menjadi `https://feedback-nlp-lab.pages.dev` bila nama itu masih tersedia).
3. Production branch: `main`.
4. Framework preset: None. Root directory: `web`. Build command: `npm ci && npm run build`. Build output directory: `dist`.
5. Environment variable: `NODE_VERSION` = `22`.
6. Simpan dan deploy. Opsional: matikan preview build untuk branch non-produksi (kuota 500 build per bulan dipakai bersama semua proyek).

## Catatan

- `web/public/_headers` ikut tersalin ke `dist` dan memasang CSP ketat (`script-src 'self'`, `style-src 'self'`, tanpa pihak ketiga). Font IBM Plex Sans dan Fraunces (OFL) dibundel, jadi `font-src 'self'` cukup. Uji e2e memakai header yang sama dan gagal bila ada pelanggaran CSP.
- HTML dan `/data/*` dikirim `no-cache`; `/assets/*` bernama hash sehingga aman disimpan setahun.
- Berkas terbesar sekitar 700 KB (JavaScript ECharts) dan 520 KB (`data/model.json`), jauh di bawah batas 25 MiB.
- Situs statis tidak tidur saat idle.
- Data situs ditulis oleh `feedbacklab run` ke `web/public/data` dan di-commit.

## Pemeriksaan setelah deploy

Sesi pengembangan tidak bisa membuka `pages.dev`. Pemeriksaan otomatis tersedia di workflow **Periksa situs live** (tab Actions, Run workflow, isi URL). Workflow itu memastikan halaman, header keamanan, dan `data/results.json` di situs sama persis dengan isi repo.

Pemeriksaan manual (sekitar 3 menit): buka situs di jendela penyamaran, buka keenam menu (Ringkasan, Uji ulasan, Topik, Model, Jelajah ulasan, Metode), ketik satu ulasan di Uji ulasan, lalu coba di ponsel dan ganti tema.
