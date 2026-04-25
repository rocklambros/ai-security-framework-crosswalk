"""
update_notebook_structure.py

One-shot surgical edits to the project1 EDA notebook:
  1. Assert the notebook has exactly 119 cells (expected pre-edit state).
  2. Change cell 85's heading from the old Conclusion title to the new v7c Assessment title.
  3. Delete cells 114-118 (the thin v_final placeholder section — 5 cells).
  4. Write the modified notebook back in place.

Run from any working directory; paths are resolved relative to this script.
"""

import json
import pathlib
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NB_PATH = REPO_ROOT / "project1" / "COMP_4433_RockLambros_project1_crosswalk_eda.ipynb"

# ---------------------------------------------------------------------------
# Expected / target values
# ---------------------------------------------------------------------------
EXPECTED_CELL_COUNT = 119
TARGET_CELL_COUNT = 114  # after deleting 5 cells

OLD_HEADING = "## 9 · Conclusion: Uncertainty and Takeaways"
NEW_HEADING = "## 9 · v7c Assessment: Uncertainty and Limitations"

HEADING_CELL_IDX = 85       # 0-based index of the heading cell to rename
DELETE_START = 114           # first cell index to delete (inclusive, 0-based)
DELETE_END = 118             # last cell index to delete (inclusive, 0-based)


def load_notebook(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_notebook(nb: dict, path: pathlib.Path) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def get_first_line(source) -> str:
    """Return the first non-empty line of a cell source (list or str)."""
    if isinstance(source, list):
        return source[0].rstrip("\n") if source else ""
    return source.split("\n")[0]


def set_first_line(source, new_line: str):
    """Replace the first line of source with new_line, preserving type."""
    if isinstance(source, list):
        if not source:
            return [new_line]
        rest = source[1:]
        return [new_line] + rest
    lines = source.split("\n")
    lines[0] = new_line
    return "\n".join(lines)


def main() -> None:
    if not NB_PATH.exists():
        print(f"ERROR: notebook not found at {NB_PATH}", file=sys.stderr)
        sys.exit(1)

    nb = load_notebook(NB_PATH)
    cells = nb["cells"]

    # ------------------------------------------------------------------
    # 1. Assert expected pre-edit state
    # ------------------------------------------------------------------
    actual_count = len(cells)
    assert actual_count == EXPECTED_CELL_COUNT, (
        f"Expected {EXPECTED_CELL_COUNT} cells but found {actual_count}. "
        "The notebook may have already been modified."
    )
    print(f"[OK] Cell count assertion passed: {actual_count} cells")

    # Verify heading cell
    heading_first_line = get_first_line(cells[HEADING_CELL_IDX]["source"])
    assert heading_first_line == OLD_HEADING, (
        f"Cell {HEADING_CELL_IDX} first line is:\n  {heading_first_line!r}\n"
        f"Expected:\n  {OLD_HEADING!r}"
    )
    print(f"[OK] Heading assertion passed: cell {HEADING_CELL_IDX} has expected text")

    # Verify delete range starts with v_final heading
    delete_first_line = get_first_line(cells[DELETE_START]["source"])
    assert "v_final" in delete_first_line or "Section 12" in delete_first_line, (
        f"Cell {DELETE_START} does not look like the v_final placeholder. "
        f"First line: {delete_first_line!r}"
    )
    print(f"[OK] Delete-range assertion passed: cell {DELETE_START} is v_final placeholder")

    # ------------------------------------------------------------------
    # 2. Change the heading
    # ------------------------------------------------------------------
    cells[HEADING_CELL_IDX]["source"] = set_first_line(
        cells[HEADING_CELL_IDX]["source"], NEW_HEADING
    )
    print(f"[CHANGED] Cell {HEADING_CELL_IDX} heading → {NEW_HEADING!r}")

    # ------------------------------------------------------------------
    # 3. Delete cells 114–118 (inclusive)
    # ------------------------------------------------------------------
    del cells[DELETE_START : DELETE_END + 1]
    print(f"[DELETED] Cells {DELETE_START}–{DELETE_END} removed ({DELETE_END - DELETE_START + 1} cells)")

    # ------------------------------------------------------------------
    # 4. Verify final state
    # ------------------------------------------------------------------
    new_count = len(nb["cells"])
    assert new_count == TARGET_CELL_COUNT, (
        f"Post-edit cell count is {new_count}, expected {TARGET_CELL_COUNT}"
    )
    print(f"[OK] Post-edit cell count: {new_count}")

    last_cell_src = get_first_line(nb["cells"][-1]["source"])
    print(f"[INFO] Last cell (index {new_count - 1}) first line: {last_cell_src!r}")

    # ------------------------------------------------------------------
    # 5. Write back
    # ------------------------------------------------------------------
    write_notebook(nb, NB_PATH)
    print(f"\n[DONE] Notebook written to: {NB_PATH}")


if __name__ == "__main__":
    main()
