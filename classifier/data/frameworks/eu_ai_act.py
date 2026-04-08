"""EU AI Act (Regulation 2024/1689) HTML → article-level node list ingester.

Source: EUR-Lex CELEX 32024R1689. Articles are the natural granularity.
Parser strategy: walk <p> elements, treat any with class containing "oj-ti-art"
as an article boundary; the next "oj-sti-art" is the title; subsequent
paragraphs until the next "oj-ti-art" are the body.

Note: EUR-Lex uses the "oj-" prefix variant (oj-ti-art / oj-sti-art) rather
than the bare ti-art / sti-art classes referenced in generic EUR-Lex docs.
"""
from __future__ import annotations
import re
from pathlib import Path

from bs4 import BeautifulSoup

ARTICLE_NUM_RE = re.compile(r"Article\s+(\d+[a-z]?)", re.IGNORECASE)


def ingest_eu_ai_act(html_path: Path) -> list[dict]:
    soup = BeautifulSoup(Path(html_path).read_text(encoding="utf-8"), "html.parser")
    paragraphs = soup.find_all("p")

    nodes: list[dict] = []
    current_num: str | None = None
    current_title_parts: list[str] = []
    current_body: list[str] = []

    def flush() -> None:
        nonlocal current_num, current_title_parts, current_body
        if current_num:
            title = " ".join(current_title_parts).strip()
            body = "\n".join(current_body).strip()
            full_title = f"Article {current_num} — {title}" if title else f"Article {current_num}"
            nodes.append({
                "node_id": f"eu_ai_act:Art{current_num}",
                "local_id": f"Art{current_num}",
                "framework": "eu_ai_act",
                "title": full_title,
                "text": body or title,
            })
        current_num = None
        current_title_parts = []
        current_body = []

    for p in paragraphs:
        cls = " ".join(p.get("class", []))
        text = p.get_text(" ", strip=True)
        if "oj-ti-art" in cls:
            flush()
            m = ARTICLE_NUM_RE.search(text)
            if m:
                current_num = m.group(1)
        elif "oj-sti-art" in cls and current_num:
            current_title_parts.append(text)
        elif current_num and text:
            current_body.append(text)
    flush()
    return nodes
