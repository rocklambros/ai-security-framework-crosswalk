# Licensing decision record

## Code

MIT (unchanged). See top-level `LICENSE` (to be written as part of Plan 8
Task G).

## Upstream data (`data/upstream/`)

CC BY-SA 4.0 per the GenAI Security Project crosswalk repository
(pinned commit recorded in `data/upstream/source_pin.json`). Attribution
and ShareAlike obligations propagate to any derivative distribution of
this data.

## Released trained model weights

**CC BY-SA 4.0.**

### Reasoning

Upstream training data is CC BY-SA 4.0. The legal question of whether a
trained classifier whose weights encode that data is a "derivative work"
under Creative Commons is unsettled, with credible arguments on both
sides. Rather than take a position in the middle of a contested area of
law, we adopt the safe-and-simple rule:

> If the training data is CC BY-SA 4.0 and the trained model is distributed
> as an artifact that meaningfully depends on that data (e.g., weights, not
> just architecture), the model weights inherit CC BY-SA 4.0.

This means:

1. The HuggingFace model upload in Plan 7 and the HF model upload in
   Plan 8 both carry a `CC-BY-SA-4.0` license tag in their model cards.
2. Attribution (upstream GenAI Security Project crosswalk + pinned SHA)
   is required of any downstream user.
3. Downstream distributions of our weights must also be CC BY-SA 4.0.
4. Combining our weights with more-restrictive training data is permitted
   so long as the distributed artifact remains CC BY-SA 4.0 or more
   permissive on its ShareAlike clause.

### What is NOT CC BY-SA

- Architecture code (`classifier/ensemble/*.py`, etc.) — this is MIT.
- Configuration files, scripts, documentation — MIT.
- Paper text and figures — Creative Commons Attribution 4.0 (CC BY 4.0)
  unless explicitly marked otherwise, to allow broad reuse.

### Why not MIT on the weights?

MIT on the weights would be cleaner for downstream users but arguably
violates the ShareAlike clause of CC BY-SA 4.0 if a court ever rules
that weights are derivative works. CC BY-SA 4.0 on the weights is the
strictly-safe choice even if the legal question later resolves in favor
of a more permissive treatment. If that happens, we can relicense
downward; we cannot relicense upward without everyone's consent.

## Cross-references

- Plan 7 model card template MUST include this license decision.
- Plan 8 LICENSE file + CITATION.cff MUST reference this document.
- `THIRD_PARTY_NOTICES.md` (Plan 7) vendors upstream attribution text.
