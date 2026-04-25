"""Build Sections 1-2: Abstract, Plain English, Setup."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_notebook import (
    make_md, make_code, load_notebook, save_notebook,
    load_old_notebook, copy_old_cells,
)

# Always start fresh — do not load the existing notebook
nb = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.10.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
old = load_old_notebook()

# --- Cell 0: Title + Abstract ---
nb["cells"].append(make_md("""# AI Security Framework Crosswalk: From Baseline Failure to Ordinal Ensemble

**Author:** Rock Lambros, University of Denver, COMP 4433

**Abstract.** This notebook traces the development of a 4-class ordinal classifier for AI security framework crosswalks, from a baseline that scored 0% on its most important class to a 3-model ensemble that broke through.

The crosswalk dataset contains 983 security controls from nine AI security frameworks connected by 5,813 edges. Expert annotators labeled 179 pairs on a 4-tier ordinal scale: Unrelated, Partial, Related, Equivalent. The v7c baseline reached 81.0% exact accuracy and 0.512 macro F1, but scored 0.000 F1 on the Equivalent class. The classifier never predicted that two controls from different frameworks meant the same thing.

The Open Common Requirements Enumeration (OpenCRE) database provided 13,519 pairs with expert-curated relationships and a hop-distance structure that maps naturally onto ordinal tiers. After removing 34 pairs overlapping the frozen test set, 6,200 clean pairs remained. Disagreement mining---scoring these through v7c and selecting the 673 where it conflicted with OpenCRE labels---produced the v8 training augmentation.

v8b expanded augmentation further, but DeBERTa-large collapsed to single-class prediction and the LightGBM stacker overfit to training accuracy of 1.000 against validation accuracy of 0.528. Both failures pointed to the same problem: noisy proxy labels amplified by a learnable second stage.

v_final stripped the pipeline down. Mapping-level deduplication removed 56% of text-pair contamination from validation. Three ordinal loss functions (KL-divergence with ordinal smoothing, CORN ordinal regression, focal loss) replaced standard cross-entropy. Softmax averaging across RoBERTa-large, DeBERTa-v3-base, and BGE-large-v1.5 replaced the stacker. The result: macro F1 rose to 0.558 (+4.6 pp), Equivalent F1 reached 0.400 (from 0.000), conformal coverage exceeded 90% on all four classes, and the ensemble scored all 4,001 edges in the crosswalk graph. The trained model is available on [HuggingFace](https://huggingface.co/rockCO78/ai-security-crosswalk-vfinal)."""))

# --- Cell 1: Plain English ---
nb["cells"].append(make_md("""> **Plain English:** I built a tool that compares security controls across nine AI security standards and decides whether two controls from different frameworks are unrelated, partially related, related, or equivalent. The first version worked well overall (81% accuracy) but could not identify equivalent controls at all---it scored 0% on the class that matters most for compliance mapping.
>
> After discovering OpenCRE, a public database that already links these standards through shared requirements, I tried two ways to add its data to training. The first (disagreement mining) was promising but limited. The second (direct augmentation) caused the large model to collapse to a single prediction and the combiner to memorize the training data perfectly while failing on new examples. Both failures pointed in the same direction: strip the architecture down and remove the learnable combiner.
>
> The final version averages three models trained with loss functions that care about the ordering of the tiers. It gets Equivalent right for the first time. The trained model is on HuggingFace for anyone to use."""))

# --- Cells 2-3: Setup header + description (copy from old cells 2-3) ---
setup_cells = copy_old_cells(old, [2, 3])
nb["cells"].extend(setup_cells)

# --- Cell 4: Setup code (copy from old cell 4, with REPO_ROOT added) ---
old_setup = old["cells"][4]
setup_source = "".join(old_setup["source"])

# Insert REPO_ROOT definition after the REPO line
repo_line_idx = setup_source.find("REPO = ")
if repo_line_idx >= 0:
    repo_line_end = setup_source.find("\n", repo_line_idx)
    if repo_line_end > 0:
        setup_source = (
            setup_source[: repo_line_end + 1]
            + "REPO_ROOT = REPO.parent if REPO.name == \"project1\" else REPO\n"
            + setup_source[repo_line_end + 1 :]
        )

setup_code = make_code(setup_source)
nb["cells"].append(setup_code)

save_notebook(nb)
