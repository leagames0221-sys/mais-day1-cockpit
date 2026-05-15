"""Week 4: Vault + FastAPI app + e2e_smoke literal verify。"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

PJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PJ_ROOT))


# ----- Vault -----


@pytest.fixture
def vault_env(monkeypatch):
    """Vault 用 temp dir + VAULT_KEY env 設定 (T1/T2 inherit pattern)。"""
    from cryptography.fernet import Fernet

    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("DATA_DIR", tmp)
        monkeypatch.setenv("VAULT_KEY", Fernet.generate_key().decode())
        # reload vault module (DATA_DIR を再 evaluate)
        if "src.vault.store" in sys.modules:
            del sys.modules["src.vault.store"]
        yield Path(tmp)


def test_vault_encrypt_decrypt_roundtrip(vault_env) -> None:
    """Fernet 暗号化 + decrypt で literal 元 data 復元 (T1/T2 inherit pattern)。"""
    from src.vault import store

    data = {"name": "テスト 太郎", "phone": "090-0000-0000"}
    store.encrypt_to_vault("PN-000001", data, vault_name="plan_node_pii_test")

    retrieved = store.decrypt_from_vault("PN-000001", vault_name="plan_node_pii_test", requester="test")
    assert retrieved == data


def test_vault_returns_none_on_missing_id(vault_env) -> None:
    from src.vault import store

    result = store.decrypt_from_vault("PN-NOTEXIST", vault_name="plan_node_pii_test", requester="test")
    assert result is None


def test_vault_audit_log_emitted(vault_env) -> None:
    """全 access が audit log に literal record (vault layer 7 audit)。"""
    import json

    from src.vault import store

    store.encrypt_to_vault("PN-000002", {"x": 1}, vault_name="plan_node_pii_test")
    store.decrypt_from_vault("PN-000002", vault_name="plan_node_pii_test", requester="api")

    audit_log = vault_env / "audit" / "access_log.jsonl"
    assert audit_log.is_file()
    lines = audit_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2 # write + read
    entries = [json.loads(line) for line in lines]
    actions = {e["action"] for e in entries}
    assert "write" in actions
    assert "read" in actions


# ----- FastAPI app -----


def test_fastapi_app_imports() -> None:
    """src.api.app import literal possible (FastAPI + LangGraph + Jinja2 全 wire OK)。"""
    from src.api.app import app

    assert app.title.startswith("MAIS")


def test_fastapi_health_endpoint() -> None:
    """/health endpoint が JSON 200 OK 返却。"""
    from fastapi.testclient import TestClient
    from src.api.app import app

    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "mais-t3-day1-readiness"


def test_fastapi_landing_renders() -> None:
    """/ landing page が HTML 200 + Title literal 含む。"""
    from fastapi.testclient import TestClient
    from src.api.app import app

    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "MAIS" in r.text
    assert "Day-1" in r.text


def test_fastapi_api_generate_returns_t3output_json() -> None:
    """/api/generate が T3Output schema literal JSON 返却。"""
    from fastapi.testclient import TestClient
    from src.api.app import app

    client = TestClient(app)
    r = client.get("/api/generate")
    assert r.status_code == 200
    data = r.json()
    assert "ip_id" in data
    assert data["ip_id"].startswith("IP-")
    assert "plan_nodes" in data
    assert len(data["plan_nodes"]) == 12 # 4 dim × 3 day
    assert "dependency_edges" in data
    assert len(data["dependency_edges"]) == 8
    assert "communication_kits" in data
    assert len(data["communication_kits"]) == 5
    assert "risk_scores" in data
    assert "jp_day1_hits" in data


def test_fastapi_generate_renders_plan_view() -> None:
    """POST /generate が plan_view.html を 200 + 表 literal 含む。"""
    from fastapi.testclient import TestClient
    from src.api.app import app

    client = TestClient(app)
    r = client.post("/generate")
    assert r.status_code == 200
    assert "PlanNode" in r.text
    assert "DependencyEdge" in r.text
    assert "CommunicationKit" in r.text
    assert "中堅日本企業" in r.text


# ----- e2e smoke script structure verify (subprocess run は user runtime、 T1/T2 同 pattern) -----


def test_e2e_smoke_script_has_18_steps_structure() -> None:
    """scripts/e2e_smoke.py に 18 step pattern literal 配置 (file scan、 actual run は user-side)。"""
    e2e_path = PJ_ROOT / "scripts" / "e2e_smoke.py"
    content = e2e_path.read_text(encoding="utf-8")
    # 18 step literal 列挙確認
    for i in range(1, 19):
        assert f"Step {i}:" in content, f"Step {i} marker missing in e2e_smoke.py"
    # main + step + phase headers 存在
    assert "def main()" in content
    assert "[Phase 1:" in content
    assert "[Phase 2:" in content
    assert "[Phase 3:" in content
    assert "18/18 PASS" in content


