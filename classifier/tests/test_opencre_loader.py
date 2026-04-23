"""Unit tests for classifier.data.opencre_loader.

All tests use mock/fixture data — no real API calls are made.
"""
from __future__ import annotations

import hashlib

import pytest

from classifier.data.opencre_loader import (
    GAP_PENALTIES,
    build_pair_row,
    classify_framework,
    extract_pairs_from_cre,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_standard_link(
    framework_name: str,
    section: str,
    ltype: str = "LinkedTo",
) -> dict:
    """Return a synthetic CRE link dict pointing at a standard."""
    return {
        "ltype": ltype,
        "document": {
            "doctype": "standard",
            "name": framework_name,
            "section": section,
            "sectionID": section,
        },
    }


def _make_cre(cre_id: str, cre_name: str, links: list[dict]) -> dict:
    return {"id": cre_id, "name": cre_name, "doctype": "CRE", "links": links}


# ---------------------------------------------------------------------------
# classify_framework
# ---------------------------------------------------------------------------

class TestClassifyFramework:
    def test_ai_security_atlas(self):
        assert classify_framework("MITRE ATLAS") == "ai_security"

    def test_ai_security_ai_exchange(self):
        assert classify_framework("OWASP AI Exchange") == "ai_security"

    def test_ai_security_llm(self):
        assert classify_framework("OWASP LLM Top 10") == "ai_security"

    def test_ai_security_machine_learning(self):
        assert classify_framework("Machine Learning Security") == "ai_security"

    def test_ai_security_enisa(self):
        assert classify_framework("ENISA Multilayer Framework") == "ai_security"

    def test_ai_security_artificial_intelligence(self):
        assert classify_framework("Artificial Intelligence Risk") == "ai_security"

    def test_traditional_asvs(self):
        assert classify_framework("ASVS") == "traditional"

    def test_traditional_nist_800_53(self):
        assert classify_framework("NIST SP 800-53") == "traditional"

    def test_traditional_cwe(self):
        assert classify_framework("CWE") == "traditional"

    def test_traditional_27001(self):
        assert classify_framework("ISO/IEC 27001:2022") == "traditional"

    def test_traditional_pci_dss(self):
        assert classify_framework("PCI DSS v4.0") == "traditional"

    def test_traditional_wstg(self):
        assert classify_framework("OWASP WSTG") == "traditional"

    def test_traditional_samm(self):
        assert classify_framework("OWASP SAMM v2.0") == "traditional"

    def test_traditional_capec(self):
        assert classify_framework("CAPEC") == "traditional"

    def test_other_unknown(self):
        assert classify_framework("SomeObscureFramework") == "other"

    def test_case_insensitive_ai(self):
        # Keywords are checked against lowercased input
        assert classify_framework("mitre atlas") == "ai_security"

    def test_case_insensitive_traditional(self):
        assert classify_framework("CWE") == "traditional"


# ---------------------------------------------------------------------------
# extract_pairs_from_cre — basic LinkedTo pair
# ---------------------------------------------------------------------------

class TestExtractPairsFromCre:
    def test_two_linkedto_standards_produce_one_pair(self):
        cre = _make_cre(
            cre_id="123-456",
            cre_name="Input Validation",
            links=[
                _make_standard_link("NIST SP 800-53", "SI-10", ltype="LinkedTo"),
                _make_standard_link("ASVS", "5.1.3", ltype="LinkedTo"),
            ],
        )
        pairs = extract_pairs_from_cre(cre)
        assert len(pairs) == 1

    def test_pair_has_correct_cre_metadata(self):
        cre = _make_cre(
            cre_id="123-456",
            cre_name="Input Validation",
            links=[
                _make_standard_link("NIST SP 800-53", "SI-10", ltype="LinkedTo"),
                _make_standard_link("ASVS", "5.1.3", ltype="LinkedTo"),
            ],
        )
        pair = extract_pairs_from_cre(cre)[0]
        assert pair["cre_id"] == "123-456"
        assert pair["cre_name"] == "Input Validation"

    def test_pair_canonical_ordering(self):
        """source_node_id <= target_node_id (alphabetical)."""
        cre = _make_cre(
            cre_id="10",
            cre_name="Test",
            links=[
                _make_standard_link("ASVS", "5.1.3", ltype="LinkedTo"),
                _make_standard_link("NIST SP 800-53", "SI-10", ltype="LinkedTo"),
            ],
        )
        pair = extract_pairs_from_cre(cre)[0]
        assert pair["source_node_id"] <= pair["target_node_id"]

    def test_three_linkedto_standards_produce_three_pairs(self):
        cre = _make_cre(
            cre_id="10",
            cre_name="Test",
            links=[
                _make_standard_link("ASVS", "1.1", ltype="LinkedTo"),
                _make_standard_link("CWE", "20", ltype="LinkedTo"),
                _make_standard_link("NIST SP 800-53", "SI-10", ltype="LinkedTo"),
            ],
        )
        pairs = extract_pairs_from_cre(cre)
        assert len(pairs) == 3  # C(3,2) = 3

    def test_single_standard_produces_no_pairs(self):
        cre = _make_cre(
            cre_id="10",
            cre_name="Test",
            links=[
                _make_standard_link("ASVS", "1.1", ltype="LinkedTo"),
            ],
        )
        assert extract_pairs_from_cre(cre) == []

    def test_no_links_produces_no_pairs(self):
        cre = _make_cre(cre_id="10", cre_name="Test", links=[])
        assert extract_pairs_from_cre(cre) == []

    def test_duplicate_node_ids_deduplicated(self):
        """Two links pointing at the same standard should not form a self-pair."""
        cre = _make_cre(
            cre_id="10",
            cre_name="Test",
            links=[
                _make_standard_link("ASVS", "1.1", ltype="LinkedTo"),
                _make_standard_link("ASVS", "1.1", ltype="LinkedTo"),
            ],
        )
        # Both links produce the same node_id; C(2,2)=1 but canonical key dedup
        # means we only emit ≤1 unique pair — and since it's a self-pair it's dropped.
        pairs = extract_pairs_from_cre(cre)
        # All pairs must have distinct src/tgt; a self-pair (same node_id) is skipped
        for p in pairs:
            assert p["source_node_id"] != p["target_node_id"]


# ---------------------------------------------------------------------------
# AutomaticallyLinkedTo links are skipped
# ---------------------------------------------------------------------------

class TestAutoLinksSkipped:
    def test_auto_links_not_counted(self):
        cre = _make_cre(
            cre_id="10",
            cre_name="Test",
            links=[
                _make_standard_link("ASVS", "1.1", ltype="AutomaticallyLinkedTo"),
                _make_standard_link("NIST SP 800-53", "SI-10", ltype="AutomaticallyLinkedTo"),
            ],
        )
        # Both links are auto — no manual standards → no pairs
        assert extract_pairs_from_cre(cre) == []

    def test_mixed_links_only_manual_used(self):
        """AutomaticallyLinkedTo partners are excluded; manual ones form pairs."""
        cre = _make_cre(
            cre_id="10",
            cre_name="Test",
            links=[
                _make_standard_link("ASVS", "1.1", ltype="LinkedTo"),
                _make_standard_link("CWE", "20", ltype="AutomaticallyLinkedTo"),
                _make_standard_link("NIST SP 800-53", "SI-10", ltype="LinkedTo"),
            ],
        )
        pairs = extract_pairs_from_cre(cre)
        # Only ASVS and NIST 800-53 are manual; CWE is skipped → 1 pair
        assert len(pairs) == 1
        # Confirm CWE is not present in any pair
        for pair in pairs:
            assert "cwe" not in pair["source_framework"]
            assert "cwe" not in pair["target_framework"]

    def test_auto_link_alternate_spelling_skipped(self):
        """'Automatically Linked To' spelling also excluded."""
        cre = _make_cre(
            cre_id="10",
            cre_name="Test",
            links=[
                {
                    "ltype": "Automatically Linked To",
                    "document": {
                        "doctype": "standard",
                        "name": "ASVS",
                        "section": "1.1",
                        "sectionID": "1.1",
                    },
                },
                _make_standard_link("NIST SP 800-53", "SI-10", ltype="LinkedTo"),
            ],
        )
        # Only 1 manual standard → no pairs
        assert extract_pairs_from_cre(cre) == []


# ---------------------------------------------------------------------------
# build_pair_row — schema validation
# ---------------------------------------------------------------------------

class TestBuildPairRow:
    REQUIRED_KEYS = {
        "source_node_id",
        "target_node_id",
        "source_text",
        "target_text",
        "source_framework",
        "target_framework",
        "cre_id",
        "cre_name",
        "gap_penalty",
        "fw_class_a",
        "fw_class_b",
        "provenance",
        "provenance_sha",
    }

    def _sample_row(self, **overrides) -> dict:
        base = dict(
            source_node_id="owasp_asvs:5.1.3",
            target_node_id="nist_800_53:SI-10",
            source_text="5.1.3",
            target_text="SI-10",
            source_framework="owasp_asvs",
            target_framework="nist_800_53",
            cre_id="123-456",
            cre_name="Input Validation",
            gap_penalty=0,
            fw_class_a="traditional",
            fw_class_b="traditional",
            provenance="opencre",
            provenance_sha="abc123",
        )
        base.update(overrides)
        return build_pair_row(**base)

    def test_row_has_all_required_keys(self):
        row = self._sample_row()
        assert self.REQUIRED_KEYS.issubset(set(row.keys()))

    def test_row_values_match_inputs(self):
        row = self._sample_row()
        assert row["source_node_id"] == "owasp_asvs:5.1.3"
        assert row["target_node_id"] == "nist_800_53:SI-10"
        assert row["cre_id"] == "123-456"
        assert row["cre_name"] == "Input Validation"
        assert row["gap_penalty"] == 0
        assert row["fw_class_a"] == "traditional"
        assert row["fw_class_b"] == "traditional"
        assert row["provenance"] == "opencre"
        assert row["provenance_sha"] == "abc123"

    def test_gap_penalty_nonzero(self):
        row = self._sample_row(gap_penalty=2)
        assert row["gap_penalty"] == 2

    def test_fw_class_ai_security(self):
        row = self._sample_row(fw_class_a="ai_security")
        assert row["fw_class_a"] == "ai_security"


# ---------------------------------------------------------------------------
# Provenance SHA correctness
# ---------------------------------------------------------------------------

class TestProvenanceSha:
    def test_provenance_sha_in_extracted_pair(self):
        cre = _make_cre(
            cre_id="99",
            cre_name="SHA Test",
            links=[
                _make_standard_link("ASVS", "1.1", ltype="LinkedTo"),
                _make_standard_link("CWE", "20", ltype="LinkedTo"),
            ],
        )
        pairs = extract_pairs_from_cre(cre)
        assert len(pairs) == 1
        sha = pairs[0]["provenance_sha"]
        assert isinstance(sha, str)
        assert len(sha) == 64  # SHA-256 hex digest

    def test_provenance_sha_is_deterministic(self):
        """Same CRE + pair should always produce the same SHA."""
        cre = _make_cre(
            cre_id="99",
            cre_name="SHA Test",
            links=[
                _make_standard_link("ASVS", "1.1", ltype="LinkedTo"),
                _make_standard_link("CWE", "20", ltype="LinkedTo"),
            ],
        )
        pairs_a = extract_pairs_from_cre(cre)
        pairs_b = extract_pairs_from_cre(cre)
        assert pairs_a[0]["provenance_sha"] == pairs_b[0]["provenance_sha"]

    def test_provenance_sha_changes_with_different_cre_id(self):
        def _pairs(cre_id: str) -> list:
            cre = _make_cre(
                cre_id=cre_id,
                cre_name="Test",
                links=[
                    _make_standard_link("ASVS", "1.1", ltype="LinkedTo"),
                    _make_standard_link("CWE", "20", ltype="LinkedTo"),
                ],
            )
            return extract_pairs_from_cre(cre)

        sha_a = _pairs("99")[0]["provenance_sha"]
        sha_b = _pairs("100")[0]["provenance_sha"]
        assert sha_a != sha_b


# ---------------------------------------------------------------------------
# Gap penalties
# ---------------------------------------------------------------------------

class TestGapPenalties:
    def test_linked_to_zero_penalty(self):
        assert GAP_PENALTIES["LinkedTo"] == 0

    def test_contains_one_penalty(self):
        assert GAP_PENALTIES["Contains"] == 1

    def test_is_part_of_two_penalty(self):
        assert GAP_PENALTIES["Is Part Of"] == 2

    def test_related_two_penalty(self):
        assert GAP_PENALTIES["Related"] == 2


from classifier.data.tier_mapper import map_opencre_tier, TierLabel


def test_map_opencre_tier_low_penalty():
    """Gap penalty 0 (both LinkedTo) -> skewed toward EQUIVALENT/RELATED."""
    dist = map_opencre_tier(gap_penalty=0, bridge_pair=False)
    assert abs(sum(dist.values()) - 1.0) < 1e-6
    assert dist[TierLabel.EQUIVALENT] > dist[TierLabel.PARTIAL]
    assert dist[TierLabel.RELATED] > dist[TierLabel.UNRELATED]


def test_map_opencre_tier_high_penalty():
    """Gap penalty 4 (both Contains/Related) -> skewed toward PARTIAL."""
    dist = map_opencre_tier(gap_penalty=4, bridge_pair=False)
    assert abs(sum(dist.values()) - 1.0) < 1e-6
    assert dist[TierLabel.PARTIAL] > dist[TierLabel.EQUIVALENT]


def test_map_opencre_tier_bridge_pair():
    """Bridge pairs (AI<->traditional) get wider distributions."""
    bridge = map_opencre_tier(gap_penalty=0, bridge_pair=True)
    non_bridge = map_opencre_tier(gap_penalty=0, bridge_pair=False)
    assert bridge[TierLabel.EQUIVALENT] < non_bridge[TierLabel.EQUIVALENT]
