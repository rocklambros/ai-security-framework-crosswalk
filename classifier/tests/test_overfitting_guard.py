"""Test OverfittingGuard detects train/val loss divergence."""


def test_overfitting_detected_after_consecutive_val_increases():
    from classifier.ensemble.cross_encoder_trainer import _OverfittingGuard

    guard = _OverfittingGuard(patience=2, lr_factor=0.5)

    action = guard.step(train_loss=1.0, val_loss=1.0)
    assert action == "ok"

    action = guard.step(train_loss=0.8, val_loss=1.1)
    assert action == "ok"

    action = guard.step(train_loss=0.6, val_loss=1.3)
    assert action == "reduce_lr"


def test_overfitting_guard_stops_after_extended_divergence():
    from classifier.ensemble.cross_encoder_trainer import _OverfittingGuard

    guard = _OverfittingGuard(patience=2, lr_factor=0.5, max_lr_reductions=2)

    guard.step(train_loss=1.0, val_loss=1.0)
    guard.step(train_loss=0.8, val_loss=1.1)
    action = guard.step(train_loss=0.6, val_loss=1.3)
    assert action == "reduce_lr"

    guard.acknowledge_lr_reduction()

    guard.step(train_loss=0.5, val_loss=1.4)
    action = guard.step(train_loss=0.4, val_loss=1.6)
    assert action == "reduce_lr"

    guard.acknowledge_lr_reduction()

    guard.step(train_loss=0.3, val_loss=1.7)
    action = guard.step(train_loss=0.2, val_loss=1.9)
    assert action == "stop"


def test_overfitting_guard_resets_on_improvement():
    from classifier.ensemble.cross_encoder_trainer import _OverfittingGuard

    guard = _OverfittingGuard(patience=2, lr_factor=0.5)

    guard.step(train_loss=1.0, val_loss=1.0)
    guard.step(train_loss=0.8, val_loss=1.1)
    guard.step(train_loss=0.6, val_loss=0.9)

    guard.step(train_loss=0.5, val_loss=1.0)
    action = guard.step(train_loss=0.4, val_loss=0.95)
    assert action == "ok"
