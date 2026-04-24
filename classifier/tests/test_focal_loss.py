import torch
from classifier.ensemble.focal_loss import focal_loss


def test_focal_loss_basic_shape():
    logits = torch.randn(8, 4)
    labels = torch.tensor([0, 1, 2, 3, 0, 1, 2, 3])
    loss = focal_loss(logits, labels, n_classes=4)
    assert loss.shape == ()
    assert loss.item() > 0


def test_focal_loss_correct_predictions_low_loss():
    logits_good = torch.tensor([[5.0, -5, -5, -5], [-5, 5, -5, -5]])
    logits_bad = torch.tensor([[-5.0, 5, -5, -5], [5, -5, -5, -5]])
    labels = torch.tensor([0, 1])
    loss_good = focal_loss(logits_good, labels)
    loss_bad = focal_loss(logits_bad, labels)
    assert loss_good < loss_bad


def test_focal_loss_gamma_zero_equals_ce():
    logits = torch.randn(16, 4)
    labels = torch.randint(0, 4, (16,))
    fl = focal_loss(logits, labels, gamma=0.0, alpha=None)
    ce = torch.nn.functional.cross_entropy(logits, labels)
    assert torch.allclose(fl, ce, atol=1e-5)


def test_focal_loss_with_class_weights():
    logits = torch.randn(8, 4)
    labels = torch.tensor([0, 0, 0, 0, 1, 2, 3, 3])
    alpha = torch.tensor([0.1, 0.3, 0.3, 0.3])
    loss = focal_loss(logits, labels, alpha=alpha)
    assert loss.item() > 0
