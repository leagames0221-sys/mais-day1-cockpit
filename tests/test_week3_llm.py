"""Week 3: LLMProvider Protocol + MockProvider + jp_day1 augment + kit generator + Citation link back。"""
from __future__ import annotations

import sys
from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PJ_ROOT))

from src.citation.link_back import (
    AUDIENCE_RELEVANCE_KEYWORDS,
    link_t2_citations_by_audience,
)
from src.communication.generate_kits import AUDIENCE_DEFAULTS, generate_kits_for_ip
from src.integration.schemas import (
    Answer,
    Citation,
    IntegrationPlan,
    JPDay1Pattern,
    JPPattern,
    T2Output,
)
from src.jp_day1.llm_augment import augment_jp_day1_hits
from src.llm.provider import MockProvider, default_provider
from src.orchestrator.build_state_graph import build_t3_graph


def _ip() -> IntegrationPlan:
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


# ----- LLMProvider Protocol + MockProvider -----


def test_default_provider_is_mock() -> None:
    p = default_provider()
    assert isinstance(p, MockProvider)


def test_mock_generates_plan_statement_per_dimension() -> None:
    p = MockProvider()
    for dim in ("organization", "process", "system", "culture"):
        for day_n in (1, 30, 100):
            stmt = p.generate_plan_statement(
                dimension=dim, day_n=day_n, ip_summary="IP=IP-000001",
                relevant_jp_day1_axes=[], severity_marker="",
            )
            assert isinstance(stmt, str)
            assert len(stmt) > 5


def test_mock_plan_statement_includes_jp_marker_when_axes_present() -> None:
    p = MockProvider()
    stmt = p.generate_plan_statement(
        dimension="organization", day_n=1, ip_summary="x",
        relevant_jp_day1_axes=["union_relation"], severity_marker=", max=high",
    )
    assert "jp_day1 axis" in stmt
    assert "union_relation" in stmt


def test_mock_generates_5_audience_bodies() -> None:
    p = MockProvider()
    for audience in ("employee", "customer", "vendor", "regulator", "investor"):
        body = p.generate_communication_body(
            audience=audience, ip_summary="IP=IP-000001",
            timing_day_n=1, subject="x", relevant_citations=["CIT-000001"],
        )
        assert isinstance(body, str)
        assert "[redaction:" in body
        assert "CIT-000001" in body


def test_mock_evaluate_jp_day1_hit_genuine() -> None:
    p = MockProvider()
    is_genuine, reasoning = p.evaluate_jp_day1_hit(
        axis="union_relation", trigger_text="主要取引銀行 + 労働組合 と協議要", keyword_matched="労働組合",
    )
    assert is_genuine is True
    assert "genuine" in reasoning


def test_mock_evaluate_jp_day1_hit_false_positive() -> None:
    p = MockProvider()
    is_genuine, reasoning = p.evaluate_jp_day1_hit(
        axis="union_relation", trigger_text="過去に解散済の労働組合", keyword_matched="労働組合",
    )
    assert is_genuine is False
    assert "false positive" in reasoning


# ----- jp_day1 augment -----


def _hit(axis: str = "union_relation", trigger_source: str = "A-000001") -> JPDay1Pattern:
    return JPDay1Pattern(
        jpd1_id="JPD1-000001",
        ip_id="IP-000001",
        axis=axis,
        severity="high",
        trigger_source=trigger_source,
        summary_redacted=f"keyword '労働組合' literal 検出",
        mitigation_recommendation_redacted="x",
    )


def test_augment_keeps_genuine_hit() -> None:
    hits = [_hit()]
    answers = {"A-000001": "主要取引銀行と労働組合への事前協議が必要"}
    kept, dropped = augment_jp_day1_hits(hits, answers)
    assert len(kept) == 1
    assert len(dropped) == 0
    assert "genuine" in kept[0].mitigation_recommendation_redacted


def test_augment_drops_false_positive() -> None:
    hits = [_hit()]
    answers = {"A-000001": "過去に解散済の労働組合のため対応不要"}
    kept, dropped = augment_jp_day1_hits(hits, answers)
    assert len(kept) == 0
    assert len(dropped) == 1
    assert "false positive" in dropped[0][1]


# ----- Citation link back -----


def test_audience_keywords_cover_5_audiences() -> None:
    expected = {"employee", "customer", "vendor", "regulator", "investor"}
    assert set(AUDIENCE_RELEVANCE_KEYWORDS.keys()) == expected


def test_link_citations_by_keyword_match() -> None:
    t2 = T2Output(
        ddp_id="DDP-000001",
        citations=[
            Citation(
                citation_id="CIT-000001", answer_id="A-000001", chunk_id="CHK-000001",
                doc_id="DOC-000001", page=1, snippet="従業員 + 役員 配置に関する記載", confidence=0.9,
            ),
            Citation(
                citation_id="CIT-000002", answer_id="A-000002", chunk_id="CHK-000002",
                doc_id="DOC-000002", page=2, snippet="主要顧客との契約条件", confidence=0.9,
            ),
        ],
        jp_patterns_hits=[],
        questionnaire_answers=[],
    )
    result = link_t2_citations_by_audience(t2)
    assert "CIT-000001" in result.get("employee", [])
    assert "CIT-000002" in result.get("customer", [])


def test_link_citations_fallback_when_no_keyword_match() -> None:
    t2 = T2Output(
        ddp_id="DDP-000001",
        citations=[
            Citation(
                citation_id="CIT-000001", answer_id="A-000001", chunk_id="CHK-000001",
                doc_id="DOC-000001", page=1, snippet="generic content (no audience keyword)", confidence=0.9,
            )
        ],
        jp_patterns_hits=[],
        questionnaire_answers=[],
    )
    result = link_t2_citations_by_audience(t2)
    # 全 5 audience に fallback link
    for audience in ("employee", "customer", "vendor", "regulator", "investor"):
        assert result.get(audience) == ["CIT-000001"]


# ----- kit generator + e2e integration -----


def test_audience_defaults_cover_5_audiences() -> None:
    assert set(AUDIENCE_DEFAULTS.keys()) == {"employee", "customer", "vendor", "regulator", "investor"}


def test_generate_kits_for_ip_returns_5() -> None:
    kits = generate_kits_for_ip(_ip())
    assert len(kits) == 5
    audiences = {k.audience for k in kits}
    assert audiences == {"employee", "customer", "vendor", "regulator", "investor"}
    for kit in kits:
        assert "[redaction:" in kit.body_draft_redacted
        assert kit.redaction_level == kit.audience


def test_generate_kits_with_citations_link_back() -> None:
    kits = generate_kits_for_ip(
        _ip(),
        citations_by_topic={"employee": ["CIT-001", "CIT-002"], "investor": ["CIT-099"]},
    )
    emp = next(k for k in kits if k.audience == "employee")
    inv = next(k for k in kits if k.audience == "investor")
    assert emp.citation_array == ["CIT-001", "CIT-002"]
    assert inv.citation_array == ["CIT-099"]


def test_e2e_t3_graph_with_llm_augment_and_kit_generation() -> None:
    """e2e: T2 → T3 全 pipeline で LLM augment + kit generator + Citation link back 全 active。"""
    t2 = T2Output(
        ddp_id="DDP-000001",
        citations=[
            Citation(
                citation_id="CIT-000100", answer_id="A-000001", chunk_id="CHK-000001",
                doc_id="DOC-000001", page=1, snippet="従業員 配置 + 雇用継続", confidence=0.9,
            )
        ],
        jp_patterns_hits=[
            JPPattern(jpp_id="JPP-000001", pattern_type="family_governance", severity="high",
                      chunk_refs=["CHK-000001"]),
        ],
        questionnaire_answers=[
            Answer(answer_id="A-000001", question_id="Q-000001",
                   answer_text_redacted="主要取引銀行への報告と労働組合への事前協議を要する",
                   citation_array=["CIT-000100"], confidence=0.9),
        ],
    )
    app = build_t3_graph(use_checkpoint=False)
    final_state = app.invoke(
        {
            "t2_output": t2, "industry": "製造業", "size_band": "100-300 名",
            "day1_target_date": "2026-09-01",
        },
        config={"configurable": {"thread_id": "test-week3"}},
    )
    out = final_state["t3_output"]
    # employee kit に CIT-000100 link back literal verify (snippet に '従業員' literal)
    emp_kit = next(k for k in out.communication_kits if k.audience == "employee")
    assert "CIT-000100" in emp_kit.citation_array
    # LLM augment で reasoning literal 蓄積 (kept hits は genuine reasoning)
    for hit in out.jp_day1_hits:
        assert "genuine" in hit.mitigation_recommendation_redacted