"""LangGraph state schema。

 6 軸 mitigation 設計反映:
- memory-only checkpoint (CVE-2026-28277 + CVE-2025-67644 不発): MemorySaver のみ literal 使用
- Pydantic BaseModel state schema (CVE-2026-44843 不発、 user 入力 deserialize ZERO)
- JsonPlusSerializer 不使用 (GHSA-wwqv-p2pp-99h5 不発): LangGraph default serializer のみ
"""
from __future__ import annotations

from typing import Annotated, TypedDict

from src.integration.schemas import (
    CommunicationKit,
    DependencyEdge,
    IntegrationPlan,
    JPDay1Pattern,
    PlanNode,
    RiskScore,
    T2Output,
    T3Output,
)


def _merge_list(left: list, right: list) -> list:
    """LangGraph reducer: 並列 node からの list output を literal concat (parallel agent merge)。"""
    return (left or []) + (right or [])


class T3State(TypedDict, total=False):
    """T3 orchestrator state schema。

    flow: ingest_t2 → detect_jp_day1 → 4 axis parallel (organization / process / system / culture)
    → build_dependency_graph (NetworkX) → compute_risk_scores → generate_communication_kits
    → finalize_t3_output
    """

    # input
    t2_output: T2Output
    industry: str
    size_band: str
    day1_target_date: str # ISO 8601 str (LangGraph state serializable)

    # intermediate
    integration_plan: IntegrationPlan
    jp_day1_hits: Annotated[list[JPDay1Pattern], _merge_list]
    plan_nodes: Annotated[list[PlanNode], _merge_list] # 4 軸 parallel 結合
    dependency_edges: list[DependencyEdge]
    risk_scores: list[RiskScore]
    communication_kits: list[CommunicationKit]

    # output
    t3_output: T3Output
