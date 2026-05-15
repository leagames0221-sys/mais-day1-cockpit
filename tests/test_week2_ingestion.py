"""Week 2 day 1-3: T2 → T3 ingestion + jp_day1 trigger mapping smoke test。"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PJ_ROOT))

from src.integration.ingest_t2_output import ( # noqa: E402
    aggregate_severity,
    derive_jp_day1_hits_from_t2,
    ingest_t2_output_to_ip,
    map_jp_pattern_to_axes,
)
from src.integration.schemas import ( # noqa: E402
    Answer,
    Citation,
    JPPattern,
    T2Output,
)


def _build_minimal_t2_output() -> T2Output:
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
                answer_text_redacted="主要取引銀行への報告と労働組合への事前協議を要する",
                citation_array=["CIT-000001"],
                confidence=0.9,
            )
        ],
    )


def test_map_jp_pattern_to_axes_family_governance() -> None:
    """: family_governance → axis 3 (family_integration)。"""
    assert map_jp_pattern_to_axes("family_governance") == ["family_integration"]


def test_map_jp_pattern_to_axes_nominal_shares_dual_axis() -> None:
    """: nominal_shares → axis 3 + axis 2 dual mapping。"""
    axes = map_jp_pattern_to_axes("nominal_shares")
    assert set(axes) == {"family_integration", "bank_relation"}


def test_map_jp_pattern_to_axes_owner_private_expense_dual_axis() -> None:
    """: owner_private_expense → axis 4 + axis 3。"""
    axes = map_jp_pattern_to_axes("owner_private_expense")
    assert set(axes) == {"business_custom", "family_integration"}


def test_map_jp_pattern_to_axes_unknown_returns_empty() -> None:
    """Unknown pattern_type は空 list 返却 (doctrine: waste-zero)。"""
    assert map_jp_pattern_to_axes("unknown_pattern") == []


def test_ingest_t2_output_creates_ip_with_valid_id() -> None:
    """T2Output → IntegrationPlan 変換時 IP-XXXXXX prefix literal 生成 + source_t2_ddp_id link back。"""
    t2 = _build_minimal_t2_output()
    ip, _ = ingest_t2_output_to_ip(
        t2,
        industry="製造業",
        size_band="従業員 100-300 名",
        day1_target_date=date(2026, 9, 1),
    )
    assert ip.ip_id.startswith("IP-")
    assert ip.source_t2_ddp_id == "DDP-000001"
    assert ip.industry == "製造業"
    assert ip.status == "draft"
    assert 0.0 <= ip.confidence <= 1.0


def test_derive_jp_day1_hits_triggers_family_integration_from_t2_jp_pattern() -> None:
    """T2 family_governance hit → T3 family_integration axis JPD1 生成 literal。"""
    t2 = _build_minimal_t2_output()
    hits = derive_jp_day1_hits_from_t2(t2, ip_id="IP-000001")
    family_int_hits = [h for h in hits if h.axis == "family_integration"]
    assert len(family_int_hits) >= 1
    assert family_int_hits[0].severity == "high"
    assert family_int_hits[0].trigger_source == "JPP-000001"


def test_derive_jp_day1_hits_triggers_union_relation_from_keyword() -> None:
    """Answer text に literal 「労働組合」 → union_relation axis JPD1 生成。"""
    t2 = _build_minimal_t2_output()
    hits = derive_jp_day1_hits_from_t2(t2, ip_id="IP-000001")
    union_hits = [h for h in hits if h.axis == "union_relation"]
    assert len(union_hits) >= 1
    assert union_hits[0].severity == "high"


def test_derive_jp_day1_hits_triggers_bank_relation_from_keyword() -> None:
    """Answer text に literal 「主要取引銀行」 → bank_relation axis JPD1 生成。"""
    t2 = _build_minimal_t2_output()
    hits = derive_jp_day1_hits_from_t2(t2, ip_id="IP-000001")
    bank_hits = [h for h in hits if h.axis == "bank_relation"]
    assert len(bank_hits) >= 1
    assert bank_hits[0].severity == "high"


def test_ingest_returns_ip_and_hits_tuple() -> None:
    """ingest_t2_output_to_ip は (IntegrationPlan, list[JPDay1Pattern]) tuple 返却。"""
    t2 = _build_minimal_t2_output()
    ip, hits = ingest_t2_output_to_ip(
        t2,
        industry="製造業",
        size_band="従業員 100-300 名",
        day1_target_date=date(2026, 9, 1),
    )
    assert ip.ip_id.startswith("IP-")
    assert isinstance(hits, list)
    assert all(h.ip_id == ip.ip_id for h in hits)


def test_aggregate_severity_returns_max() -> None:
    """aggregate_severity が literal 最大 severity 返却 (low < medium < high)。"""
    t2 = _build_minimal_t2_output()
    hits = derive_jp_day1_hits_from_t2(t2, ip_id="IP-000001")
    # family_governance high + 主要取引銀行 high + 労働組合 high → max = high
    assert aggregate_severity(hits) == "high"


def test_aggregate_severity_empty_returns_low() -> None:
    """空 hits literal aggregate → low (default lowest)。"""
    assert aggregate_severity([]) == "low"


def test_no_real_pii_in_synthetic_data() -> None:
    """合成 data only、 実 PII (実 銀行名 / 実 個人名) 不在 verify。"""
    t2 = _build_minimal_t2_output()
    # snippet / answer_text_redacted は redact 済 / 業界 keyword のみ literal 期待
    forbidden_real_pii = ["三菱UFJ", "三井住友", "みずほ", "山田太郎", "鈴木一郎"] # 実在 PII を literal 除外
    for c in t2.citations:
        for pii in forbidden_real_pii:
            assert pii not in c.snippet, f"real PII literal in citation: {pii}"
    for a in t2.questionnaire_answers:
        for pii in forbidden_real_pii:
            assert pii not in a.answer_text_redacted, f"real PII literal in answer: {pii}"
