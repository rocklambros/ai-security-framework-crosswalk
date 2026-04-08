"""
OWASP GenAI Data Security Risks and Mitigations (DSGAI) ingester.

Source provenance
-----------------
The PDF was extracted with ``pdftotext -layout`` to produce a layout-preserving
plain-text file.  This preserves the original page geometry, which means:

  1. Each entry header appears on a line that begins with a form-feed character
     (``\x0c``) directly followed by ``DSGAI##``.  The Table of Contents (TOC)
     lines, by contrast, have leading spaces.  Using ``^\x0cDSGAI`` as the
     anchor therefore filters out the TOC entries without any line-number
     arithmetic.

  2. Seven titles wrap onto the continuation line because the title text was
     wider than the PDF column.  The continuation line is always the immediate
     next line in the file (no blank line between), is ≤ 20 stripped characters
     long, does not start with ``DSGAI``, and is not a section heading (those
     are ≥ 22 chars).  These continuation lines are concatenated to produce the
     full title string.

     Wrapped entries:
       DSGAI07 — …for AI Systems
       DSGAI09 — …Cross-Channel Data Leakage
       DSGAI10 — …Transformation Pitfalls
       DSGAI12 — …(LLM-to-SQL/Graph)
       DSGAI15 — …Prompt Over-Sharing
       DSGAI17 — …Failures in AI Pipelines
       DSGAI21 — …via Data Poisoning

Usage
-----
    from pathlib import Path
    from classifier.data.frameworks.dsgai import ingest_dsgai

    nodes = ingest_dsgai(Path("data/frameworks/owasp-dsgai/OWASP-GenAI-Data-Security-Risks-and-Mitigations-2026-v1.0.txt"))
"""

from __future__ import annotations

import re
from pathlib import Path


# Matches the start of a body entry: form-feed then DSGAI##  — <title text>
# The form-feed is produced by pdftotext at every page break and appears
# immediately before the entry header (which starts at the left margin).
_ENTRY_RE = re.compile(
    r"^\x0cDSGAI(\d{2}) \u2014 (.+)$",
    re.MULTILINE,
)

# Maximum stripped length of a legitimate title-continuation line.
# Observed continuation lines are 7–13 chars; section headings start at 22.
_MAX_CONTINUATION_LEN = 20


def _is_continuation(line: str) -> bool:
    """Return True when *line* looks like a wrapped title continuation."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("DSGAI"):
        return False
    return len(stripped) <= _MAX_CONTINUATION_LEN


def ingest_dsgai(txt_path: Path) -> list[dict]:
    """Parse the pdftotext -layout extraction and return 21 node dicts.

    Parameters
    ----------
    txt_path:
        Path to the layout-extracted plain-text file.

    Returns
    -------
    list of dicts, each with keys:
        ``node_id``   – ``owasp_dsgai:DSGAI##``
        ``local_id``  – ``DSGAI##``
        ``framework`` – ``owasp_dsgai``
        ``title``     – full rejoined title string (stripped)
        ``text``      – body text between this entry and the next (stripped)

    Raises
    ------
    ValueError
        If the parsed result is not exactly 21 entries with IDs DSGAI01–DSGAI21.
    """
    text = txt_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    matches = list(_ENTRY_RE.finditer(text))

    # Build a line-number lookup: character offset -> 1-based line number.
    # We need this to locate the continuation line index.
    def _lineno(offset: int) -> int:
        return text.count("\n", 0, offset) + 1

    nodes: list[dict] = []

    for idx, m in enumerate(matches):
        num = m.group(1)
        raw_title = m.group(2).rstrip()

        # Check for wrapped title: inspect the line immediately after the
        # header line in the *lines* array.
        header_line_idx = _lineno(m.start()) - 1  # 0-based index into lines[]
        # The form-feed is part of this line, so the next line is header_line_idx + 1
        next_line_idx = header_line_idx + 1
        if next_line_idx < len(lines) and _is_continuation(lines[next_line_idx]):
            continuation = lines[next_line_idx].strip()
            # Join: if the raw title ends with a hyphen (word-break), join
            # directly; otherwise add a space.
            if raw_title.endswith("-"):
                full_title = raw_title + continuation
            else:
                full_title = raw_title + " " + continuation
        else:
            full_title = raw_title

        # Body text runs from end of this match to start of the next (or EOF).
        body_start = m.end()
        body_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()

        nodes.append(
            {
                "node_id": f"owasp_dsgai:DSGAI{num}",
                "local_id": f"DSGAI{num}",
                "framework": "owasp_dsgai",
                "title": full_title.strip(),
                "text": body,
            }
        )

    # Validate
    if len(nodes) != 21:
        raise ValueError(
            f"Expected 21 DSGAI entries, found {len(nodes)}.  "
            "Check the source file."
        )

    expected_ids = [f"DSGAI{i:02d}" for i in range(1, 22)]
    actual_ids = [n["local_id"] for n in nodes]
    if actual_ids != expected_ids:
        raise ValueError(
            f"Entry IDs do not match expected DSGAI01–DSGAI21.\n"
            f"Got: {actual_ids}"
        )

    return nodes
