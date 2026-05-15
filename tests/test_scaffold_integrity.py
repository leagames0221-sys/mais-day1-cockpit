"""scaffold integrity tests — 14 base file + internal knowledge base 5 + .gitignore + requirements + ADR citation markers literal verify。"""
from __future__ import annotations
import re
from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent


def test_14_base_scaffold_files_exist() -> None:
    """T3 scaffold 14 base file 全 file system literal 存在。"""
    expected = [
        ".gitignore",
        "CLAUDE.md",
        "README.md",
        "pytest.ini",
        "requirements-week0.txt",
        ".github/dependabot.yml",
        ".github/workflows/drift-check.yml",
        ".github/workflows/pip-audit.yml",
        "(internal config)/internal_kb/productContext.md",
        "(internal config)/internal_kb/activeContext.md",
        "(internal config)/internal_kb/decisionLog.md",
        "(internal config)/internal_kb/systemPatterns.md",
        "(internal config)/internal_kb/logbook.md",
        "docs/discovery_brief.md",
    ]
    for rel in expected:
        assert (PJ_ROOT / rel).is_file(), f"scaffold missing: {rel}"


def test_internal_kb_5_file_complete() -> None:
    """doctrine: handoff-duty 順守、 internal knowledge base 5 file 完備。"""
    for name in ("productContext", "activeContext", "decisionLog", "systemPatterns", "logbook"):
        path = PJ_ROOT / ".claude" / "internal_kb" / f"{name}.md"
        assert path.is_file(), f"internal_kb/{name}.md missing"
        assert path.stat().st_size > 100, f"internal_kb/{name}.md is empty / stub"


def test_gitignore_heartbeat_literal_exclude() -> None:
    """T2 学び doctrine: analogical-recall: heartbeat path literal exclude。"""
    gi = (PJ_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "(internal config)/*.heartbeat" in gi, "heartbeat exclude missing (T2 真 bug 再発 risk)"
    assert "(internal config)/*.jsonl" in gi, "jsonl exclude missing (T2 telemetry stage 漏れ risk)"
    assert ".env" in gi, ".env credential exclude missing (Security Master Layer 1)"
    assert ".vendor/" in gi, ".vendor/ exclude missing (216MB binary)"
    assert "out_video/" in gi, "out_video/ exclude missing (video pipeline output)"


def test_requirements_week0_pep508_parse_ok() -> None:
    """requirements-week0.txt の PEP 508 syntax literal parse OK + 6 package 期待値。"""
    raw = (PJ_ROOT / "requirements-week0.txt").read_text(encoding="utf-8")
    lines = [line.strip() for line in raw.splitlines() if line.strip() and not line.strip().startswith("#")]
    pkg_names = [re.split(r"[<>=!~]", line)[0].strip() for line in lines]
    expected_set = {"faker", "python-dotenv", "pytest", "pytest-cov", "pydantic", "pip-audit"}
    assert set(pkg_names) == expected_set, f"requirements-week0 mismatch: {pkg_names}"
    # pytest >= 9.0.3 (CVE-2025-71176 fix) literal verify
    pytest_line = next(line for line in lines if line.startswith("pytest>="))
    assert "9.0.3" in pytest_line, "pytest CVE-2025-71176 fix version missing"


def test_adr_008_citation_marker_count() -> None:
    """drift-check step 4: internal ADR (mais-deal-matching) citation reference 1 件以上 hit。"""
    hits = 0
    targets = [
        PJ_ROOT / "CLAUDE.md",
        PJ_ROOT / "README.md",
        *(PJ_ROOT / ".claude" / "internal_kb").glob("*.md"),
        *(PJ_ROOT / "docs").glob("*.md"),
    ]
    for f in targets:
        if f.is_file():
            hits += f.read_text(encoding="utf-8").count("mais-deal-matching")
    assert hits >= 5, f"internal ADR citation marker too few: {hits}"


def test_t2_sibling_citation_marker_count() -> None:
    """drift-check step 5: T2 sibling (mais-dd-workbench) citation 1 件以上 hit。"""
    hits = 0
    targets = [
        PJ_ROOT / "CLAUDE.md",
        PJ_ROOT / "README.md",
        *(PJ_ROOT / ".claude" / "internal_kb").glob("*.md"),
        *(PJ_ROOT / "docs").glob("*.md"),
    ]
    for f in targets:
        if f.is_file():
            hits += f.read_text(encoding="utf-8").count("mais-dd-workbench")
    assert hits >= 5, f"T2 sibling citation marker too few: {hits}"


def test_video_pipeline_cross_pj_citation() -> None:
    """drift-check step 6: video-pipeline cross-PJ SSoT citation。"""
    hits = 0
    targets = [
        PJ_ROOT / "CLAUDE.md",
        PJ_ROOT / "README.md",
        *(PJ_ROOT / ".claude" / "internal_kb").glob("*.md"),
        *(PJ_ROOT / "docs").glob("*.md"),
    ]
    for f in targets:
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            hits += text.count("video-pipeline") + text.count("TTS engine")
    assert hits >= 5, f"video-pipeline / TTS engine citation too few: {hits}"
