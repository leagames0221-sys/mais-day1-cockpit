"""drift-check.yml CI 8 step を local literal replicate。

CI で 1 round、 本 test で local 2 round = doctrine: verify-priority 順守 (file system check + automation test)。
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent


def test_step1_internal_kb_5_file() -> None:
    """CI step 1 replicate: internal knowledge base 5 file 存在。"""
    for name in ("productContext", "activeContext", "decisionLog", "systemPatterns", "logbook"):
        assert (PJ_ROOT / ".claude" / "internal_kb" / f"{name}.md").is_file()


def test_step2_tier2_claude_md() -> None:
    """CI step 2 replicate: Tier 2 CLAUDE.md 存在。"""
    assert (PJ_ROOT / "CLAUDE.md").is_file()


def test_step3_readme_literal_file_refs_exist() -> None:
    """CI step 3 replicate: README が言及した literal file が実在。"""
    for rel in ("requirements-week0.txt", "docs/discovery_brief.md", ".github/dependabot.yml"):
        assert (PJ_ROOT / rel).is_file(), f"README literal ref missing: {rel}"


def test_step4_adr008_citation_marker_grep() -> None:
    """CI step 4 replicate: mais-deal-matching grep が CLAUDE/README/internal_kb/docs で 1 件以上 hit。"""
    found = False
    for root in (PJ_ROOT / "CLAUDE.md", PJ_ROOT / "README.md", PJ_ROOT / ".claude" / "internal_kb", PJ_ROOT / "docs"):
        if root.is_file():
            if "mais-deal-matching" in root.read_text(encoding="utf-8"):
                found = True
                break
        elif root.is_dir():
            for f in root.rglob("*.md"):
                if "mais-deal-matching" in f.read_text(encoding="utf-8"):
                    found = True
                    break
            if found:
                break
    assert found, "internal ADR mais-deal-matching citation marker absent"


def test_step5_t2_sibling_citation_marker_grep() -> None:
    """CI step 5 replicate: mais-dd-workbench grep。"""
    found = False
    for root in (PJ_ROOT / "CLAUDE.md", PJ_ROOT / "README.md", PJ_ROOT / ".claude" / "internal_kb", PJ_ROOT / "docs"):
        if root.is_file():
            if "mais-dd-workbench" in root.read_text(encoding="utf-8"):
                found = True
                break
        elif root.is_dir():
            for f in root.rglob("*.md"):
                if "mais-dd-workbench" in f.read_text(encoding="utf-8"):
                    found = True
                    break
            if found:
                break
    assert found, "T2 sibling citation absent"


def test_step6_video_pipeline_citation_grep() -> None:
    """CI step 6 replicate: video-pipeline / TTS engine grep。"""
    found = False
    pattern = re.compile(r"(video-pipeline|TTS engine)")
    for root in (PJ_ROOT / "CLAUDE.md", PJ_ROOT / "README.md", PJ_ROOT / ".claude" / "internal_kb", PJ_ROOT / "docs"):
        if root.is_file():
            if pattern.search(root.read_text(encoding="utf-8")):
                found = True
                break
        elif root.is_dir():
            for f in root.rglob("*.md"):
                if pattern.search(f.read_text(encoding="utf-8")):
                    found = True
                    break
            if found:
                break
    assert found, "video-pipeline / TTS engine citation absent"


def test_step7_pii_boundary_no_field_names_in_disallowed_modules() -> None:
    """CI step 7 replicate: 11 src 中 7 module (orchestrator/planner/dependency/communication/pipeline/operational/citation) に PII field 名 literal 出現禁止。"""
    forbidden = re.compile(
        r"(name_full|email|phone|address_full|raw_self_intro|raw_description|name_kana|"
        r"dob_exact|contact_email|contact_phone|contact_person|raw_text|employee_name|vendor_contact)"
    )
    disallowed_modules = ["orchestrator", "planner", "dependency", "communication", "pipeline", "operational", "citation"]
    for mod in disallowed_modules:
        for py in (PJ_ROOT / "src" / mod).rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            match = forbidden.search(text)
            assert not match, f"PII field literal in {py}: {match.group(0) if match else ''}"


def test_step8_pip_audit_disable_pip_flag_absent() -> None:
    """CI step 8 replicate: pip-audit.yml の run: 行で --disable-pip flag が actual command として使われていない。

    T2 commit 76eb283 で literal fix 済 pattern の literal 再発防止 mechanism。
    self-referential false positive 回避: pip-audit.yml の run: 行のみ scan、 comment + verify step は exclude。
    """
    pip_audit_yml = (PJ_ROOT / ".github" / "workflows" / "pip-audit.yml").read_text(encoding="utf-8")
    actual_pattern = re.compile(r"^\s*run:.*pip-audit.*--disable-pip", re.MULTILINE)
    assert actual_pattern.search(pip_audit_yml) is None, (
        "T2 真 bug 再発: pip-audit --disable-pip flag が actual command として検出"
    )


def test_step9_pytest_collectable() -> None:
    """CI step 9 replicate: pytest collect 自体が動作する。

    sys.executable を literal 使用 (venv 経由実行で langgraph 等 import OK)、
    system Python (venv 外) では LangGraph 未 install で collect fail risk。
    """
    import sys as _sys

    result = subprocess.run(
        [_sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/"],
        cwd=PJ_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"pytest collect failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "test" in result.stdout.lower(), "no test collected"
