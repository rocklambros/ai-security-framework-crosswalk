"""Entry point: load SME pool → stratified splits → write JSONL + SHA256 manifest."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from classifier.config import SPLITS_DIR
from classifier.data.sme_pool import load_sme_pool, COLUMNS
from classifier.data.splits import build_splits, SEED


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    pool = load_sme_pool()
    splits = build_splits(pool, seed=SEED)

    pool_path = SPLITS_DIR / "sme_pool_full.jsonl"
    pool.sort_values("pair_key")[list(COLUMNS)].to_json(
        pool_path, orient="records", lines=True,
        double_precision=10, date_format="iso", force_ascii=False,
    )

    paths = {"sme_pool_full.jsonl": pool_path}
    for name, df in splits.items():
        p = SPLITS_DIR / f"{name}.jsonl"
        df[list(COLUMNS)].to_json(
            p, orient="records", lines=True,
            double_precision=10, date_format="iso", force_ascii=False,
        )
        paths[f"{name}.jsonl"] = p

    hashes = {name: _sha256(p) for name, p in paths.items()}
    hashes["_meta"] = {
        "seed": SEED,
        "pool_size": len(pool),
        "cal_size": len(splits["human_cal"]),
        "frozen_size": len(splits["human_test_frozen"]),
    }
    (SPLITS_DIR / "hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True))
    print(json.dumps(hashes, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
