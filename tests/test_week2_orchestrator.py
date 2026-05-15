"""Week 2 day 4-7: LangGraph state graph + 4 軸 agent parallel + e2e smoke。"""
from __future__ import annotations

import sys
from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PJ_ROOT))

import pytest

from src.integration.schemas import (
    Answer,
    Citation,
    IntegrationPlan,
    JPDay1Pattern,
    JPPattern,
    T2Output,
    T3Output,
)
from src.orchestrator.build_state_graph import build_t3_graph
from src.planner.agents import (
    DIMENSION_TO_JP_AXES,
    _filter_relevant_hits,
    culture_agent,
    organization_agent,
    process_agent,
    system_agent,
)


def _minimal_t2() -> T2Output:
    return T2Output(
        ddp_id="DDP-000001",
        citations=[
            Citation(
                citation_id="CIT-000001",
                answer_id="A-000001",
                chunk_id="CHK-000001",
                doc_id="DOC-000001",
                page=1,
                snippet="(redacted)",
                confidence=0.8,
            )
        ],
        jp_patterns_hits=[
            JPPattern(
                jpp_id="JPP-000001",
                pattern_type="family_governance",
                severity="high",
                chunk_refs=["CHK-000001"],
            )
        ],
        questionnaire_answers=[
            Answer(
                answer_id="A-000001",
                question_id="Q-000001",
                answer_text_redacted="主要取引銀行と労働組合に関する事前協議が必要",
                citation_array=["CIT-000001"],
                confidence=0.9,
            )
        ],
    )


def _minimal_ip() -> IntegrationPlan:
    from datetime import date, datetime, timezone

    return IntegrationPlan(
        ip_id="IP-000001",
        source_t2_ddp_id="DDP-000001",
        industry="製造業",
        size_band="従業員 100-300 名",
        acquirer_id="ACQ-000001",
        target_id="TGT-000001",
        day1_target_date=date(2026, 9, 1),
        status="draft",
        generated_at=datetime.now(timezone.utc),
        confidence=0.8,
    )


def _hit(axis: str, severity: str = "medium") -> JPDay1Pattern:
    return JPDay1Pattern(
        jpd1_id=f"JPD1-{secrets_int():06d}",
        ip_id="IP-000001",
        axis=axis,
        severity=severity,
        trigger_source="x",
        summary_redacted="x",
        mitigation_recommendation_redacted="x",
    )


def secrets_int() -> int:
    import secrets

    return secrets.randbelow(10**6)


# ----- agent unit tests -----


def test_dimension_to_jp_axes_mapping_literal() -> None:
    """ + dimension ↔ axis literal mapping。"""
    assert "union_relation" in DIMENSION_TO_JP_AXES["organization"]
    assert "family_integration" in DIMENSION_TO_JP_AXES["culture"]
    assert DIMENSION_TO_JP_AXES["system"] == [] # : system 軸は jp_day1 と直接 link なし


def test_filter_relevant_hits_organization() -> None:
    hits = [_hit("union_relation"), _hit("trade_practice")]
    rel = _filter_relevant_hits(hits, "organization")
    assert len(rel) == 1
    assert rel[0].axis == "union_relation"


def test_organization_agent_returns_plan_nodes() -> None:
    state = {"integration_plan": _minimal_ip(), "jp_day1_hits": [_hit("union_relation", "high")]}
    out = organization_agent(state)
    assert "plan_nodes" in out
    assert all(pn.dimension == "organization" for pn in out["plan_nodes"])
    assert len(out["plan_nodes"]) == 3 # Day 1 / 30 / 100


def test_4_agents_all_return_3_nodes() -> None:
    state = {"integration_plan": _minimal_ip(), "jp_day1_hits": []}
    for agent_fn, dim in (
        (organization_agent, "organization"),
        (process_agent, "process"),
        (system_agent, "system"),
        (culture_agent, "culture"),
    ):
        out = agent_fn(state)
        assert len(out["plan_nodes"]) == 3
        assert all(pn.dimension == dim for pn in out["plan_nodes"])


# ----- state graph e2e smoke -----


def test_build_t3_graph_compiles_without_error() -> None:
    """LangGraph DAG が literal compile 可能 (構造的 import / wiring 確認)。"""
    app = build_t3_graph(use_checkpoint=True)
    assert app is not None


def test_build_t3_graph_without_checkpoint_compiles() -> None:
    """checkpoint なし版も literal compile 可能。"""
    app = build_t3_graph(use_checkpoint=False)
    assert app is not None


def test_t3_graph_e2e_smoke_with_mock_t2() -> None:
    """T2 mock output → T3Output 全 pipeline e2e literal run。"""
    app = build_t3_graph(use_checkpoint=True)
    config = {"configurable": {"thread_id": "test-thread-1"}}
    initial_state = {
        "t2_output": _minimal_t2(),
        "industry": "製造業",
        "size_band": "従業員 100-300 名",
        "day1_target_date": "2026-09-01",
    }
    final_state = app.invoke(initial_state, config=config)

    # T3Output literal validated
    assert "t3_output" in final_state
    out: T3Output = final_state["t3_output"]
    assert out.ip_id.startswith("IP-")
    assert out.source_t2_ddp_id == "DDP-000001"

    # 4 軸 × 3 Day = 12 PlanNode
    assert len(out.plan_nodes) == 12
    dimensions = {pn.dimension for pn in out.plan_nodes}
    assert dimensions == {"organization", "process", "system", "culture"}

    # 各 dim 内 Day 1 → 30 → 100 = **2 transitions** × 4 dim = **8 DependencyEdge** (n-1 edges per dim)
    assert len(out.dependency_edges) == 8

    # 12 PlanNode → 12 RiskScore
    assert len(out.risk_scores) == 12

    # 5 audience CommunicationKit
    assert len(out.communication_kits) == 5
    audiences = {ck.audience for ck in out.communication_kits}
    assert audiences == {"employee", "customer", "vendor", "regulator", "investor"}

    # jp_day1_hits = T2 family_governance (high) + 主要取引銀行 + 労働組合 = ≥ 3 件
    assert len(out.jp_day1_hits) >= 3
    axes = {h.axis for h in out.jp_day1_hits}
    assert "family_integration" in axes
    assert "bank_relation" in axes
    assert "union_relation" in axes


def test_t3_graph_returns_valid_t3output_schema() -> None:
    """LangGraph 出力が T3Output Pydantic schema を literal pass。"""
    app = build_t3_graph(use_checkpoint=True)
    initial_state = {
        "t2_output": _minimal_t2(),
        "industry": "製造業",
        "size_band": "従業員 100-300 名",
        "day1_target_date": "2026-09-01",
    }
    final_state = app.invoke(initial_state, config={"configurable": {"thread_id": "test-thread-2"}})
    out = final_state["t3_output"]
    # Pydantic re-validation で literal schema 順守 verify
    T3Output.model_validate(out.model_dump())
