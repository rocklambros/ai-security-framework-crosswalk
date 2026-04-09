from typing import Literal
from pydantic import BaseModel, Field, computed_field


Relation = Literal["equivalent", "related", "partial", "unrelated"]


class GapTuple(BaseModel):
    source_framework: str
    source_id: str
    target_framework: str
    target_node_id: str


class LLMSMELabel(BaseModel):
    model_config = {"protected_namespaces": ()}

    source_framework: str
    source_id: str
    target_framework: str
    target_node_id: str
    relation: Relation
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    prompt_sha: str = Field(min_length=64, max_length=64)
    model_version: str
    provenance_tag: Literal["llm_sme_v1"] = "llm_sme_v1"
    weight: float = 0.6


class CoverageRow(BaseModel):
    source_framework: str
    target_framework: str
    upstream_gold: int = Field(ge=0)
    llm_sme_silver: int = Field(ge=0)

    @computed_field
    @property
    def total(self) -> int:
        return self.upstream_gold + self.llm_sme_silver

    @computed_field
    @property
    def empty(self) -> bool:
        return self.total == 0
