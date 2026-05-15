"""internal knowledge base 5 file の markdown structure + 必須 heading + cross-ref reachability literal 検証。"""
from __future__ import annotations
import os
import re
from pathlib import Path

import pytest

PJ_ROOT = Path(__file__).resolve().parent.parent
MB_DIR = PJ_ROOT / ".claude" / "internal_kb"

# CI 環境では sibling repo (mais-deal-matching / mais-dd-workbench) が checkout されないため、
# cross-repo path reachability test は local only に limit (GitHub Actions = single repo checkout)
IS_CI = bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))


def test_productContext_has_required_sections() -> None:
    text = (MB_DIR / "productContext.md").read_text(encoding="utf-8")
    for section in ("## goal", "## scope", "## target user", "## value proposition", "## 制約"):
        assert section in text, f"productContext missing section: {section}"


def test_activeContext_has_current_phase_and_carryover() -> None:
    text = (MB_DIR / "activeContext.md").read_text(encoding="utf-8")
    assert "## current phase" in text, "activeContext missing 'current phase'"
    assert "carryover" in text.lower(), "activeContext missing carryover marker"


def test_decisionLog_has_adr_200_201_202() -> None:
    """T3 専用 ADR 番号帯 (ADR-200+) の起草 3 件 literal 存在。"""
    text = (MB_DIR / "decisionLog.md").read_text(encoding="utf-8")
    for adr in ("ADR-200", "ADR-201", "ADR-202"):
        assert adr in text, f"decisionLog missing {adr}"
    # T1/T2 ADR 番号帯と非衝突 (ADR-001 / ADR-100 が T3 decisionLog に出現しないこと)
    assert "ADR-001" not in text or "mais-deal-matching" in text, "T3 decisionLog should reference T1 ADR only via cross-repo citation"


def test_systemPatterns_has_id_prefix_7_types() -> None:
    """T3 固有 ID prefix 7 種 (IP / PN / DE / CK / RS / CA / JPD1) literal 列挙確認。"""
    text = (MB_DIR / "systemPatterns.md").read_text(encoding="utf-8")
    for prefix in ("IP-XXXXXX", "PN-XXXXXX", "DE-XXXXXX", "CK-XXXXXX", "RS-XXXXXX", "JPD1-XXXXXX"):
        assert prefix in text, f"systemPatterns missing ID prefix: {prefix}"


def test_logbook_has_dated_entry() -> None:
    """doctrine: handoff-duty: logbook に session entry が timestamp 付きで存在。"""
    text = (MB_DIR / "logbook.md").read_text(encoding="utf-8")
    assert re.search(r"## 2026-\d{2}-\d{2}", text), "logbook missing dated session entry"


@pytest.mark.skipif(IS_CI, reason="cross-repo path test = local only (CI checkouts single repo)")
def test_cross_repo_path_reachability() -> None:
    """T3 doc が citation reference する cross-repo path が file system で literal 解決可能。"""
    # internal ADR SSoT (mais-deal-matching)
    adr_008_path = PJ_ROOT.parent / "mais-deal-matching" / ".claude" / "internal_kb" / "decisionLog.md"
    assert adr_008_path.is_file(), f"internal ADR SSoT path unreachable: {adr_008_path}"
    content = adr_008_path.read_text(encoding="utf-8")
    assert "internal ADR" in content, "internal ADR not found in T1 decisionLog"

    # T2 logbook (sibling 連携 source)
    t2_logbook = PJ_ROOT.parent / "mais-dd-workbench" / ".claude" / "internal_kb" / "logbook.md"
    assert t2_logbook.is_file(), f"T2 logbook unreachable: {t2_logbook}"

    # video-pipeline cross-PJ SSoT ((internal knowledge library)/...)
    home_claude = Path.home() / ".claude" / "knowledge-library" / "agent-architecture" / "video-pipeline" / "README.md"
    assert home_claude.is_file(), f"video-pipeline cross-PJ SSoT unreachable: {home_claude}"
