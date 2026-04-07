"""Tests for the fine-tuned embedding model.

These tests are skipped automatically if the fine-tuned model directory
does not exist (e.g. on a fresh checkout where Session 5 hasn't been
run yet).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
FT_PATH = REPO / "mapping_engine" / "models" / "finetuned-crosswalk-v1"

pytestmark = pytest.mark.skipif(
    not (FT_PATH / "config.json").exists(),
    reason="fine-tuned model not present",
)


def test_loads_from_local_path():
    from mapping_engine.engine.semantic import _load_model

    model = _load_model(str(FT_PATH))
    assert model is not None
    assert model.get_sentence_embedding_dimension() == 1024


def test_embeddings_differ_from_base():
    from mapping_engine.engine.semantic import _load_model

    base = _load_model("BAAI/bge-large-en-v1.5")
    ft = _load_model(str(FT_PATH))
    text = "implement real-time input filtering for adversarial prompts"
    eb = base.encode(text, show_progress_bar=False)
    ef = ft.encode(text, show_progress_bar=False)
    assert eb.shape == ef.shape
    diff = float(np.linalg.norm(eb - ef))
    assert diff > 1e-4
