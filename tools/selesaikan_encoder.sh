#!/usr/bin/env bash
# Jalankan setelah bobot IndoBERT bisa diunduh (atau setelah reports/encoder_run.json dari
# workflow "Fine-tune IndoBERT" sudah di-commit). Mengisi evaluasi encoder lalu memeriksa semuanya.
set -euo pipefail
cd "$(dirname "$0")/.."

feedbacklab data fetch
if [[ ! -f reports/encoder_run.json ]]; then
  echo "encoder_run.json belum ada: fine-tune di mesin ini (CPU sekitar 1 jam, GPU beberapa menit)"
  feedbacklab encoder
fi
feedbacklab run
python tools/verify_published.py
pytest -q
(cd web && npm ci && npm test && npm run build && npm run e2e)
echo "Selesai. Perbarui docs/laporan-evaluasi.md dan README dengan angka dari reports/results.json."
