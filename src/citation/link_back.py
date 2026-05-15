"""T2 Citation array link back: T3 CommunicationKit + PlanNode source link back (T2 ADR-102 inherit)。"""
from __future__ import annotations

from collections import defaultdict

from src.integration.schemas import Audience, Citation, T2Output


# audience ごとの T2 Citation relevance heuristic (PoC: keyword + page 範囲 で simple split)
# 受託 deploy 時 = LLM relevance scoring に literal upgrade
AUDIENCE_RELEVANCE_KEYWORDS: dict[Audience, list[str]] = {
    "employee": ["人事", "労働", "雇用", "従業員", "役員", "組織"],
    "customer": ["顧客", "サービス", "契約", "品質", "納期"],
    "vendor": ["仕入", "取引先", "支払", "サプライヤー", "Change of Control"],
    "regulator": ["法定", "届出", "規制", "認可", "コンプライアンス"],
    "investor": ["株主", "IR", "シナジー", "EPS", "業績", "株価"],
}


def link_t2_citations_by_audience(t2: T2Output) -> dict[Audience, list[str]]:
    """T2 Citation array を 5 audience ごとに literal split (PoC: keyword heuristic)。

    Returns:
        {audience: [citation_id, ...]} の dict (各 audience 最大 5 件)
    """
    result: dict[Audience, list[str]] = defaultdict(list)

    for citation in t2.citations:
        # snippet keyword scan で audience relevance 判定
        for audience, keywords in AUDIENCE_RELEVANCE_KEYWORDS.items():
            if any(kw in citation.snippet for kw in keywords):
                if len(result[audience]) < 5:
                    result[audience].append(citation.citation_id)

    # 全 audience 空なら literal default = 各 audience に 1 件目を fallback link
    if not any(result.values()) and t2.citations:
        for audience in AUDIENCE_RELEVANCE_KEYWORDS:
            result[audience] = [t2.citations[0].citation_id]

    return dict(result)
