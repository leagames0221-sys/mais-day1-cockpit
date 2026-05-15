""" Stage 2 LLM augmentation: keyword scan の false positive 排除 + reasoning (★★→★★★ 化)。"""
from __future__ import annotations

from src.integration.schemas import JPDay1Pattern
from src.llm.provider import LLMProvider, MockProvider


def augment_jp_day1_hits(
    hits: list[JPDay1Pattern],
    answers_by_id: dict[str, str], # answer_id -> answer_text_redacted (raw context)
    provider: LLMProvider | None = None,
) -> tuple[list[JPDay1Pattern], list[tuple[str, str]]]:
    """Stage 2 LLM 評価で false positive を literal drop + reasoning 蓄積。

    Args:
        hits: Stage 1 (regex / keyword) で生成した JPDay1Pattern
        answers_by_id: T2 Answer text (answer_id key、 LLM context として provide)
        provider: LLMProvider (default = MockProvider)

    Returns:
        (kept_hits, dropped_with_reasoning): kept + drop reasoning list
    """
    if provider is None:
        provider = MockProvider()

    kept: list[JPDay1Pattern] = []
    dropped: list[tuple[str, str]] = []

    for hit in hits:
        # trigger_source が answer_id なら literal answer text を context として使用
        context_text = answers_by_id.get(hit.trigger_source, hit.summary_redacted)

        # MockProvider は keyword を summary から抽出 (literal 「keyword '<x>' literal 検出」 pattern)
        import re

        m = re.search(r"keyword '([^']+)'", hit.summary_redacted)
        keyword = m.group(1) if m else "(unknown)"

        is_genuine, reasoning = provider.evaluate_jp_day1_hit(
            axis=hit.axis,
            trigger_text=context_text,
            keyword_matched=keyword,
        )
        if is_genuine:
            # mitigation_recommendation_redacted を LLM reasoning で literal upgrade
            updated = hit.model_copy(
                update={"mitigation_recommendation_redacted": reasoning}
            )
            kept.append(updated)
        else:
            dropped.append((hit.jpd1_id, reasoning))

    return kept, dropped
