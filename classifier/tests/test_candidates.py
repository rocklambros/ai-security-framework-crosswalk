from classifier.data.candidates import FRAMEWORK_PAIRS, FRAMEWORKS


def test_twelve_framework_pairs():
    assert len(FRAMEWORK_PAIRS) == 12


def test_every_framework_in_at_least_two_pairs():
    """Feasibility: 9 fw x 2 = 18 appearances; 12 pairs x 2 sides = 24 slots. OK."""
    from collections import Counter
    appearances = Counter()
    for s, t in FRAMEWORK_PAIRS:
        appearances[s] += 1
        appearances[t] += 1
    for fw in FRAMEWORKS:
        assert appearances[fw] >= 2, f"{fw} appears in <2 pairs"
