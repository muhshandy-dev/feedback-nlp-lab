"""Periksa situs live: halaman terbuka, header keamanan terpasang, data sama dengan repo.

Pemakaian: python tools/check_live.py https://feedback-nlp-lab.pages.dev
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_HEADERS = {
    "content-security-policy": "script-src 'self'",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "feedback-nlp-lab-check"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (URL dari pemilik repo)
        return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()


def main(base: str) -> int:
    base = base.rstrip("/")
    errors = []
    status, headers, body = get(base + "/")
    if status != 200 or b"Feedback NLP Lab" not in body:
        errors.append(f"halaman utama: status {status}")
    for name, needle in REQUIRED_HEADERS.items():
        if needle not in headers.get(name, ""):
            errors.append(f"header {name} tidak memuat {needle!r}")
    for f in ("results.json", "test_predictions.json", "model.json"):
        _, _, live = get(f"{base}/data/{f}")
        local = (ROOT / "web" / "public" / "data" / f).read_bytes()
        if json.loads(live) != json.loads(local):
            errors.append(f"data/{f} di situs berbeda dengan repo")
    if errors:
        print("GAGAL:\n- " + "\n- ".join(errors))
        return 1
    print(f"OK: {base} tampil, header keamanan ada, data sama dengan repo")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "https://feedback-nlp-lab.pages.dev"))
