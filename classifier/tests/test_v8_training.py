"""Tests for v8 training data assembly and contamination."""
import pytest
from classifier.data.contamination import check_cre_bridge_contamination


def test_cre_bridge_contamination_detects_shared_cre():
    """If A and B share a CRE, and B is in the frozen test, A is contaminated."""
    opencre_pairs = [
        {"source_node_id": "asvs:V1.1", "target_node_id": "cwe:287", "cre_id": "100-100", "provenance_sha": "sha1"},
        {"source_node_id": "asvs:V1.1", "target_node_id": "nist_800_53:AC-1", "cre_id": "100-100", "provenance_sha": "sha2"},
        {"source_node_id": "cwe:287", "target_node_id": "nist_800_53:AC-1", "cre_id": "100-100", "provenance_sha": "sha3"},
    ]
    frozen_node_ids = {"cwe:287", "owasp_llm:LLM01"}

    contaminated = check_cre_bridge_contamination(opencre_pairs, frozen_node_ids)
    # Pairs that directly touch cwe:287 are contaminated
    # sha1 touches cwe:287, sha3 touches cwe:287
    assert "sha1" in contaminated
    assert "sha3" in contaminated


def test_cre_bridge_clean_pair():
    opencre_pairs = [
        {"source_node_id": "mitre_atlas:T001", "target_node_id": "nist_rmf:GOV-1", "cre_id": "200-200", "provenance_sha": "clean1"},
    ]
    frozen_node_ids = {"cwe:287", "owasp_llm:LLM01"}

    contaminated = check_cre_bridge_contamination(opencre_pairs, frozen_node_ids)
    assert len(contaminated) == 0
