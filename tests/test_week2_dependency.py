"""Week 2 day 4-7: NetworkX dep graph + topological sort + cyclic 検出 + RiskScore (ADR-203)。"""
from __future__ import annotations

import sys
from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PJ_ROOT))

import pytest

from src.dependency.compute_risk_score import (
    AXIS_TO_DIMENSION_WEIGHT,
    SEVERITY_MULTIPLIER,
    CyclicDependencyError,
    build_plan_node_graph,
    compute_risk_score_for_target,
    compute_risk_scores_for_plan_nodes,
    detect_cycles,
    topological_critical_path,
)
from src.integration.schemas import DependencyEdge, JPDay1Pattern, PlanNode


def _pn(pn_id: str, dim: str = "organization", day_n: int = 1) -> PlanNode:
    return PlanNode(
        pn_id=pn_id,
        ip_id="IP-000001",
        dimension=dim,
        day_n=day_n,
        statement_redacted="x",
        risk_score_ref="RS-000001",
        owner_role="CEO",
        completion_criteria="x",
    )


def _de(de_id: str, fr: str, to: str, dep_type: str = "blocks") -> DependencyEdge:
    return DependencyEdge(
        de_id=de_id,
        from_pn=fr,
        to_pn=to,
        dep_type=dep_type,
        weight=0.8,
        risk_score_ref="RS-000001",
        rationale_redacted="x",
    )


def _hit(axis: str, severity: str = "medium") -> JPDay1Pattern:
    return JPDay1Pattern(
        jpd1_id="JPD1-000001",
        ip_id="IP-000001",
        axis=axis,
        severity=severity,
        trigger_source="x",
        summary_redacted="x",
        mitigation_recommendation_redacted="x",
    )


# ----- graph construction -----


def test_build_plan_node_graph_basic() -> None:
    pns = [_pn("PN-000001"), _pn("PN-000002"), _pn("PN-000003")]
    des = [_de("DE-000001", "PN-000001", "PN-000002"), _de("DE-000002", "PN-000002", "PN-000003")]
    g = build_plan_node_graph(pns, des)
    assert g.number_of_nodes() == 3
    assert g.number_of_edges() == 2


def test_build_graph_parallel_dep_creates_bidirectional_edges() -> None:
    pns = [_pn("PN-000001"), _pn("PN-000002")]
    des = [_de("DE-000001", "PN-000001", "PN-000002", dep_type="parallel")]
    g = build_plan_node_graph(pns, des)
    # parallel = 両方向 edge
    assert g.has_edge("PN-000001", "PN-000002")
    assert g.has_edge("PN-000002", "PN-000001")


# ----- cycle detection -----


def test_detect_cycles_no_cycle() -> None:
    pns = [_pn("PN-000001"), _pn("PN-000002"), _pn("PN-000003")]
    des = [_de("DE-000001", "PN-000001", "PN-000002"), _de("DE-000002", "PN-000002", "PN-000003")]
    g = build_plan_node_graph(pns, des)
    assert detect_cycles(g) == []


def test_detect_cycles_blocks_cycle() -> None:
    pns = [_pn("PN-000001"), _pn("PN-000002"), _pn("PN-000003")]
    # PN1 → PN2 → PN3 → PN1 (blocks cycle)
    des = [
        _de("DE-000001", "PN-000001", "PN-000002"),
        _de("DE-000002", "PN-000002", "PN-000003"),
        _de("DE-000003", "PN-000003", "PN-000001"),
    ]
    g = build_plan_node_graph(pns, des)
    cycles = detect_cycles(g)
    assert len(cycles) == 1
    assert len(cycles[0]) == 3


def test_topological_critical_path_with_cycle_raises() -> None:
    pns = [_pn("PN-000001"), _pn("PN-000002")]
    des = [
        _de("DE-000001", "PN-000001", "PN-000002"),
        _de("DE-000002", "PN-000002", "PN-000001"),
    ]
    g = build_plan_node_graph(pns, des)
    with pytest.raises(CyclicDependencyError):
        topological_critical_path(g)


def test_topological_critical_path_ok_with_dag() -> None:
    pns = [_pn("PN-000001"), _pn("PN-000002"), _pn("PN-000003")]
    des = [_de("DE-000001", "PN-000001", "PN-000002"), _de("DE-000002", "PN-000002", "PN-000003")]
    g = build_plan_node_graph(pns, des)
    order = topological_critical_path(g)
    assert order.index("PN-000001") < order.index("PN-000002")
    assert order.index("PN-000002") < order.index("PN-000003")


# ----- risk score -----


def test_axis_to_dimension_weight_all_5_axes_covered() -> None:
    expected_axes = {"union_relation", "bank_relation", "family_integration", "business_custom", "trade_practice"}
    assert set(AXIS_TO_DIMENSION_WEIGHT.keys()) == expected_axes


def test_severity_multiplier_monotonic() -> None:
    assert SEVERITY_MULTIPLIER["low"] < SEVERITY_MULTIPLIER["medium"] < SEVERITY_MULTIPLIER["high"]


def test_compute_risk_score_no_hits_returns_base() -> None:
    rs = compute_risk_score_for_target("plan_node", "PN-000001", [])
    assert rs.score >= 20  # base_score default
    assert "no jp_day1 hit" in rs.mitigation_recommendation_redacted
    assert rs.jp_day1_pattern_hits == []


def test_compute_risk_score_high_severity_union_boosts_regulatory() -> None:
    """union_relation high → regulatory dimension に 30 weight × 1.0 multiplier。"""
    rs = compute_risk_score_for_target("plan_node", "PN-000001", [_hit("union_relation", "high")])
    assert rs.dimensions["regulatory"] == 30
    assert "JPD1-000001" in rs.jp_day1_pattern_hits


def test_compute_risk_score_clamped_to_100() -> None:
    """高 severity 多数 hits でも total score literal clamp [0, 100]。"""
    many_hits = [_hit("union_relation", "high"), _hit("bank_relation", "high"), _hit("family_integration", "high")]
    rs = compute_risk_score_for_target("plan_node", "PN-000001", many_hits)
    assert 0 <= rs.score <= 100


def test_compute_risk_scores_for_plan_nodes_full_pipeline() -> None:
    """全 PlanNode に対する RiskScore literal 生成 + dimension match で hits filter。"""
    pns = [_pn("PN-000001", dim="organization"), _pn("PN-000002", dim="system")]
    hits = [_hit("union_relation", "high"), _hit("family_integration", "medium")]
    scores = compute_risk_scores_for_plan_nodes(pns, hits)
    assert len(scores) == 2
    # organization → union_relation match + family_integration match (both axes in DIMENSION_TO_JP_AXES["organization"])
    # system → no match (DIMENSION_TO_JP_AXES["system"] == [])
    org_score = next(s for s in scores if s.target_id == "PN-000001")
    sys_score = next(s for s in scores if s.target_id == "PN-000002")
    assert len(org_score.jp_day1_pattern_hits) >= 1
    assert len(sys_score.jp_day1_pattern_hits) == 0
