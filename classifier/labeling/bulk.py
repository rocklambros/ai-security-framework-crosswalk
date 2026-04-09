from __future__ import annotations
from typing import Callable
from .client import LabelerClient
from .prompts import render_prompt, prompt_sha
from .schemas import GapTuple, LLMSMELabel


def label_gap_tuples(
    gaps: list[GapTuple],
    text_lookup: Callable[[str, str], str],
    client: LabelerClient,
) -> list[LLMSMELabel]:
    """text_lookup(framework, node_id) -> text body (from nodes.json)."""
    out: list[LLMSMELabel] = []
    for g in gaps:
        ctx = {
            "source_framework": g.source_framework,
            "source_id": g.source_id,
            "source_text": text_lookup(g.source_framework, g.source_id),
            "target_framework": g.target_framework,
            "target_node_id": g.target_node_id,
            "target_text": text_lookup(g.target_framework, g.target_node_id.split(":", 1)[-1]),
        }
        system, user = render_prompt(ctx)
        sha = prompt_sha(system, user)
        resp = client.label(system, user)
        out.append(
            LLMSMELabel(
                source_framework=g.source_framework,
                source_id=g.source_id,
                target_framework=g.target_framework,
                target_node_id=g.target_node_id,
                relation=resp["relation"],
                confidence=float(resp["confidence"]),
                rationale=resp["rationale"],
                prompt_sha=sha,
                model_version=client.model,
            )
        )
    return out
