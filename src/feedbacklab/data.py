"""Pengambilan, verifikasi, dan pemuatan NusaX-Senti (Indonesia) pada commit yang dikunci."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

from .pii import scrub

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "data" / "nusax_manifest.json"
DEFAULT_DATA_DIR = ROOT / "data" / "raw" / "nusax"
RAW_URL = "https://raw.githubusercontent.com/{repo}/{commit}/{path}/{split}.csv"

SPLITS = ("train", "valid", "test")
LABELS = ("negative", "neutral", "positive")


def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def sha256_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _download(url: str, dest: Path, retries: int = 4) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 (https tetap)
                dest.write_bytes(r.read())
            return
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(2 * 2**attempt)


def fetch(data_dir: Path = DEFAULT_DATA_DIR) -> None:
    """Unduh ketiga split dari commit yang dikunci, lalu cocokkan checksum."""
    m = manifest()
    for split in SPLITS:
        dest = Path(data_dir) / f"{split}.csv"
        if not dest.exists():
            url = RAW_URL.format(repo=m["repo"], commit=m["commit"], path=m["path"], split=split)
            _download(url, dest)
    verify(data_dir)


def verify(data_dir: Path = DEFAULT_DATA_DIR) -> None:
    m = manifest()
    for split, expected in m["files"].items():
        got = sha256_of(Path(data_dir) / f"{split}.csv")
        if got != expected:
            raise ValueError(f"checksum {split}.csv tidak cocok: {got} != {expected}")


def load(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, pd.DataFrame]:
    """Muat split resmi. Teks sudah melewati penghapusan data pribadi."""
    verify(data_dir)
    out = {}
    for split in SPLITS:
        df = pd.read_csv(Path(data_dir) / f"{split}.csv")
        if set(df["label"]) - set(LABELS):
            raise ValueError(f"label tak dikenal di {split}")
        cleaned = df["text"].map(scrub)
        df = df.assign(
            text=cleaned.map(lambda r: r.text),
            pii=cleaned.map(lambda r: r.counts),
        )
        out[split] = df[["id", "text", "label", "pii"]].reset_index(drop=True)
    _check_disjoint(out)
    return out


def _check_disjoint(splits: dict[str, pd.DataFrame]) -> None:
    """Teks yang sama tidak boleh muncul di dua split (kebocoran)."""
    seen: dict[str, str] = {}
    for name, df in splits.items():
        for t in df["text"].str.lower().str.strip():
            if t in seen and seen[t] != name:
                raise ValueError(f"teks duplikat lintas split {seen[t]} dan {name}")
            seen[t] = name
