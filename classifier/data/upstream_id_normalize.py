"""Canonicalize upstream target_control_id strings to nodes.json node_ids.

Per-framework rules derived from the Plan 1-C investigation. Each canonicalizer
is pure and total: given the raw upstream string (and, where needed, the raw
control_name), it returns the local_id portion of a nodes.json node_id
(without the `{framework}:` prefix) or None if the row cannot be resolved.

Category A frameworks (format mismatch, fixable here):
  - eu_ai_act: upstream puts the obligation text in control_id; the article
    reference lives in control_name as 'Art. N — Title'. We extract ArtN.
  - nist_rmf:  upstream abbreviates function prefixes (GV/MP/MS/MG);
    nodes.json spells them out (GOVERN/MAP/MEASURE/MANAGE).
  - aiuc_1:    single-letter A..F refer to domains (nodes use domain_A..F);
    B001..B009 are already valid control ids.

Category B frameworks (corpus-absent, canonicalizer returns None):
  - csa_aicm:    upstream uses tier designators L1..L7 which do not map to
                 any control id in the csa_aicm corpus.

mitre_atlas ID aliases (GenAI-Data-Security-Initiative uses older ATLAS IDs):
  - AML.T0022 -> AML.T0012 (Valid Accounts — renumbered)
  - AML.T0032 -> AML.T0020 (Data Poisoning -> Poison Training Data)
  - AML.T0027, AML.T0030, AML.T0045: absent from current ATLAS snapshot,
    no clear alias. These 6 rows (3 unique IDs) stay unresolved.
"""
from __future__ import annotations
import re
from typing import Optional

_NIST_RMF_PREFIX = {
    "GV": "GOVERN",
    "MP": "MAP",
    "MS": "MEASURE",
    "MG": "MANAGE",
}

_EU_AI_ACT_ART_RE = re.compile(r"^\s*Art\.?\s*(\d+)")
_NIST_RMF_RE = re.compile(r"^(GV|MP|MS|MG)-(.+)$")
_AIUC_DOMAIN_RE = re.compile(r"^[A-F]$")
_AIUC_CONTROL_RE = re.compile(r"^[A-F]\d{3}(?:\.\d+)?$")

# MITRE ATLAS ID aliases — GenAI-Data-Security-Initiative uses older IDs
_ATLAS_ALIASES: dict[str, str] = {
    "AML.T0022": "AML.T0012",  # Valid Accounts (renumbered)
    "AML.T0032": "AML.T0020",  # Data Poisoning -> Poison Training Data
}


def canonicalize_eu_ai_act(raw_control_id: Optional[str], raw_control_name: Optional[str]) -> Optional[str]:
    """Extract ArtN from control_name='Art. N — ...'. Ignore the description in control_id."""
    if not raw_control_name:
        return None
    m = _EU_AI_ACT_ART_RE.match(raw_control_name)
    if not m:
        return None
    return f"Art{int(m.group(1))}"


def canonicalize_nist_rmf(raw: Optional[str]) -> Optional[str]:
    """GV-1.6 -> GOVERN-1.6, etc. Pass through already-expanded ids."""
    if not raw:
        return None
    s = raw.strip()
    m = _NIST_RMF_RE.match(s)
    if m:
        return f"{_NIST_RMF_PREFIX[m.group(1)]}-{m.group(2)}"
    # already-expanded form (GOVERN-1.6) — pass through
    return s


def canonicalize_aiuc_1(raw: Optional[str]) -> Optional[str]:
    """A..F -> domain_A..domain_F; B001..B009 pass through; everything else None."""
    if not raw:
        return None
    s = raw.strip()
    if _AIUC_DOMAIN_RE.match(s):
        return f"domain_{s}"
    if _AIUC_CONTROL_RE.match(s):
        return s
    return None


def canonicalize_mitre_atlas(raw: Optional[str]) -> Optional[str]:
    """Apply ATLAS ID aliases, then identity passthrough."""
    if not raw:
        return None
    s = raw.strip()
    return _ATLAS_ALIASES.get(s, s)


def canonicalize_identity(raw: Optional[str]) -> Optional[str]:
    """For frameworks whose upstream ids already match nodes.json."""
    if not raw:
        return None
    return raw.strip()


def canonicalize_corpus_absent(raw: Optional[str]) -> Optional[str]:
    """Category B: the target framework's corpus does not contain the upstream id scheme."""
    return None


def canonicalize(
    target_framework: str,
    raw_control_id: Optional[str],
    nodes_by_id: set[str],
    raw_control_name: Optional[str] = None,
) -> tuple[Optional[str], bool]:
    """Dispatch by framework, canonicalize, verify membership.

    Returns (target_node_id_or_None, resolved_bool). target_node_id is the
    full 'fw:local_id' string when resolved, None otherwise.
    """
    if target_framework == "eu_ai_act":
        local = canonicalize_eu_ai_act(raw_control_id, raw_control_name)
    elif target_framework == "nist_rmf":
        local = canonicalize_nist_rmf(raw_control_id)
    elif target_framework == "aiuc_1":
        local = canonicalize_aiuc_1(raw_control_id)
    elif target_framework == "csa_aicm":
        local = canonicalize_corpus_absent(raw_control_id)
    elif target_framework == "mitre_atlas":
        local = canonicalize_mitre_atlas(raw_control_id)
    else:
        local = canonicalize_identity(raw_control_id)

    if local is None:
        return None, False
    nid = f"{target_framework}:{local}"
    if nid in nodes_by_id:
        return nid, True
    return None, False
