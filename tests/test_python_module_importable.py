"""真 issue #1 fix 後 verification: src/ + 11 subdir が Python module として import 可能。

T3 Tier 2 CLAUDE.md + systemPatterns.md で literal 主張済の
`python -m src.<module>.<entry>` path が動作する (= __init__.py 12 file 全 配置済) を保証。
"""
from __future__ import annotations
import importlib
from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PJ_ROOT / "src"


def test_src_init_py_exists() -> None:
    """src/__init__.py literal 配置 (T2 commit history と同 pattern)。"""
    assert (SRC_ROOT / "__init__.py").is_file(), "src/__init__.py missing"


def test_all_11_subdir_have_init_py() -> None:
    """11 subdir 全 __init__.py 配置確認。"""
    expected_subdirs = [
        "orchestrator",
        "planner",
        "dependency",
        "communication",
        "integration",
        "jp_day1",
        "pipeline",
        "citation",
        "vault",
        "operational",
        "api",
    ]
    for subdir in expected_subdirs:
        init_path = SRC_ROOT / subdir / "__init__.py"
        assert init_path.is_file(), f"src/{subdir}/__init__.py missing"


def test_src_importable_as_python_package() -> None:
    """`python -m src.<module>.<entry>` が動作する前提 = src import OK。"""
    import sys
    sys.path.insert(0, str(PJ_ROOT))
    try:
        spec = importlib.util.find_spec("src")
        assert spec is not None, "src module not found"
    finally:
        sys.path.pop(0)


def test_all_11_submodules_importable() -> None:
    """11 subdir 全 module として import 可能。"""
    import sys
    sys.path.insert(0, str(PJ_ROOT))
    try:
        expected_modules = [
            "src.orchestrator",
            "src.planner",
            "src.dependency",
            "src.communication",
            "src.integration",
            "src.jp_day1",
            "src.pipeline",
            "src.citation",
            "src.vault",
            "src.operational",
            "src.api",
        ]
        for mod_name in expected_modules:
            spec = importlib.util.find_spec(mod_name)
            assert spec is not None, f"module not importable: {mod_name}"
    finally:
        sys.path.pop(0)
