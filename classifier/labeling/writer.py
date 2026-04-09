from __future__ import annotations
import json
from pathlib import Path
from .schemas import LLMSMELabel


def write_labels(labels: list[LLMSMELabel], out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for lbl in labels:
            d = lbl.model_dump()
            fh.write(json.dumps(d, sort_keys=True, ensure_ascii=False) + "\n")
