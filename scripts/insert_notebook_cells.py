"""
insert_notebook_cells.py — reusable helper for inserting cells into a notebook.

Usage:
    python scripts/insert_notebook_cells.py <position> <cells.json>

Arguments:
    position    Integer index at which to insert (0-based). Existing cells at
                that index and beyond are shifted right. Use -1 to append.
    cells.json  Path to a JSON file containing an array of cell objects.

Each cell object in cells.json must have at minimum:
    "cell_type"  : "code" | "markdown" | "raw"
    "source"     : str  (will be split on newlines into a list)
                   OR list of str (used as-is)

Optional fields (sensible defaults applied if absent):
    "metadata"        : {}
    "outputs"         : []   (code cells only)
    "execution_count" : null (code cells only)

Example cells.json:
    [
      {
        "cell_type": "markdown",
        "source": "## New Section\\nSome intro text."
      },
      {
        "cell_type": "code",
        "source": ["import pandas as pd\\n", "df = pd.read_csv('data.csv')"]
      }
    ]

The notebook path is resolved via the NOTEBOOK env-var or defaults to:
    <repo_root>/project1/COMP_4433_RockLambros_project1_crosswalk_eda.ipynb
"""

import json
import os
import pathlib
import sys


# ---------------------------------------------------------------------------
# Notebook path resolution
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_NB_PATH = (
    REPO_ROOT / "project1" / "COMP_4433_RockLambros_project1_crosswalk_eda.ipynb"
)


def resolve_nb_path() -> pathlib.Path:
    env_path = os.environ.get("NOTEBOOK")
    if env_path:
        p = pathlib.Path(env_path)
        if not p.is_absolute():
            p = pathlib.Path.cwd() / p
        return p.resolve()
    return DEFAULT_NB_PATH


# ---------------------------------------------------------------------------
# Cell normalisation
# ---------------------------------------------------------------------------

def _source_to_list(source) -> list:
    """
    Convert source to the canonical ipynb list-of-strings format.
    Each line except the last ends with '\\n'.
    """
    if isinstance(source, list):
        # Already a list — return as-is (trust the caller to have correct \\n)
        return source
    # It's a plain string — split and re-add newlines
    lines = source.split("\n")
    result = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            result.append(line + "\n")
        else:
            result.append(line)
    return result


def normalise_cell(raw: dict) -> dict:
    """Apply ipynb defaults to a cell dict from the JSON input."""
    cell_type = raw.get("cell_type", "code")
    source = _source_to_list(raw.get("source", ""))
    metadata = raw.get("metadata", {})

    cell = {
        "cell_type": cell_type,
        "metadata": metadata,
        "source": source,
    }

    if cell_type == "code":
        cell["outputs"] = raw.get("outputs", [])
        cell["execution_count"] = raw.get("execution_count", None)

    return cell


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_notebook(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_notebook(nb: dict, path: pathlib.Path) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def load_new_cells(path: pathlib.Path) -> list:
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, list):
        raise ValueError(f"cells.json must contain a JSON array, got {type(raw)}")
    return [normalise_cell(c) for c in raw]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    try:
        position = int(sys.argv[1])
    except ValueError:
        print(f"ERROR: position must be an integer, got {sys.argv[1]!r}", file=sys.stderr)
        sys.exit(1)

    cells_json_path = pathlib.Path(sys.argv[2])
    if not cells_json_path.is_absolute():
        cells_json_path = pathlib.Path.cwd() / cells_json_path

    nb_path = resolve_nb_path()

    if not nb_path.exists():
        print(f"ERROR: notebook not found at {nb_path}", file=sys.stderr)
        sys.exit(1)

    if not cells_json_path.exists():
        print(f"ERROR: cells file not found at {cells_json_path}", file=sys.stderr)
        sys.exit(1)

    nb = load_notebook(nb_path)
    new_cells = load_new_cells(cells_json_path)
    cells = nb["cells"]

    before_count = len(cells)

    if position == -1 or position >= len(cells):
        # Append to end
        insert_at = len(cells)
    else:
        insert_at = position

    for i, cell in enumerate(new_cells):
        cells.insert(insert_at + i, cell)

    after_count = len(nb["cells"])
    write_notebook(nb, nb_path)

    print(
        f"[DONE] Inserted {len(new_cells)} cell(s) at position {insert_at}. "
        f"Notebook: {before_count} → {after_count} cells."
    )
    print(f"       Notebook path: {nb_path}")


if __name__ == "__main__":
    main()
