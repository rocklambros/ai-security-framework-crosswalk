from classifier.data.splits import build_splits, SEED
from classifier.data.sme_pool import load_sme_pool

def test_split_fraction():
    pool = load_sme_pool()
    splits = build_splits(pool, seed=SEED)
    total = len(splits["human_cal"]) + len(splits["human_test_frozen"])
    assert total == len(pool)
    frozen_frac = len(splits["human_test_frozen"]) / total
    assert 0.18 <= frozen_frac <= 0.22, f"Frozen fraction {frozen_frac:.3f} not ~20%"

def test_splits_disjoint():
    pool = load_sme_pool()
    splits = build_splits(pool, seed=SEED)
    cal_keys = set(splits["human_cal"]["pair_key"])
    frozen_keys = set(splits["human_test_frozen"]["pair_key"])
    assert cal_keys.isdisjoint(frozen_keys)
    assert len(cal_keys | frozen_keys) == len(pool)

def test_splits_deterministic():
    df = load_sme_pool()
    s1 = build_splits(df, seed=SEED)
    s2 = build_splits(df, seed=SEED)
    assert list(s1["human_cal"]["pair_key"]) == list(s2["human_cal"]["pair_key"])

def test_stratification_covers_every_pair():
    splits = build_splits(load_sme_pool(), seed=SEED)
    cal_pairs = set(splits["human_cal"]["framework_pair"])
    frozen_pairs = set(splits["human_test_frozen"]["framework_pair"])
    assert cal_pairs == frozen_pairs


def test_stratification_fallback_on_singleton():
    import pandas as pd
    rows = []
    rows += [{"framework_pair": "pair_A", "expert_tier": "Direct",  "pair_key": f"A::d{i}"} for i in range(5)]
    rows += [{"framework_pair": "pair_A", "expert_tier": "Related", "pair_key": f"A::r{i}"} for i in range(5)]
    rows += [{"framework_pair": "pair_A", "expert_tier": "Tangential", "pair_key": "A::t0"}]
    rows += [{"framework_pair": "pair_B", "expert_tier": "Direct",  "pair_key": f"B::d{i}"} for i in range(5)]
    rows += [{"framework_pair": "pair_B", "expert_tier": "Related", "pair_key": f"B::r{i}"} for i in range(4)]
    df = pd.DataFrame(rows)
    assert len(df) == 20
    out = build_splits(df, seed=42, cal_size=5, frozen_size=15)
    cal_keys = set(out["human_cal"]["pair_key"])
    frozen_keys = set(out["human_test_frozen"]["pair_key"])
    assert cal_keys.isdisjoint(frozen_keys)
    assert len(cal_keys | frozen_keys) == 20
    assert set(out["human_cal"]["framework_pair"]) == {"pair_A", "pair_B"}
    assert set(out["human_test_frozen"]["framework_pair"]) == {"pair_A", "pair_B"}
