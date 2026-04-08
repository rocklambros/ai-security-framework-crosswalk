from classifier.data.splits import build_splits, SEED
from classifier.data.sme_pool import load_sme_pool

def test_split_sizes():
    splits = build_splits(load_sme_pool(), seed=SEED)
    assert len(splits["human_cal"]) == 150
    assert len(splits["human_test_frozen"]) == 400

def test_splits_disjoint():
    splits = build_splits(load_sme_pool(), seed=SEED)
    cal_keys = set(splits["human_cal"]["pair_key"])
    frozen_keys = set(splits["human_test_frozen"]["pair_key"])
    assert cal_keys.isdisjoint(frozen_keys)
    assert len(cal_keys | frozen_keys) == 550

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
    assert len(frozen_pairs) == 11
