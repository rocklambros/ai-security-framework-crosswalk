import pandas as pd
from classifier.data.sme_pool import load_sme_pool, EXPECTED_TOTAL

REQUIRED_COLS = {
    "pair_key", "pair_name", "source_node_id", "target_node_id",
    "source_text", "target_text", "expert_tier", "framework_pair",
}

def test_load_sme_pool_shape():
    df = load_sme_pool()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == EXPECTED_TOTAL  # 550
    missing = REQUIRED_COLS - set(df.columns)
    assert not missing, f"missing columns: {missing}"

def test_pair_key_unique():
    df = load_sme_pool()
    assert df["pair_key"].is_unique

def test_expert_tier_in_domain():
    df = load_sme_pool()
    assert set(df["expert_tier"].unique()) <= {"Direct", "Related", "None", "Tangential"}

def test_eleven_framework_pairs():
    df = load_sme_pool()
    assert df["framework_pair"].nunique() == 11
