"""Build Sections 3-4: Dataset Overview + Framework Landscape.

Copies cells 6-33 from the old notebook verbatim. These 28 cells
already contain proper figure citations, active titles, on-plot
annotations, and Plain English blockquotes.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_notebook import load_notebook, save_notebook, load_old_notebook, copy_old_cells

nb = load_notebook()
old = load_old_notebook()

cells = copy_old_cells(old, list(range(6, 34)))
nb["cells"].extend(cells)

save_notebook(nb)
