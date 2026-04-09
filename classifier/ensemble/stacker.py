"""LightGBM stacker for the AI security framework crosswalk classifier."""
from __future__ import annotations

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    lgb = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# V1 feature columns (original single cross-encoder baseline)
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    "score_ce",
    "score_bm25",
    "score_bridge",
    "gat_dot",
    "gat_cosine",
]

# ---------------------------------------------------------------------------
# V2 features: Multi-encoder ensemble
# ---------------------------------------------------------------------------
CE_MODEL_NAMES = ["deberta", "roberta", "electra"]
CE_LOGIT_COLS = [f"{m}_logit_{i}" for m in CE_MODEL_NAMES for i in range(4)]
CE_CLS_SIM_COLS = [f"{m}_cls_sim" for m in CE_MODEL_NAMES]
GAT_V2_DIFF_COLS = [f"gat_diff_{d:02d}" for d in range(64)]
GAT_V2_SCALAR_COLS = ["gat_dot", "gat_cosine"]
BASELINE_V2_COLS = ["score_bm25", "score_bridge"]

FEATURE_COLS_V2 = (
    CE_LOGIT_COLS       # 12 (3 models × 4 logits)
    + CE_CLS_SIM_COLS   # 3
    + GAT_V2_DIFF_COLS  # 64
    + GAT_V2_SCALAR_COLS  # 2
    + BASELINE_V2_COLS  # 2
)  # Total: 83


# ---------------------------------------------------------------------------
# Stacker
# ---------------------------------------------------------------------------
class LGBMStacker:
    """Thin wrapper around a LightGBM booster used as the ensemble stacker."""

    def __init__(self, params: dict | None = None, version: str = "v1") -> None:
        self.params = params
        self.model: "lgb.Booster | None" = None
        self.run_id: str = ""
        self.version = version
        self.feature_cols = FEATURE_COLS if version == "v1" else FEATURE_COLS_V2
