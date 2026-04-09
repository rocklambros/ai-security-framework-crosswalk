"""Unit + integration tests for upstream id canonicalization."""
import json
from collections import defaultdict
from pathlib import Path

import pytest

from classifier.data.upstream_id_normalize import (
    canonicalize,
    canonicalize_aiuc_1,
    canonicalize_eu_ai_act,
    canonicalize_identity,
    canonicalize_nist_rmf,
)
from classifier.data.candidates import FRAMEWORK_PAIRS, FRAMEWORKS

REPO = Path(__file__).resolve().parents[2]
NODES = REPO / "data" / "processed" / "nodes.json"
MAPPINGS = REPO / "data" / "upstream" / "mappings_v1.jsonl"


@pytest.fixture(scope="module")
def nodes_by_id() -> set[str]:
    return {n["node_id"] for n in json.loads(NODES.read_text())}


# --- unit tests ---

def test_eu_ai_act_extracts_article_from_control_name():
    assert canonicalize_eu_ai_act("any text", "Art. 9 — Risk management") == "Art9"
    assert canonicalize_eu_ai_act("any text", "Art. 15 — Accuracy") == "Art15"
    assert canonicalize_eu_ai_act("any text", "Art. 53(1)(a) — GPAI") == "Art53"
    assert canonicalize_eu_ai_act("any text", "no match") is None
    assert canonicalize_eu_ai_act(None, None) is None


def test_nist_rmf_expands_prefixes():
    assert canonicalize_nist_rmf("GV-1.6") == "GOVERN-1.6"
    assert canonicalize_nist_rmf("MP-2.3") == "MAP-2.3"
    assert canonicalize_nist_rmf("MS-2.5") == "MEASURE-2.5"
    assert canonicalize_nist_rmf("MG-2.4") == "MANAGE-2.4"
    # already-expanded passes through
    assert canonicalize_nist_rmf("GOVERN-1.1") == "GOVERN-1.1"
    assert canonicalize_nist_rmf(None) is None


def test_aiuc_1_domain_letters_and_controls():
    assert canonicalize_aiuc_1("A") == "domain_A"
    assert canonicalize_aiuc_1("F") == "domain_F"
    assert canonicalize_aiuc_1("B005") == "B005"
    assert canonicalize_aiuc_1("A001.1") == "A001.1"
    assert canonicalize_aiuc_1("DSGAI01, DSGAI04") is None
    assert canonicalize_aiuc_1("2026-03-27") is None
    assert canonicalize_aiuc_1("Primary DSGAI entries") is None
    assert canonicalize_aiuc_1(None) is None


def test_identity_passthrough():
    assert canonicalize_identity("AML.T0020") == "AML.T0020"
    assert canonicalize_identity("LLM01") == "LLM01"
    assert canonicalize_identity(None) is None


def test_canonicalize_dispatch_membership(nodes_by_id):
    # eu_ai_act: canonicalization works but nodes live under eu_gpai_cop in the graph,
    # so membership check correctly returns False. Unit test covers the extraction.
    nid, ok = canonicalize("eu_ai_act", "long desc", nodes_by_id, "Art. 9 — Risk management")
    assert not ok and nid is None
    # nist_rmf
    nid, ok = canonicalize("nist_rmf", "GV-1.6", nodes_by_id, None)
    assert ok and nid == "nist_rmf:GOVERN-1.6"
    # aiuc_1 domain letter
    nid, ok = canonicalize("aiuc_1", "A", nodes_by_id, None)
    assert ok and nid == "aiuc_1:domain_A"
    # csa_aicm corpus-absent
    nid, ok = canonicalize("csa_aicm", "L1", nodes_by_id, None)
    assert not ok and nid is None
    # mitre identity — not present → None
    nid, ok = canonicalize("mitre_atlas", "AML.T0027", nodes_by_id, None)
    assert not ok and nid is None
    # mitre identity — present → resolved
    nid, ok = canonicalize("mitre_atlas", "AML.T0020", nodes_by_id, None)
    assert ok and nid == "mitre_atlas:AML.T0020"


# --- integration ---

def test_in_scope_resolution_rate_category_a(nodes_by_id):
    """Category A target frameworks must achieve >= 0.88 resolution.

    nist_rmf/eu_ai_act hit 1.00 (full format-mismatch fix).
    aiuc_1 hits ~0.89 because ~11% of rows are upstream junk (date headers,
    comma-separated DSGAI lists) — those are legitimately unresolvable.
    mitre_atlas hits ~0.97 (two AML.T techniques missing from the snapshot).
    """
    mappings = [json.loads(l) for l in open(MAPPINGS)]
    fw_set = set(FRAMEWORKS); pair_set = set(FRAMEWORK_PAIRS)
    in_scope = [
        r for r in mappings
        if r["source_framework"] in fw_set and r["target_framework"] in fw_set
        and (r["source_framework"], r["target_framework"]) in pair_set
    ]
    rates = defaultdict(lambda: [0, 0])
    for r in in_scope:
        rates[r["target_framework"]][0] += 1
        if not r["target_id_unresolved"]:
            rates[r["target_framework"]][1] += 1

    cat_a = ("eu_ai_act", "nist_rmf", "aiuc_1", "mitre_atlas")
    for fw in cat_a:
        tot, res = rates[fw]
        assert tot > 0, f"{fw}: no in-scope rows"
        assert res / tot >= 0.88, f"{fw}: resolution rate {res}/{tot}={res/tot:.3f} < 0.88"

    # Category B stays unresolved
    assert rates["csa_aicm"][1] == 0, "csa_aicm should be 0 (Category B, L1-L7 not in corpus)"


def test_canonicalization_is_injective_per_framework(nodes_by_id):
    """No two distinct raw strings within one framework collapse to the same node_id."""
    mappings = [json.loads(l) for l in open(MAPPINGS)]
    per_fw_raw_to_nid = defaultdict(lambda: defaultdict(set))
    for r in mappings:
        if r.get("target_id_unresolved") or not r.get("target_node_id"):
            continue
        fw = r["target_framework"]
        per_fw_raw_to_nid[fw][r["target_node_id"]].add(r["target_control_id"])

    # Known aliases: for eu_ai_act multiple description strings share the same
    # article — that's intentional. For others we assert near-injectivity.
    for fw, nid_map in per_fw_raw_to_nid.items():
        if fw == "eu_ai_act":
            continue  # many-to-one by design (description → article)
        for nid, raws in nid_map.items():
            # NIST: GV-1.6 and GOVERN-1.6 are legitimate aliases; we merge them.
            # ATLAS: AML.T0022→AML.T0012, AML.T0032→AML.T0020 are version renames.
            if fw in ("nist_rmf", "mitre_atlas") and len(raws) <= 2:
                continue
            assert len(raws) == 1, (
                f"{fw}: raw values {raws} collapse to {nid} (not injective)"
            )
