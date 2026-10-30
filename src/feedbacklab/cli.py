"""Perintah: `feedbacklab data fetch`, `feedbacklab run`, `feedbacklab encoder`."""

from __future__ import annotations

import argparse
import json

from . import data


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="feedbacklab")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("data", help="unduh dan verifikasi NusaX-Senti")
    d.add_argument("action", choices=["fetch", "verify"])
    sub.add_parser("run", help="latih baseline, topik, evaluasi, ekspor ke website")
    e = sub.add_parser("encoder", help="fine-tune IndoBERT (butuh torch, transformers, bobot HF)")
    e.add_argument("--out", default=str(data.ROOT / "reports" / "encoder_run.json"))
    e.add_argument("--epochs", type=int, default=None)
    args = p.parse_args(argv)

    if args.cmd == "data":
        (data.fetch if args.action == "fetch" else data.verify)()
        print("data NusaX terverifikasi")
    elif args.cmd == "run":
        from .pipeline import run

        r = run()
        summary = {
            "tfidf_test_macro_f1": r["tfidf"]["test"]["macro_f1"],
            "majority_test_macro_f1": r["majority"]["test"]["macro_f1"],
            "encoder": r["encoder"].get("test", {}).get("macro_f1", r["encoder"]["status"]),
            "topics_k": r["topics"]["k"],
        }
        print(json.dumps(summary, indent=1))
    elif args.cmd == "encoder":
        from .encoder import run as run_encoder

        cfg = {"epochs": args.epochs} if args.epochs else None
        res = run_encoder(args.out, config=cfg)
        print(json.dumps({r["seed"]: r["valid_macro_f1"] for r in res["runs"]}))


if __name__ == "__main__":
    main()
