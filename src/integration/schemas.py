"""T3 Object Type 6 件 + T2 → T3 入出力契約 schema。

SSoT: mais-deal-matching) + T2 (Citation schema) + T3 /203。
本 module は **operational 側のみ** (PII vault 側 schema は src/vault/ で別途定義予定、 Week 4)。
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ============================================================
# : T2 → T3 入力 schema
# ============================================================


class Citation(BaseModel):
    """T2 から literal 継承 (section_header は ChunkMetadata 側 field のため Citation には不在)。"""

    citation_id: str = Field(pattern=r"^CIT-[0-9]{6,}$")
    answer_id: str = Field(pattern=r"^A-[0-9]{6,}$")
    chunk_id: str = Field(pattern=r"^CHK-[0-9]{6,}$")
    doc_id: str = Field(pattern=r"^DOC-[0-9]{6,}$")
    page: int = Field(ge=1)
    snippet: str = Field(max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)
    human_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None


JPPatternType = Literal["family_governance", "nominal_shares", "owner_private_expense"]
JPDay1Axis = Literal[
    "union_relation", "bank_relation", "family_integration", "business_custom", "trade_practice"
]
Severity = Literal["low", "medium", "high"]
Dimension = Literal["organization", "process", "system", "culture"]
Audience = Literal["employee", "customer", "vendor", "regulator", "investor"]
DepType = Literal["blocks", "blocked-by", "parallel"]
PlanStatus = Literal["draft", "accepted", "arcinternald"]
TargetType = Literal["plan_node", "dependency_edge"]


class JPPattern(BaseModel):
    """T2 中堅 fit pattern hit (T3 jp_day1 detector trigger source)。"""

    jpp_id: str = Field(pattern=r"^JPP-[0-9]{6,}$")
    pattern_type: JPPatternType
    severity: Severity
    chunk_refs: list[str]


class Answer(BaseModel):
    """T2 DD Question 構造化回答 (T3 PlanNode + DependencyEdge weight 入力)。"""

    answer_id: str = Field(pattern=r"^A-[0-9]{6,}$")
    question_id: str = Field(pattern=r"^Q-[0-9]{6,}$")
    answer_text_redacted: str
    citation_array: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class T2Output(BaseModel):
    """T2 API output。"""

    ddp_id: str = Field(pattern=r"^DDP-[0-9]{6,}$")
    citations: list[Citation]
    jp_patterns_hits: list[JPPattern]
    questionnaire_answers: list[Answer]


# ============================================================
# : T3 Object Type 6 件 (operational layer)
# ============================================================


class IntegrationPlan(BaseModel):
    """M&A 案件 1 件 = 1 IP、 100 日計画 root。"""

    ip_id: str = Field(pattern=r"^IP-[0-9]{6,}$")
    source_t2_ddp_id: str = Field(pattern=r"^DDP-[0-9]{6,}$")
    industry: str
    size_band: str
    acquirer_id: str = Field(pattern=r"^ACQ-[0-9]{6,}$")
    target_id: str = Field(pattern=r"^TGT-[0-9]{6,}$")
    day1_target_date: date
    status: PlanStatus = "draft"
    generated_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)


class PlanNode(BaseModel):
    """Day-N task node、 4 軸統合 (operational redacted、 raw は PlanNodePII vault)。"""

    pn_id: str = Field(pattern=r"^PN-[0-9]{6,}$")
    ip_id: str = Field(pattern=r"^IP-[0-9]{6,}$")
    dimension: Dimension
    day_n: int = Field(ge=1, le=100)
    statement_redacted: str
    risk_score_ref: str = Field(pattern=r"^RS-[0-9]{6,}$")
    owner_role: str
    completion_criteria: str


class DependencyEdge(BaseModel):
    """NetworkX graph edge、 PN 間 依存関係。"""

    de_id: str = Field(pattern=r"^DE-[0-9]{6,}$")
    from_pn: str = Field(pattern=r"^PN-[0-9]{6,}$")
    to_pn: str = Field(pattern=r"^PN-[0-9]{6,}$")
    dep_type: DepType
    weight: float = Field(ge=0.0, le=1.0)
    risk_score_ref: str = Field(pattern=r"^RS-[0-9]{6,}$")
    rationale_redacted: str


class CommunicationKit(BaseModel):
    """5 audience cascade (operational redacted、 raw は CommunicationKitPII vault)。"""

    ck_id: str = Field(pattern=r"^CK-[0-9]{6,}$")
    ip_id: str = Field(pattern=r"^IP-[0-9]{6,}$")
    audience: Audience
    channel: str
    timing_day_n: int = Field(ge=1, le=100)
    subject: str
    body_draft_redacted: str
    citation_array: list[str]
    redaction_level: Audience
    human_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None


class RiskScore(BaseModel):
    """PN / DE ごとの 0-100 score、 5 dimension 内訳。"""

    rs_id: str = Field(pattern=r"^RS-[0-9]{6,}$")
    target_type: TargetType
    target_id: str
    score: int = Field(ge=0, le=100)
    dimensions: dict[str, int]
    jp_day1_pattern_hits: list[str]
    mitigation_recommendation_redacted: str


class JPDay1Pattern(BaseModel):
    """5 軸 detector 発火イベント。"""

    jpd1_id: str = Field(pattern=r"^JPD1-[0-9]{6,}$")
    ip_id: str = Field(pattern=r"^IP-[0-9]{6,}$")
    axis: JPDay1Axis
    severity: Severity
    trigger_source: str
    summary_redacted: str
    mitigation_recommendation_redacted: str


# ============================================================
# : T3 → T4 出力 schema
# ============================================================


class T3Output(BaseModel):
    """T3 IntegrationPlan generator API output (T4 / 受託 deploy 用)。"""

    ip_id: str = Field(pattern=r"^IP-[0-9]{6,}$")
    plan_nodes: list[PlanNode]
    dependency_edges: list[DependencyEdge]
    communication_kits: list[CommunicationKit]
    risk_scores: list[RiskScore]
    jp_day1_hits: list[JPDay1Pattern]
    source_t2_ddp_id: str = Field(pattern=r"^DDP-[0-9]{6,}$")
    generated_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)
