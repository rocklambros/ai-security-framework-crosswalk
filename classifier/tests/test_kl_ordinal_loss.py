"""Tests for KL-divergence ordinal loss with Gaussian soft targets."""
import pytest
import numpy as np


def test_soft_target_sums_to_one():
    """Soft targets must be valid probability distributions."""
    torch = pytest.importorskip("torch")
    from classifier.ensemble.kl_ordinal_loss import ordinal_soft_targets

    for label in range(4):
        targets = ordinal_soft_targets(
            torch.tensor([label]), n_classes=4, sigma=0.75
        )
        np.testing.assert_allclose(
            targets.sum(dim=1).numpy(), 1.0, atol=1e-6,
            err_msg=f"Soft target for label {label} does not sum to 1",
        )


def test_soft_target_peaks_at_label():
    """The maximum probability should be at the true label."""
    torch = pytest.importorskip("torch")
    from classifier.ensemble.kl_ordinal_loss import ordinal_soft_targets

    for label in range(4):
        targets = ordinal_soft_targets(
            torch.tensor([label]), n_classes=4, sigma=0.75
        )
        assert targets.argmax(dim=1).item() == label


def test_soft_target_ordinal_neighbors():
    """Adjacent classes should have higher probability than distant ones."""
    torch = pytest.importorskip("torch")
    from classifier.ensemble.kl_ordinal_loss import ordinal_soft_targets

    targets = ordinal_soft_targets(torch.tensor([2]), n_classes=4, sigma=0.75)
    t = targets[0]
    assert t[1].item() > t[0].item(), "P(PARTIAL) should exceed P(UNRELATED) for label RELATED"
    assert t[3].item() > t[0].item(), "P(EQUIVALENT) should exceed P(UNRELATED) for label RELATED"


def test_kl_ordinal_loss_finite():
    """Loss must be finite and positive for random logits."""
    torch = pytest.importorskip("torch")
    from classifier.ensemble.kl_ordinal_loss import kl_ordinal_loss

    logits = torch.randn(16, 4)
    labels = torch.randint(0, 4, (16,))
    loss = kl_ordinal_loss(logits, labels, n_classes=4, sigma=0.75)
    assert loss.item() > 0
    assert np.isfinite(loss.item())


def test_kl_ordinal_loss_decreases_with_correct_logits():
    """Loss should be lower when logits match the true labels."""
    torch = pytest.importorskip("torch")
    from classifier.ensemble.kl_ordinal_loss import kl_ordinal_loss

    labels = torch.tensor([0, 1, 2, 3])
    good_logits = torch.eye(4) * 10.0
    # Deliberately wrong: each sample predicts the opposite extreme class
    bad_logits = torch.eye(4).flip(dims=[1]) * 10.0

    good_loss = kl_ordinal_loss(good_logits, labels, n_classes=4, sigma=0.75)
    bad_loss = kl_ordinal_loss(bad_logits, labels, n_classes=4, sigma=0.75)
    assert good_loss.item() < bad_loss.item()


def test_sigma_controls_smoothness():
    """Larger sigma should produce smoother (higher entropy) targets."""
    torch = pytest.importorskip("torch")
    from classifier.ensemble.kl_ordinal_loss import ordinal_soft_targets

    label = torch.tensor([2])
    narrow = ordinal_soft_targets(label, n_classes=4, sigma=0.3)
    wide = ordinal_soft_targets(label, n_classes=4, sigma=1.5)

    def entropy(p):
        return -(p * torch.log(p + 1e-10)).sum().item()

    assert entropy(narrow[0]) < entropy(wide[0])
