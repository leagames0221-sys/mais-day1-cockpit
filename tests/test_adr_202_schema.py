""" schema test (src/integration/schemas.py が SSoT、 本 test は instantiate + validation 検証)。

doctrine: doc-sync 順守、 schema 定義は src/integration/schemas.py に literal 集約 (本 file は import + smoke のみ)。
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

PJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PJ_ROOT))

from src.integration.schemas import ( # noqa: E402
    Answer,
    Citation,
    CommunicationKit,
    DependencyEdge,
    IntegrationPlan,
    JPDay1Pattern,
    JPPattern,
    PlanNode,
    RiskScore,
    T2Output,
    T3Output,
)


def test_t2_output_schema_instantiates() -> None:
    """T2 → T3 入力 schema が valid placeholder data で literal 構築できる。"""
    sample = T2Output(
        ddp_id="DDP-000001",
        citations=[
            Citation(
                citation_id="CIT-000001",
                answer_id="A-000001",
                chunk_id="CHK-000001",
                doc_id="DOC-000001",
                page=12,
                snippet="本契約の効力発生後、 譲渡人は...",
                confidence=0.87,
                human_verified=False,
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
                answer_text_redacted="(redacted)",
                citation_array=["CIT-000001"],
                confidence=0.9,
            )
        ],
    )
    assert sample.ddp_id == "DDP-000001"
    assert len(sample.citations) == 1
    assert sample.jp_patterns_hits[0].severity == "high"


def test_t3_output_schema_instantiates() -> None:
    """T3 → T4 出力 schema が valid placeholder data で literal 構築できる。"""
    sample = T3Output(
        ip_id="IP-000001",
        plan_nodes=[
            PlanNode(
                pn_id="PN-000001",
                ip_id="IP-000001",
                dimension="organization",
                day_n=1,
                statement_redacted="両社の人事部門を統合",
                risk_score_ref="RS-000001",
                owner_role="CHRO",
                completion_criteria="統一 HRBP 5 名選定",
            )
        ],
        dependency_edges=[
            DependencyEdge(
                de_id="DE-000001",
                from_pn="PN-000001",
                to_pn="PN-000002",
                dep_type="blocks",
                weight=0.85,
                risk_score_ref="RS-000002",
                rationale_redacted="(redacted)",
            )
        ],
        communication_kits=[
            CommunicationKit(
                ck_id="CK-000001",
                ip_id="IP-000001",
                audience="employee",
                channel="all-hands letter",
                timing_day_n=1,
                subject="新体制発足に関するご挨拶",
                body_draft_redacted="(redacted)",
                citation_array=["CIT-000001"],
                redaction_level="employee",
            )
        ],
        risk_scores=[
            RiskScore(
                rs_id="RS-000001",
                target_type="plan_node",
                target_id="PN-000001",
                score=67,
                dimensions={
                    "security": 12,
                    "continuity": 25,
                    "culture": 18,
                    "regulatory": 5,
                    "financial": 7,
                },
                jp_day1_pattern_hits=["JPD1-000001"],
                mitigation_recommendation_redacted="(redacted)",
            )
        ],
        jp_day1_hits=[
            JPDay1Pattern(
                jpd1_id="JPD1-000001",
                ip_id="IP-000001",
                axis="union_relation",
                severity="high",
                trigger_source="A-000123",
                summary_redacted="(redacted)",
                mitigation_recommendation_redacted="(redacted)",
            )
        ],
        source_t2_ddp_id="DDP-000001",
        generated_at=datetime(2026, 5, 13, 14, 30),
        confidence=0.82,
    )
    assert sample.ip_id == "IP-000001"
    assert sample.plan_nodes[0].dimension == "organization"
    assert sample.risk_scores[0].dimensions["culture"] == 18


def test_id_prefix_validation_rejects_invalid() -> None:
    """正規表現 pattern が invalid prefix を literal reject。"""
    with pytest.raises(Exception):
        PlanNode(
            pn_id="INVALID-000001",
            ip_id="IP-000001",
            dimension="organization",
            day_n=1,
            statement_redacted="x",
            risk_score_ref="RS-000001",
            owner_role="CHRO",
            completion_criteria="x",
        )


def test_t2_t3_citation_array_link_back() -> None:
    """T3 CommunicationKit が T2 CIT prefix を citation_array literal で参照可能。"""
    kit = CommunicationKit(
        ck_id="CK-000001",
        ip_id="IP-000001",
        audience="customer",
        channel="email",
        timing_day_n=1,
        subject="x",
        body_draft_redacted="(redacted)",
        citation_array=["CIT-000012", "CIT-000045"],
        redaction_level="customer",
    )
    assert all(cit.startswith("CIT-") for cit in kit.citation_array)


def test_audience_specific_redaction_literal_validates() -> None:
    """ audience-specific redaction matrix、 5 audience 全 literal validate。"""
    for audience in ("employee", "customer", "vendor", "regulator", "investor"):
        kit = CommunicationKit(
            ck_id="CK-000001",
            ip_id="IP-000001",
            audience=audience,
            channel="x",
            timing_day_n=1,
            subject="x",
            body_draft_redacted="(redacted)",
            citation_array=[],
            redaction_level=audience,
        )
        assert kit.audience == audience


def test_jp_day1_5_axes_literal_validate() -> None:
    """ jp_day1 5 軸 全 literal validate。"""
    for axis in ("union_relation", "bank_relation", "family_integration", "business_custom", "trade_practice"):
        jpd1 = JPDay1Pattern(
            jpd1_id="JPD1-000001",
            ip_id="IP-000001",
            axis=axis,
            severity="medium",
            trigger_source="x",
            summary_redacted="x",
            mitigation_recommendation_redacted="x",
        )
        assert jpd1.axis == axis
