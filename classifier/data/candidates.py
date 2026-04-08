"""Candidate-pool generation for the 12-pair coverage requirement.

Per-framework appearance counts across the 12 pairs below:
  aiuc_1: 3 (src 1,2,12)
  csa_aicm: 2 (src 3,4)
  mitre_atlas: 3 (src 5 + tgt 4,10)
  nist_rmf: 3 (src 6,7 + tgt 12)
  owasp_llm: 3 (tgt 2,5,8)
  owasp_agentic: 4 (tgt 1,3,6,11)
  owasp_ai_exchange: 2 (src 8 + tgt 9)
  eu_gpai_cop: 2 (src 9 + tgt 7)
  cosai_rm: 2 (src 10,11)
All 9 frameworks have >=2 appearances.
"""
from __future__ import annotations

FRAMEWORKS: list[str] = [
    "aiuc_1", "csa_aicm", "mitre_atlas", "nist_rmf",
    "owasp_llm", "owasp_agentic", "owasp_ai_exchange",
    "eu_gpai_cop", "cosai_rm",
]

FRAMEWORK_PAIRS: list[tuple[str, str]] = [
    ("aiuc_1",             "owasp_agentic"),   # 1
    ("aiuc_1",             "owasp_llm"),       # 2
    ("csa_aicm",           "owasp_agentic"),   # 3
    ("csa_aicm",           "mitre_atlas"),     # 4
    ("mitre_atlas",        "owasp_llm"),       # 5
    ("nist_rmf",           "owasp_agentic"),   # 6
    ("nist_rmf",           "eu_gpai_cop"),     # 7
    ("owasp_ai_exchange",  "owasp_llm"),       # 8
    ("eu_gpai_cop",        "owasp_ai_exchange"), # 9
    ("cosai_rm",           "mitre_atlas"),     # 10
    ("cosai_rm",           "owasp_agentic"),   # 11
    ("aiuc_1",             "nist_rmf"),        # 12
]
assert len(FRAMEWORK_PAIRS) == 12
