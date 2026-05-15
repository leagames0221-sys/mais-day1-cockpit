"""T2 API output → T3 IntegrationPlan 変換 + jp_day1 trigger mapping (ADR-202 + ADR-205)。

ADR-205 T2 → T3 trigger mapping:
- family_governance → axis 3 (family_integration)
- nominal_shares → axis 3 (family_integration) + axis 2 (bank_relation、 担保 影響)
- owner_private_expense → axis 4 (business_custom) + axis 3 (family_integration、 同族 連動)
"""
from __future__ import annotations

import secrets
from datetime import date, datetime, timezone
from typing import Iterable

from .schemas import (
    IntegrationPlan,
    JPDay1Axis,
    JPDay1Pattern,
    JPPattern,
    Severity,
    T2Output,
)


def _gen_id(prefix: str) -> str:
    """ID prefix + 6 char zero-padded numeric (T1/T2 同 pattern、 secrets で衝突回避)。"""
    return f"{prefix}-{secrets.randbelow(10**9):06d}"


def map_jp_pattern_to_axes(pattern_type: str) -> list[JPDay1Axis]:
    """T2 jp_patterns_hits の pattern_type を T3 jp_day1 5 軸に literal map (ADR-205)。"""
    mapping: dict[str, list[JPDay1Axis]] = {
        "family_governance": ["family_integration"],
        "nominal_shares": ["family_integration", "bank_relation"],
        "owner_private_expense": ["business_custom", "family_integration"],
    }
    return mapping.get(pattern_type, [])


def derive_jp_day1_hits_from_t2(t2: T2Output, ip_id: str) -> list[JPDay1Pattern]:
    """T2 jp_patterns_hits + Answer keyword から T3 JPDay1Pattern hits を literal 生成。

    PoC level: pattern_type → axis mapping のみ (Stage 1 regex)、 Stage 2 LLM augmentation は Week 3。
    """
    hits: list[JPDay1Pattern] = []

    # T2 jp_patterns_hits direct mapping
    for jpp in t2.jp_patterns_hits:
        for axis in map_jp_pattern_to_axes(jpp.pattern_type):
            hits.append(
                JPDay1Pattern(
                    jpd1_id=_gen_id("JPD1"),
                    ip_id=ip_id,
                    axis=axis,
                    severity=jpp.severity,
                    trigger_source=jpp.jpp_id,
                    summary_redacted=f"T2 jp_pattern {jpp.pattern_type} hit、 軸 {axis} に literal map (ADR-205)",
                    mitigation_recommendation_redacted="(Week 3 LLM augmentation 後 literal 埋め込み)",
                )
            )

    # Stage 1 keyword scan (Answer text に literal keyword 出現で trigger)
    keyword_to_axis_severity: dict[str, tuple[JPDay1Axis, Severity]] = {
        "労働組合": ("union_relation", "high"),
        "労組": ("union_relation", "high"),
        "団体交渉": ("union_relation", "high"),
        "労働協約": ("union_relation", "medium"),
        "36 協定": ("union_relation", "medium"),
        "主要取引銀行": ("bank_relation", "high"),
        "コミットメントライン": ("bank_relation", "high"),
        "期限の利益": ("bank_relation", "high"),
        "コベナンツ": ("bank_relation", "high"),
        "検収基準": ("trade_practice", "medium"),
        "親会社保証": ("trade_practice", "high"),
        "ファクタリング": ("trade_practice", "low"),
        "中元": ("business_custom", "low"),
        "歳暮": ("business_custom", "low"),
        "慶弔金": ("business_custom", "low"),
    }
    for ans in t2.questionnaire_answers:
        for keyword, (axis, severity) in keyword_to_axis_severity.items():
            if keyword in ans.answer_text_redacted:
                hits.append(
                    JPDay1Pattern(
                        jpd1_id=_gen_id("JPD1"),
                        ip_id=ip_id,
                        axis=axis,
                        severity=severity,
                        trigger_source=ans.answer_id,
                        summary_redacted=(
                            f"T2 Answer に keyword '{keyword}' literal 検出、 "
                            f"軸 {axis} severity={severity} (ADR-205 pattern library)"
                        ),
                        mitigation_recommendation_redacted="(Week 3 LLM augmentation 後 literal 埋め込み)",
                    )
                )

    return hits


def ingest_t2_output_to_ip(
    t2: T2Output,
    industry: str,
    size_band: str,
    day1_target_date: date,
    confidence: float = 0.75,
) -> tuple[IntegrationPlan, list[JPDay1Pattern]]:
    """T2 API output → T3 IntegrationPlan + JPDay1Pattern hits literal 変換。

    NOTE: 4 軸 PlanNode + DependencyEdge + RiskScore は LangGraph state graph (ADR-204) で生成、
    本 function は IngestionPlan root + jp_day1 trigger のみ literal 生成 (Week 2 day 1-3 scope)。
    """
    ip = IntegrationPlan(
        ip_id=_gen_id("IP"),
        source_t2_ddp_id=t2.ddp_id,
        industry=industry,
        size_band=size_band,
        acquirer_id=_gen_id("ACQ"),
        target_id=_gen_id("TGT"),
        day1_target_date=day1_target_date,
        status="draft",
        generated_at=datetime.now(timezone.utc),
        confidence=confidence,
    )
    jp_day1_hits = derive_jp_day1_hits_from_t2(t2, ip.ip_id)
    return ip, jp_day1_hits


def aggregate_severity(hits: Iterable[JPDay1Pattern]) -> Severity:
    """JPDay1Pattern hits の literal 最大 severity を集計 (PoC level)。"""
    rank: dict[Severity, int] = {"low": 1, "medium": 2, "high": 3}
    max_rank = 0
    for h in hits:
        max_rank = max(max_rank, rank[h.severity])
    if max_rank == 3:
        return "high"
    if max_rank == 2:
        return "medium"
    return "low"
