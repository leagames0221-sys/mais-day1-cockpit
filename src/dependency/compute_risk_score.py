"""NetworkX dependency graph + RiskScore 自動算出 (ADR-203 + ADR-205)。

ADR-203 5 dimension (security / continuity / culture / regulatory / financial) で 0-100 score、
ADR-205 jp_day1_hits を literal 反映 (severity high → score boost、 axis に応じ dimension 配分)。
"""
from __future__ import annotations

import secrets
from typing import Iterable

import networkx as nx

from src.integration.schemas import (
    DependencyEdge,
    DepType,
    JPDay1Axis,
    JPDay1Pattern,
    PlanNode,
    RiskScore,
    Severity,
    TargetType,
)


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{secrets.randbelow(10**9):06d}"


# axis → 5 dimension impact weight (ADR-205 連動)
AXIS_TO_DIMENSION_WEIGHT: dict[JPDay1Axis, dict[str, int]] = {
    "union_relation": {"regulatory": 30, "continuity": 25, "culture": 15, "security": 0, "financial": 5},
    "bank_relation": {"financial": 40, "continuity": 20, "regulatory": 10, "security": 5, "culture": 0},
    "family_integration": {"culture": 30, "continuity": 15, "regulatory": 5, "financial": 10, "security": 0},
    "business_custom": {"culture": 20, "continuity": 10, "regulatory": 5, "financial": 10, "security": 0},
    "trade_practice": {"financial": 25, "continuity": 15, "regulatory": 5, "security": 0, "culture": 5},
}

SEVERITY_MULTIPLIER: dict[Severity, float] = {"low": 0.3, "medium": 0.6, "high": 1.0}


def build_plan_node_graph(
    plan_nodes: list[PlanNode], dependency_edges: list[DependencyEdge]
) -> nx.DiGraph:
    """NetworkX DiGraph 構築 (PN = node、 DE = edge)。

    blocks / blocked-by は方向あり (from → to)、 parallel は方向なし (両方向 edge)。
    """
    g: nx.DiGraph = nx.DiGraph()
    for pn in plan_nodes:
        g.add_node(pn.pn_id, dimension=pn.dimension, day_n=pn.day_n, owner_role=pn.owner_role)
    for de in dependency_edges:
        if de.dep_type == "blocks":
            g.add_edge(de.from_pn, de.to_pn, de_id=de.de_id, weight=de.weight, dep_type="blocks")
        elif de.dep_type == "blocked-by":
            g.add_edge(de.to_pn, de.from_pn, de_id=de.de_id, weight=de.weight, dep_type="blocks")
        else:  # parallel = 両方向 (ordering 不要、 同期実行 marker)
            g.add_edge(de.from_pn, de.to_pn, de_id=de.de_id, weight=de.weight, dep_type="parallel")
            g.add_edge(de.to_pn, de.from_pn, de_id=de.de_id, weight=de.weight, dep_type="parallel")
    return g


def detect_cycles(g: nx.DiGraph) -> list[list[str]]:
    """cyclic dependency 検出 (blocks edge 経由の cycle のみ、 parallel は exclude)。

    blocks-only sub-graph で simple_cycles literal 検出。 cycle 検出 = literal critical error。
    """
    blocks_only = nx.DiGraph()
    blocks_only.add_nodes_from(g.nodes(data=True))
    for u, v, data in g.edges(data=True):
        if data.get("dep_type") == "blocks":
            blocks_only.add_edge(u, v)
    return list(nx.simple_cycles(blocks_only))


def topological_critical_path(g: nx.DiGraph) -> list[str]:
    """blocks edge の topological sort + critical path 算出 (cycle なし前提)。

    cycle 検出時は CyclicDependencyError raise (T3 systemPatterns 順守)。
    """
    blocks_only = nx.DiGraph()
    blocks_only.add_nodes_from(g.nodes(data=True))
    for u, v, data in g.edges(data=True):
        if data.get("dep_type") == "blocks":
            blocks_only.add_edge(u, v)
    if not nx.is_directed_acyclic_graph(blocks_only):
        cycles = list(nx.simple_cycles(blocks_only))
        raise CyclicDependencyError(f"blocks cycle detected: {cycles}")
    return list(nx.topological_sort(blocks_only))


class CyclicDependencyError(Exception):
    """ADR-204 systemPatterns 順守: blocks cycle 検出時 raise (NetworkX simple_cycles で literal detect)。"""


def compute_risk_score_for_target(
    target_type: TargetType,
    target_id: str,
    relevant_hits: Iterable[JPDay1Pattern],
    base_score: int = 20,
) -> RiskScore:
    """target (PN or DE) ごとの 0-100 RiskScore + 5 dimension 内訳 literal 算出。

    base_score + Σ (axis_weight × severity_multiplier) で clamp [0, 100]。
    """
    dimensions: dict[str, int] = {
        "security": 0,
        "continuity": 0,
        "culture": 0,
        "regulatory": 0,
        "financial": 0,
    }
    hit_ids: list[str] = []
    for hit in relevant_hits:
        hit_ids.append(hit.jpd1_id)
        weights = AXIS_TO_DIMENSION_WEIGHT.get(hit.axis, {})
        mult = SEVERITY_MULTIPLIER[hit.severity]
        for dim, w in weights.items():
            dimensions[dim] += int(w * mult)

    # base_score を continuity に振り (default baseline)
    dimensions["continuity"] += base_score

    # clamp + total score
    for dim in dimensions:
        dimensions[dim] = max(0, min(100, dimensions[dim]))
    total = max(0, min(100, sum(dimensions.values())))

    return RiskScore(
        rs_id=_gen_id("RS"),
        target_type=target_type,
        target_id=target_id,
        score=total,
        dimensions=dimensions,
        jp_day1_pattern_hits=hit_ids,
        mitigation_recommendation_redacted=(
            "(Week 3 LLM augmentation 後 literal 埋め込み)" if hit_ids else "(no jp_day1 hit)"
        ),
    )


def compute_risk_scores_for_plan_nodes(
    plan_nodes: list[PlanNode], jp_day1_hits: list[JPDay1Pattern]
) -> list[RiskScore]:
    """各 PlanNode に対する RiskScore literal 算出 (dimension match で relevant hits filter)。"""
    from src.planner.agents import DIMENSION_TO_JP_AXES

    scores: list[RiskScore] = []
    for pn in plan_nodes:
        relevant_axes = set(DIMENSION_TO_JP_AXES.get(pn.dimension, []))
        relevant = [h for h in jp_day1_hits if h.axis in relevant_axes]
        rs = compute_risk_score_for_target("plan_node", pn.pn_id, relevant)
        scores.append(rs)
    return scores
