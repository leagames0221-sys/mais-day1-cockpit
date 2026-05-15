"""5 audience cascade CommunicationKit body LLM 生成 + audience-specific redaction。"""
from __future__ import annotations

import secrets

from src.integration.schemas import Audience, CommunicationKit, IntegrationPlan
from src.llm.provider import LLMProvider, MockProvider


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{secrets.randbelow(10**9):06d}"


# 5 audience cascade default templates (subject / channel / timing)
AUDIENCE_DEFAULTS: dict[Audience, tuple[int, str, str]] = {
    "employee": (1, "all-hands letter", "新体制発足のご案内"),
    "customer": (1, "service continuity letter", "新体制下でのサービス継続のお知らせ"),
    "vendor": (7, "vendor partnership update", "サプライヤーパートナーシップ継続のお知らせ"),
    "regulator": (1, "regulatory notification", "Change of Control 法定通知"),
    "investor": (1, "IR statement", "経営権異動に関する IR statement"),
}


def generate_kits_for_ip(
    ip: IntegrationPlan,
    citations_by_topic: dict[Audience, list[str]] | None = None,
    provider: LLMProvider | None = None,
) -> list[CommunicationKit]:
    """5 audience CommunicationKit を literal 生成。

    Args:
        ip: IntegrationPlan (ip_id + source_t2_ddp_id 等)
        citations_by_topic: audience ごとの T2 Citation array (link back)
        provider: LLMProvider (default = MockProvider)

    Returns:
        5 CommunicationKit (employee / customer / vendor / regulator / investor)
    """
    if provider is None:
        provider = MockProvider()
    if citations_by_topic is None:
        citations_by_topic = {}

    ip_summary = f"IP={ip.ip_id}、 industry={ip.industry}、 size={ip.size_band}"
    kits: list[CommunicationKit] = []
    for audience, (timing_day_n, channel, subject) in AUDIENCE_DEFAULTS.items():
        citations = citations_by_topic.get(audience, [])
        body = provider.generate_communication_body(
            audience=audience,
            ip_summary=ip_summary,
            timing_day_n=timing_day_n,
            subject=subject,
            relevant_citations=citations,
        )
        kits.append(
            CommunicationKit(
                ck_id=_gen_id("CK"),
                ip_id=ip.ip_id,
                audience=audience,
                channel=channel,
                timing_day_n=timing_day_n,
                subject=subject,
                body_draft_redacted=body,
                citation_array=citations,
                redaction_level=audience,
                human_verified=False,
            )
        )
    return kits
