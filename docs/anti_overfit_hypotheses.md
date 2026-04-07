# Pre-Registered Hypotheses Log

This file records every hypothesis pre-registered before running cross-validation on a new feature, model change, or calibration adjustment, per the methodology in `docs/anti_overfit_methodology.md`.

**Format:** each entry is a dated section. Hypotheses are written **before** seeing CV results. The result is filled in afterward, regardless of outcome — negative results are not deleted.

**Decision rule for every entry:** an improvement only counts if the bootstrap 95% CI on the delta vs baseline excludes 0 AND the predicted direction matches the observed direction AND any related permutation-importance CI excludes 0.

---

<!-- Append new entries below this line. Do not edit prior entries except to fill in their result. -->
