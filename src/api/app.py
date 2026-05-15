"""T3 FastAPI Web UI (Week 4 PoC demo、 5 endpoint minimal、 Jinja2 templates)。

 済 stack literal reuse。
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.integration.schemas import Answer, Citation, JPPattern, T2Output
from src.orchestrator.build_state_graph import build_t3_graph

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="MAIS / T3 Day-1 Readiness Plan Generator")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Compile LangGraph once at startup
_t3_app = build_t3_graph(use_checkpoint=False)


def _build_demo_t2() -> T2Output:
    """PoC demo: 合成 T2 output (実 PII ZERO、 合成データ only literal)。"""
    return T2Output(
        ddp_id="DDP-000999",
        citations=[
            Citation(
                citation_id="CIT-000001", answer_id="A-000001", chunk_id="CHK-000001",
                doc_id="DOC-000001", page=12, snippet="従業員 + 役員配置の継続条件",
                confidence=0.87,
            ),
            Citation(
                citation_id="CIT-000002", answer_id="A-000002", chunk_id="CHK-000002",
                doc_id="DOC-000002", page=3, snippet="主要取引銀行へのコミットメント",
                confidence=0.92,
            ),
        ],
        jp_patterns_hits=[
            JPPattern(jpp_id="JPP-000001", pattern_type="family_governance", severity="high",
                      chunk_refs=["CHK-000001"]),
        ],
        questionnaire_answers=[
            Answer(answer_id="A-000001", question_id="Q-000001",
                   answer_text_redacted="主要取引銀行と労働組合への事前協議が必要",
                   citation_array=["CIT-000001", "CIT-000002"], confidence=0.9),
        ],
    )


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request) -> Any:
    return TEMPLATES.TemplateResponse(
        request=request,
        name="landing.html",
        context={"title": "MAIS / T3 Day-1 Readiness Plan Generator"},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mais-t3-day1-readiness", "version": "0.4.0"}


@app.post("/generate", response_class=HTMLResponse)
async def generate_plan(request: Request) -> Any:
    """PoC demo: 合成 T2 output → T3 IntegrationPlan + 全 deliverable literal 生成。"""
    t2 = _build_demo_t2()
    final_state = _t3_app.invoke(
        {
            "t2_output": t2,
            "industry": "製造業",
            "size_band": "従業員 100-300 名",
            "day1_target_date": "2026-09-01",
        },
        config={"configurable": {"thread_id": "demo-1"}},
    )
    out = final_state["t3_output"]
    return TEMPLATES.TemplateResponse(
        request=request,
        name="plan_view.html",
        context={
            "ip": {
                "ip_id": out.ip_id,
                "source_t2_ddp_id": out.source_t2_ddp_id,
                "confidence": out.confidence,
            },
            "plan_nodes": out.plan_nodes,
            "dependency_edges": out.dependency_edges,
            "communication_kits": out.communication_kits,
            "risk_scores": out.risk_scores,
            "jp_day1_hits": out.jp_day1_hits,
        },
    ) # noqa: E501


@app.get("/api/generate")
async def generate_plan_json() -> Any:
    """JSON API: T3 demo run の literal full output (T3Output schema 順守)。"""
    t2 = _build_demo_t2()
    final_state = _t3_app.invoke(
        {
            "t2_output": t2,
            "industry": "製造業",
            "size_band": "従業員 100-300 名",
            "day1_target_date": "2026-09-01",
        },
        config={"configurable": {"thread_id": "demo-api-1"}},
    )
    out = final_state["t3_output"]
    return JSONResponse(content=out.model_dump(mode="json"))
