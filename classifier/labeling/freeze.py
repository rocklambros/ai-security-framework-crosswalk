"""Freeze v1 silver labels into v1_frozen train/val splits.

Creates ``data/labels/llm_sme/v1_frozen/`` with:
  - ``llm_train.jsonl`` — 80% of labels (stratified by relation)
  - ``llm_val.jsonl``   — 20% of labels (stratified by relation)
  - ``hashes.json``     — SHA-256 of both files

All frozen-tuple pairs are verified absent before writing. If any label
touches a frozen endpoint, the script aborts without writing.

``verify_label_hashes()`` is a runtime guard called at entry by Plan 5+
scripts. It reads ``v1_frozen/hashes.json`` and asserts byte-stable SHA
integrity of the split files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sklearn.model_selection import train_test_split


V1_DIR = Path("data/labels/llm_sme/v1")
V1_FROZEN_DIR = Path("data/labels/llm_sme/v1_frozen")
V2_DIR = Path("data/labels/llm_sme/v2")
V2_FROZEN_DIR = Path("data/labels/llm_sme/v2_frozen")
FROZEN_TUPLES_PATH = Path("data/splits/frozen_tuples.json")


class LabelHashMismatchError(Exception):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_frozen_endpoints(path: Path = FROZEN_TUPLES_PATH) -> tuple[set, set]:
    ft = json.loads(path.read_text())
    frozen_src = {tuple(s) for s in ft["source_tuples"]}
    frozen_tgt = {tuple(t) for t in ft["target_tuples"]}
    return frozen_src, frozen_tgt


def _extract_endpoints(row: dict) -> tuple[tuple, tuple]:
    src_fw = row["source_framework"]
    src_id = row["source_id"]
    tgt_nid = row["target_node_id"]
    tgt_fw = row.get("target_framework") or tgt_nid.split(":")[0]
    tgt_id = tgt_nid.split(":", 1)[1] if ":" in tgt_nid else tgt_nid
    return (src_fw, src_id), (tgt_fw, tgt_id)


def freeze_and_split(
    v1_dir: Path = V1_DIR,
    out_dir: Path = V1_FROZEN_DIR,
    frozen_tuples_path: Path = FROZEN_TUPLES_PATH,
    val_fraction: float = 0.20,
    seed: int = 42,
    skip_endpoint_check: bool = False,
) -> dict:
    """Freeze labels into train/val splits, enforcing frozen-tuple exclusion.

    Returns dict with counts and file paths.
    Raises FileExistsError if out_dir already has split files (Contract 3).
    Raises RuntimeError if any label overlaps frozen endpoints
    (unless skip_endpoint_check=True, for v2 where train/test are
    pair-disjoint but share endpoints by design).
    """
    labels_path = v1_dir / "labels.jsonl"
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels not found: {labels_path}")

    train_path = out_dir / "llm_train.jsonl"
    val_path = out_dir / "llm_val.jsonl"
    hashes_path = out_dir / "hashes.json"

    if train_path.exists() or val_path.exists():
        raise FileExistsError(f"Contract 3: frozen splits already exist in {out_dir}")

    labels = [json.loads(l) for l in labels_path.read_text().splitlines() if l.strip()]

    # Verify no frozen endpoint overlap (v1 mode)
    # v2 labels share endpoints with frozen test but are pair-disjoint
    if not skip_endpoint_check:
        frozen_src, frozen_tgt = _load_frozen_endpoints(frozen_tuples_path)
        for i, row in enumerate(labels):
            src_ep, tgt_ep = _extract_endpoints(row)
            if src_ep in frozen_src:
                raise RuntimeError(
                    f"Frozen source endpoint in label row {i}: {src_ep}"
                )
            if tgt_ep in frozen_tgt:
                raise RuntimeError(
                    f"Frozen target endpoint in label row {i}: {tgt_ep}"
                )

    # Stratified split by relation
    relations = [r["relation"] for r in labels]
    train_rows, val_rows = train_test_split(
        labels, test_size=val_fraction, random_state=seed, stratify=relations
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    dumper = lambda r: json.dumps(r, sort_keys=True, ensure_ascii=True)

    with train_path.open("w") as f:
        for r in train_rows:
            f.write(dumper(r) + "\n")
    with val_path.open("w") as f:
        for r in val_rows:
            f.write(dumper(r) + "\n")

    hashes = {
        "llm_train.jsonl": _sha256(train_path),
        "llm_val.jsonl": _sha256(val_path),
    }
    hashes_path.write_text(json.dumps(hashes, sort_keys=True, indent=2))

    return {
        "n_total": len(labels),
        "n_train": len(train_rows),
        "n_val": len(val_rows),
        "train_path": str(train_path),
        "val_path": str(val_path),
        "hashes_path": str(hashes_path),
    }


def verify_label_hashes(
    frozen_dir: Path = V2_FROZEN_DIR,
) -> None:
    """Verify SHA-256 integrity of frozen label splits.

    Called at entry by Plan 5+ scripts. Raises LabelHashMismatchError if
    any file hash doesn't match the recorded value.
    """
    hashes_path = frozen_dir / "hashes.json"
    if not hashes_path.exists():
        raise LabelHashMismatchError(
            f"Label hashes file not found: {hashes_path}. "
            f"Run freeze_and_split() first."
        )
    recorded = json.loads(hashes_path.read_text())
    for filename, expected in recorded.items():
        fpath = frozen_dir / filename
        if not fpath.exists():
            raise LabelHashMismatchError(f"Frozen label file missing: {fpath}")
        actual = _sha256(fpath)
        if actual != expected:
            raise LabelHashMismatchError(
                f"Hash mismatch for {fpath}: expected {expected[:16]}..., got {actual[:16]}..."
            )
