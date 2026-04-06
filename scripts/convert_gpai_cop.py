#!/usr/bin/env python3
"""
Convert EU GPAI Code of Practice PDFs to clean markdown.

Reads each PDF, extracts text with structure preservation via font-size
heading detection, and writes one .md per chapter plus a combined file.
"""

import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: pymupdf not installed. Run: pip install pymupdf")
    raise

SRC_DIR = Path("data/frameworks/eu-gpai-code-of-practice")
PDFS = sorted(SRC_DIR.glob("*.pdf"))

if not PDFS:
    print(f"ERROR: No PDF files found in {SRC_DIR}")
    print("Place the 3 Code of Practice chapter PDFs there and re-run.")
    exit(1)

print(f"Found {len(PDFS)} PDF file(s):")
for p in PDFS:
    print(f"  {p.name} ({p.stat().st_size:,} bytes)")

# Chapter classification by filename (reliable since filenames are known)
CHAPTER_MAP = {
    "transparency": "transparency",
    "copyright": "copyright",
    "safety": "safety_and_security",
}


def classify_by_filename(name):
    """Classify chapter from PDF filename."""
    name_lower = name.lower()
    for keyword, chapter in CHAPTER_MAP.items():
        if keyword in name_lower:
            return chapter
    return "unknown"


def extract_lines(pdf_path):
    """Extract text lines from PDF with font metadata."""
    doc = fitz.open(pdf_path)
    all_lines = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", sort=True)["blocks"]

        for block in blocks:
            if block["type"] != 0:  # skip images
                continue
            for line in block["lines"]:
                text = ""
                max_size = 0
                is_bold = False
                for span in line["spans"]:
                    text += span["text"]
                    max_size = max(max_size, span["size"])
                    if "bold" in span["font"].lower() or "Bold" in span["font"]:
                        is_bold = True

                text = text.strip()
                if not text:
                    continue

                all_lines.append({
                    "text": text,
                    "size": max_size,
                    "bold": is_bold,
                    "page": page_num + 1,
                })

    doc.close()
    return all_lines


def lines_to_markdown(lines):
    """Convert extracted lines to markdown using font-size heading detection.

    Heading hierarchy (based on inspected font sizes):
      36pt bold  -> skip (repeated title on every PDF)
      26pt bold  -> # Chapter title
      20-24pt bold -> ## Section (Commitment N, Objectives, Recitals, Glossary, Appendix)
      12pt bold + starts with "Measure" -> ### Measure
      12pt bold (other) -> skip (author names on cover page)
      11pt bold  -> **bold inline** (principles, LEGAL TEXT, etc.)
      11pt regular -> body text
      <10pt -> footnotes (include but mark small)
    """
    md_lines = []
    prev_was_heading = False

    for line in lines:
        text = line["text"]
        size = line["size"]
        bold = line["bold"]

        # Skip standalone page numbers
        if re.match(r"^\d{1,3}$", text.strip()):
            continue

        # Title line (36pt) - skip repeated title
        if size >= 30:
            continue

        # Chapter heading (26pt only)
        if size >= 25 and bold:
            md_lines.append(f"\n# {text}\n")
            prev_was_heading = True
            continue

        # Major section heading (20-24pt) - Commitments, Objectives, Recitals, etc.
        if size >= 16 and bold:
            md_lines.append(f"\n## {text}\n")
            prev_was_heading = True
            continue

        # Measure headings (12pt bold, starts with "Measure")
        if bold and size >= 11.5 and re.match(r"Measure\s+\d", text):
            md_lines.append(f"\n### {text}\n")
            prev_was_heading = True
            continue

        # 12pt bold but NOT a Measure - could be cover page names or subsection
        # Check if it looks like a sub-heading (short, not a sentence)
        if bold and size >= 11.5 and size < 18:
            # Skip author names on cover (page 1 names)
            if line["page"] == 1:
                continue
            # Short bold text that's not a sentence -> bold paragraph
            if len(text) < 150:
                md_lines.append(f"\n**{text}**\n")
                prev_was_heading = False
                continue

        # Footnotes (small text)
        if size < 9:
            # Skip tiny superscript numbers
            if re.match(r"^\d{1,2}$", text):
                continue
            md_lines.append(text)
            prev_was_heading = False
            continue

        # Bold body text (11pt bold)
        if bold and size >= 10:
            md_lines.append(f"**{text}**")
            prev_was_heading = False
            continue

        # Regular body text
        md_lines.append(text)
        prev_was_heading = False

    # Join lines
    md = "\n".join(md_lines)

    # Fix broken lines: join lines that end mid-sentence
    # (lowercase/comma at end of line, lowercase start of next)
    md = re.sub(r"(?<=[a-z,;:\-])\n(?=[a-z(])", " ", md)

    # Fix hyphenated line breaks
    md = re.sub(r"(\w)-\n(\w)", r"\1\2", md)

    # Collapse excessive blank lines
    md = re.sub(r"\n{4,}", "\n\n\n", md)

    # Clean up spacing around headings
    md = re.sub(r"\n{3,}(#+)", r"\n\n\1", md)

    return md.strip()


def post_process(md, chapter):
    """Chapter-specific post-processing."""
    # For multi-line headings like "Commitment 10 Additional documentation and\ntransparency"
    # Merge continuation lines into the heading
    md = re.sub(
        r"(## Commitment \d+[^\n]*)\n\n(## )([a-z][^\n]*)",
        r"\1 \3",
        md,
    )

    # Ensure Commitment headings that weren't caught by font detection get tagged
    # (safety net - shouldn't be needed if font detection works)
    md = re.sub(
        r"(?<!\#)\n(Commitment\s+\d+\s+[A-Z][^\n]+)\n",
        r"\n## \1\n",
        md,
    )

    return md


# Process each PDF
chapter_outputs = {}

for pdf_path in PDFS:
    print(f"\nProcessing: {pdf_path.name}")

    chapter = classify_by_filename(pdf_path.name)
    print(f"  Chapter: {chapter}")

    lines = extract_lines(pdf_path)
    print(f"  Lines extracted: {len(lines)}")

    md = lines_to_markdown(lines)
    md = post_process(md, chapter)

    # Add metadata header
    header = f"""---
title: "EU GPAI Code of Practice - {chapter.replace('_', ' ').title()}"
source: "https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai"
chapter: "{chapter}"
retrieved: "2026-04-05"
license: "European Commission - Public"
---

"""
    md = header + md

    # Write individual chapter file
    out_name = f"gpai_cop_{chapter}.md"
    out_path = SRC_DIR / out_name
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    size = out_path.stat().st_size
    print(f"  Wrote {out_name} ({size:,} bytes)")

    chapter_outputs[chapter] = md

# Write combined file
combined_path = SRC_DIR / "gpai_code_of_practice_combined.md"
with open(combined_path, "w", encoding="utf-8") as f:
    f.write("# EU GPAI Code of Practice - Combined\n\n")
    f.write("Source: https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai\n")
    f.write("Retrieved: 2026-04-05\n")
    f.write("License: European Commission - Public\n\n")
    f.write("---\n\n")

    for chapter_key in ["transparency", "copyright", "safety_and_security"]:
        if chapter_key in chapter_outputs:
            f.write(f"\n\n{'='*60}\n\n")
            f.write(chapter_outputs[chapter_key])
        else:
            f.write(f"\n\n<!-- Chapter '{chapter_key}' not found in PDFs -->\n\n")

combined_size = combined_path.stat().st_size
print(f"\nWrote combined file ({combined_size:,} bytes)")

# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"PDFs processed: {len(PDFS)}")
for ch, md in chapter_outputs.items():
    commitments = len(re.findall(r"^## Commitment", md, re.MULTILINE))
    measures = len(re.findall(r"^### Measure", md, re.MULTILINE))
    print(f"  {ch}: {commitments} commitments, {measures} measures, ~{len(md):,} chars")
