"""Build the redesigned notebook from scratch.

Each section-building task will import helpers from this module
and append cells to the notebook.
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).parent / "COMP_4433_RockLambros_project1_crosswalk_eda.ipynb"
OLD_NB_PATH = Path(__file__).parent / "COMP_4433_RockLambros_project1_crosswalk_eda.ipynb.bak"


def make_md(source: str) -> dict:
    lines = source.split("\n")
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [l + "\n" for l in lines[:-1]] + [lines[-1]] if lines else [],
    }


def make_code(source: str) -> dict:
    lines = source.split("\n")
    return {
        "cell_type": "code",
        "metadata": {},
        "source": [l + "\n" for l in lines[:-1]] + [lines[-1]] if lines else [],
        "outputs": [],
        "execution_count": None,
    }


def load_old_notebook() -> dict:
    return json.loads(OLD_NB_PATH.read_text())


def load_notebook() -> dict:
    if NB_PATH.exists():
        return json.loads(NB_PATH.read_text())
    return {
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


def save_notebook(nb: dict) -> None:
    NB_PATH.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    print(f"Saved {len(nb['cells'])} cells to {NB_PATH}")


def copy_old_cells(old_nb: dict, indices: list) -> list:
    cells = []
    for i in indices:
        cell = json.loads(json.dumps(old_nb["cells"][i]))
        cell["outputs"] = []
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
        cells.append(cell)
    return cells
