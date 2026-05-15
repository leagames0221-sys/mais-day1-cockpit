"""T3 LLMProvider Protocol。

T1 LLMProvider は listwise rerank 特化、 T3 は generative tasks (plan statement / communication body /
jp_day1 LLM augmentation) なので literal 別 Protocol を起草 (doctrine: waste-zero 例外 = task signature 違)。

PoC = MockProvider (deterministic template、 LLM API call ZERO)、 受託 deploy 時 Claude / Gemini /
Ollama に 1 file swap (provider 差替えのみ)。 軸 ② 「prompt code embedded」 設計反映
(CVE-2026-34070 不発)。
"""
from __future__ import annotations

from typing import Literal, Protocol

# T3 Dimension / Audience / JPDay1Axis (schemas.py inherit)
Dimension = Literal["organization", "process", "system", "culture"]
Audience = Literal["employee", "customer", "vendor", "regulator", "investor"]
JPDay1Axis = Literal[
    "union_relation", "bank_relation", "family_integration", "business_custom", "trade_practice"
]


class LLMProvider(Protocol):
    """T3 generative tasks 最小 interface (4 method、 各 PoC = MockProvider deterministic)。"""

    def generate_plan_statement(
        self,
        dimension: Dimension,
        day_n: int,
        ip_summary: str,
        relevant_jp_day1_axes: list[str],
        severity_marker: str,
    ) -> str:
        """4 軸 agent (organization / process / system / culture) Day-N plan statement 生成。"""
        ...

    def generate_communication_body(
        self,
        audience: Audience,
        ip_summary: str,
        timing_day_n: int,
        subject: str,
        relevant_citations: list[str],
    ) -> str:
        """5 audience cascade body draft 生成 (audience-specific redaction 適用)。"""
        ...

    def evaluate_jp_day1_hit(
        self,
        axis: JPDay1Axis,
        trigger_text: str,
        keyword_matched: str,
    ) -> tuple[bool, str]:
        """Stage 2: keyword hit が false positive かを LLM で literal 評価。

        returns: (is_genuine_hit, reasoning)
            is_genuine_hit = True → keep、 False → drop (false positive 排除)
        """
        ...


# ============================================================
# MockProvider (PoC、 deterministic template、 LLM API call ZERO)
# ============================================================


class MockProvider:
    """deterministic mock LLM (PoC demo + test 用、 API key 不要、 数 ms 応答)。

    本番 swap path (doctrine: future-proof):
        - ClaudeProvider(api_key=os.environ["ANTHROPIC_API_KEY"]) で literal 1 file swap
        - GeminiProvider(api_key=...) 同様
        - OllamaProvider(model="llama3:8b") = local 完結、 完全無料 + cloud 不要 path
    """

    # ----- generate_plan_statement -----

    _PLAN_TEMPLATES: dict[Dimension, dict[int, str]] = {
        "organization": {
            1: "Day-1 新体制発表 + 全社員説明会 literal 実施、 役員配置 + HRBP 体制 即 確定",
            30: "HRBP 統一体制 + 評価制度 統合 plan 策定、 retention plan 起動",
            100: "組織 redesign 完遂 + retention 効果 literal 検証、 離職率 業界平均以下 目標",
        },
        "process": {
            1: "業務 process 棚卸 + Day-1 維持 vs 統合 vs 分離 判定、 critical process 全 確保",
            30: "重点 process 統合 (調達 / 経費精算 / 受発注) 段階移行、 Phase 1 完了",
            100: "process 統合 完遂 + KPI 監視 dashboard active、 統合後 業界平均以上",
        },
        "system": {
            1: "system 統合 dependency graph 確定 + Day-1 critical system 全 稼働 維持",
            30: "account 統合 + identity provider 統合 + SSO 移行 完了",
            100: "core ERP / CRM 統合 完遂 + legacy system retire、 統合 system 100% 移行",
        },
        "culture": {
            1: "両社 culture survey + key value statement 確定、 cross-team intro session",
            30: "cross-team workshop + leadership alignment、 全 manager 参加 達成",
            100: "統合 culture brand 確立 + engagement score 業界 top quartile literal 検証",
        },
    }

    def generate_plan_statement(
        self,
        dimension: Dimension,
        day_n: int,
        ip_summary: str,
        relevant_jp_day1_axes: list[str],
        severity_marker: str,
    ) -> str:
        base = self._PLAN_TEMPLATES[dimension].get(day_n, f"Day-{day_n} {dimension} 軸 統合作業")
        jp_marker = ""
        if relevant_jp_day1_axes:
            axes_str = ", ".join(relevant_jp_day1_axes)
            jp_marker = f" [jp_day1 axis: {axes_str}{severity_marker}]"
        return base + jp_marker

    # ----- generate_communication_body -----

    _AUDIENCE_REDACTION_RULES: dict[Audience, str] = {
        "employee": "内部金額 redact、 担当者氏名 OK (内部 audience)",
        "customer": "内部金額 + 担当者氏名 + 内部 process detail 全 redact",
        "vendor": "内部金額 + 担当者氏名 + 内部 process detail 全 redact",
        "regulator": "法定報告事項のみ literal 維持、 他 全 redact",
        "investor": "IR-aligned のみ literal 維持、 他 全 redact",
    }

    _AUDIENCE_BODY_TEMPLATES: dict[Audience, str] = {
        "employee": (
            "全社員のみなさまへ\n\n"
            "本日、 新体制が literal 発足いたしました。 旧体制での貢献に感謝し、 統合後も"
            "現業務の継続性 + 雇用条件の維持 を literal 約束いたします。\n\n"
            "詳細は HRBP 説明会 + 社内 portal にて順次案内予定です。"
        ),
        "customer": (
            "お客様各位\n\n"
            "経営体制移行に伴い、 新体制下でも従来サービスを literal 継続いたします。"
            "サービス品質 + 契約条件は不変 + 担当窓口の連絡先も維持されます。\n\n"
            "ご不明点は担当窓口までご連絡ください。"
        ),
        "vendor": (
            "サプライヤーパートナーの皆様\n\n"
            "経営体制移行のお知らせ。 既存契約 + 取引条件 + 支払サイト は literal 継続"
            "いたします。 Change of Control 条項の確認をご依頼させていただく場合がございます。"
        ),
        "regulator": (
            "Change of Control 法定通知\n\n"
            "本日付で経営権の異動が完了いたしました。 関連法令に基づく届出書類を別途提出いたします。\n\n"
            "対象企業 + 異動内容 + 完了日 = (citation 参照)"
        ),
        "investor": (
            "経営権異動に関する IR statement\n\n"
            "本日、 経営権の移行を完遂いたしました。 統合シナジー目標 + 100 日 plan + KPI は"
            "別途 IR 資料で literal 開示予定。 株主価値向上に向け、 統合 execution を加速いたします。"
        ),
    }

    def generate_communication_body(
        self,
        audience: Audience,
        ip_summary: str,
        timing_day_n: int,
        subject: str,
        relevant_citations: list[str],
    ) -> str:
        base = self._AUDIENCE_BODY_TEMPLATES[audience]
        redaction_note = f"\n\n[redaction: {self._AUDIENCE_REDACTION_RULES[audience]}]"
        if relevant_citations:
            cit_note = f"\n[citations: {', '.join(relevant_citations[:3])}]"
        else:
            cit_note = ""
        return base + redaction_note + cit_note

    # ----- evaluate_jp_day1_hit -----

    # Stage 2 LLM augmentation: false positive 排除 + reasoning。
    # MockProvider = deterministic keyword sanity check (本番 = Claude LLM で context 評価)
    _FALSE_POSITIVE_PATTERNS: dict[str, list[str]] = {
        # axis keyword + 否定文脈 = false positive
        "union_relation": ["過去に解散", "解散済", "労組無し", "未組織"],
        "bank_relation": ["既完済", "全額返済", "保証なし"],
        "family_integration": ["創業家 退任済", "親族役員 不在"],
        "business_custom": ["内規廃止済", "外資化"],
        "trade_practice": ["全 standard 化済", "親会社保証 解除"],
    }

    def evaluate_jp_day1_hit(
        self,
        axis: JPDay1Axis,
        trigger_text: str,
        keyword_matched: str,
    ) -> tuple[bool, str]:
        # 否定 pattern catch → false positive
        for fp_pattern in self._FALSE_POSITIVE_PATTERNS.get(axis, []):
            if fp_pattern in trigger_text:
                return (
                    False,
                    f"axis={axis} keyword='{keyword_matched}' detected、 ただし false positive context"
                    f" '{fp_pattern}' literal 検出 → drop",
                )
        return (
            True,
            f"axis={axis} keyword='{keyword_matched}' = literal genuine hit (false positive pattern 不在)",
        )


def default_provider() -> LLMProvider:
    """default = MockProvider (PoC)。 受託 deploy 時 ClaudeProvider に literal swap。"""
    return MockProvider()
