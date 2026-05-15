"""4 軸 agent (organization / process / system / culture) skeleton (ADR-204)。

PoC = MockProvider (LLMProvider Protocol、 T1/T2 inherit)、 Week 3 で Claude / Gemini 1 file swap。
各 agent は IntegrationPlan + jp_day1_hits (axis filter) を受け、 PlanNode list を返却。
"""
from __future__ import annotations

import secrets
from typing import Literal

from src.integration.schemas import Dimension, IntegrationPlan, JPDay1Pattern, PlanNode


def _gen_id(prefix: str) -> str:
    """T1/T2 同 pattern、 secrets で衝突回避。"""
    return f"{prefix}-{secrets.randbelow(10**9):06d}"


# axis → JPDay1Axis mapping (どの jp_day1_hits が 各 dimension agent に literal relevant か)
DIMENSION_TO_JP_AXES: dict[Dimension, list[str]] = {
    "organization": ["union_relation", "family_integration"],
    "process": ["business_custom", "trade_practice"],
    "system": [],  # IT system 統合 = jp_day1 5 軸と直接 link なし (Week 3 LLM augmentation で expand)
    "culture": ["family_integration", "business_custom"],
}


def _filter_relevant_hits(
    hits: list[JPDay1Pattern], dimension: Dimension
) -> list[JPDay1Pattern]:
    """各 dimension agent が literal 参照すべき jp_day1_hits を axis match で filter。"""
    relevant_axes = DIMENSION_TO_JP_AXES.get(dimension, [])
    return [h for h in hits if h.axis in relevant_axes]


def _mock_plan_nodes_for_dimension(
    ip: IntegrationPlan, hits: list[JPDay1Pattern], dimension: Dimension
) -> list[PlanNode]:
    """PoC mock implementation: 3 Day-N (1 / 30 / 100) node per dimension literal 生成。

    Week 3 で MockProvider → Claude / Gemini に 1 file swap (LLMProvider Protocol)。
    """
    severity_marker = ""
    if hits:
        max_severity = max(h.severity for h in hits)
        severity_marker = f" [jp_day1 hit: max_severity={max_severity}]"

    nodes: list[PlanNode] = []
    templates_per_dim: dict[Dimension, list[tuple[int, str, str, str]]] = {
        "organization": [
            (1, "新体制の役員配置確定 + 全社員説明会 literal 実施", "CEO", "Day-1 全社員 説明会 完了"),
            (30, "HRBP 統一体制 + 評価制度 統合 plan 策定", "CHRO", "統一 HRBP 5 名 任命完了"),
            (100, "組織 redesign 完遂 + retention plan execute", "CHRO", "離職率 < 業界 average"),
        ],
        "process": [
            (1, "業務 process 棚卸 + Day-1 維持 vs 統合 vs 分離 判定", "COO", "process inventory 完成"),
            (30, "重点 process 統合 (調達 / 経費精算 / 受発注) 段階移行 plan", "COO", "Phase 1 process 統合 完了"),
            (100, "process 統合 完遂 + KPI 監視 dashboard active", "COO", "統合後 KPI 業界平均以上"),
        ],
        "system": [
            (1, "system 統合 dependency graph 確定 + Day-1 critical system 維持", "CIO", "Day-1 critical system 全稼働"),
            (30, "account 統合 + identity provider 統合 + SSO 移行", "CIO", "SSO 統合 完了"),
            (100, "core ERP / CRM 統合 完遂 + legacy retire", "CIO", "legacy system 0 件"),
        ],
        "culture": [
            (1, "両社 culture survey + key value statement 確定", "CHRO", "culture survey response > 70%"),
            (30, "cross-team workshop + leadership alignment session", "CHRO", "workshop 全 manager 参加"),
            (100, "統合 culture brand 確立 + 内部評価 literal 検証", "CHRO", "engagement score 業界 top quartile"),
        ],
    }

    for day_n, statement, owner_role, criteria in templates_per_dim[dimension]:
        nodes.append(
            PlanNode(
                pn_id=_gen_id("PN"),
                ip_id=ip.ip_id,
                dimension=dimension,
                day_n=day_n,
                statement_redacted=statement + severity_marker,
                risk_score_ref=_gen_id("RS"),  # placeholder、 compute_risk_score で本 RS と link 上書き
                owner_role=owner_role,
                completion_criteria=criteria,
            )
        )
    return nodes


def organization_agent(state: dict) -> dict:
    """organization 軸 agent: 役員 / HR / 組織 redesign 関連 PlanNode 生成。"""
    ip: IntegrationPlan = state["integration_plan"]
    hits: list[JPDay1Pattern] = state.get("jp_day1_hits", [])
    relevant = _filter_relevant_hits(hits, "organization")
    nodes = _mock_plan_nodes_for_dimension(ip, relevant, "organization")
    return {"plan_nodes": nodes}


def process_agent(state: dict) -> dict:
    """process 軸 agent: 業務 process 統合 関連 PlanNode 生成。"""
    ip: IntegrationPlan = state["integration_plan"]
    hits: list[JPDay1Pattern] = state.get("jp_day1_hits", [])
    relevant = _filter_relevant_hits(hits, "process")
    nodes = _mock_plan_nodes_for_dimension(ip, relevant, "process")
    return {"plan_nodes": nodes}


def system_agent(state: dict) -> dict:
    """system 軸 agent: IT system 統合 関連 PlanNode 生成。"""
    ip: IntegrationPlan = state["integration_plan"]
    hits: list[JPDay1Pattern] = state.get("jp_day1_hits", [])
    relevant = _filter_relevant_hits(hits, "system")
    nodes = _mock_plan_nodes_for_dimension(ip, relevant, "system")
    return {"plan_nodes": nodes}


def culture_agent(state: dict) -> dict:
    """culture 軸 agent: culture 統合 関連 PlanNode 生成。"""
    ip: IntegrationPlan = state["integration_plan"]
    hits: list[JPDay1Pattern] = state.get("jp_day1_hits", [])
    relevant = _filter_relevant_hits(hits, "culture")
    nodes = _mock_plan_nodes_for_dimension(ip, relevant, "culture")
    return {"plan_nodes": nodes}
