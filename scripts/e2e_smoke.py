"""T3 e2e smoke (18 step pattern、 T1/T2 inherit + ADR-204 全 layer literal verify)。

Usage: python -m scripts.e2e_smoke

各 step PASS/FAIL を print、 全 PASS で exit 0、 fail で exit 1。
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

PJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PJ_ROOT))

# Windows cp932 default encoding 防御 (security_intercept.py 同 pattern、 cross-PJ universal)
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and getattr(_stream, "encoding", "").lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from src.dependency.compute_risk_score import (
    build_plan_node_graph,
    detect_cycles,
    topological_critical_path,
)
from src.integration.ingest_t2_output import (
    aggregate_severity,
    ingest_t2_output_to_ip,
    map_jp_pattern_to_axes,
)
from src.integration.schemas import (
    Answer,
    Citation,
    JPPattern,
    T2Output,
    T3Output,
)
from src.orchestrator.build_state_graph import build_t3_graph

PASSED = 0
FAILED = 0


def step(name: str, ok: bool, detail: str = "") -> None:
    global PASSED, FAILED
    status = "✅" if ok else "❌"
    print(f"  {status} {name}{' — ' + detail if detail else ''}")
    if ok:
        PASSED += 1
    else:
        FAILED += 1


def main() -> int:
    print("=== T3 e2e smoke (18 step、 ADR-204 全 layer literal verify) ===\n")

    # Step 1: 合成 T2Output schema 構築
    print("[Phase 1: input fixture]")
    t2 = T2Output(
        ddp_id="DDP-000999",
        citations=[
            Citation(citation_id="CIT-000001", answer_id="A-000001", chunk_id="CHK-000001",
                     doc_id="DOC-000001", page=12, snippet="従業員 + 役員配置", confidence=0.87),
            Citation(citation_id="CIT-000002", answer_id="A-000002", chunk_id="CHK-000002",
                     doc_id="DOC-000002", page=3, snippet="主要取引銀行コミットメント", confidence=0.92),
        ],
        jp_patterns_hits=[
            JPPattern(jpp_id="JPP-000001", pattern_type="family_governance", severity="high",
                      chunk_refs=["CHK-000001"]),
        ],
        questionnaire_answers=[
            Answer(answer_id="A-000001", question_id="Q-000001",
                   answer_text_redacted="主要取引銀行への報告と労働組合への事前協議が必要",
                   citation_array=["CIT-000001", "CIT-000002"], confidence=0.9),
        ],
    )
    step("Step 1: T2Output schema instantiate", t2.ddp_id == "DDP-000999", f"DDP-id={t2.ddp_id}")

    # Step 2: T2 → T3 ingestion (ADR-202)
    print("\n[Phase 2: ingestion + jp_day1 trigger (ADR-202 + ADR-205)]")
    ip, jp_hits = ingest_t2_output_to_ip(
        t2, industry="製造業", size_band="100-300 名", day1_target_date=date(2026, 9, 1)
    )
    step("Step 2: T2 → IntegrationPlan 変換", ip.source_t2_ddp_id == "DDP-000999", f"IP={ip.ip_id}")

    # Step 3: jp_day1 trigger mapping
    family_int = [h for h in jp_hits if h.axis == "family_integration"]
    step("Step 3: family_governance → family_integration trigger",
         len(family_int) >= 1, f"{len(family_int)} hit")

    union = [h for h in jp_hits if h.axis == "union_relation"]
    step("Step 4: 労働組合 keyword → union_relation trigger", len(union) >= 1, f"{len(union)} hit")

    bank = [h for h in jp_hits if h.axis == "bank_relation"]
    step("Step 5: 主要取引銀行 keyword → bank_relation trigger", len(bank) >= 1, f"{len(bank)} hit")

    # Step 6: severity aggregate
    step("Step 6: aggregate_severity (high)", aggregate_severity(jp_hits) == "high",
         f"max={aggregate_severity(jp_hits)}")

    # Step 7: map_jp_pattern_to_axes literal
    axes = map_jp_pattern_to_axes("nominal_shares")
    step("Step 7: nominal_shares → dual axis mapping",
         set(axes) == {"family_integration", "bank_relation"}, str(axes))

    # Step 8-14: LangGraph e2e
    print("\n[Phase 3: LangGraph state graph e2e (ADR-204 全 6 軸 mitigation active)]")
    app = build_t3_graph(use_checkpoint=False)
    step("Step 8: LangGraph DAG compile", app is not None, "build_t3_graph success")

    final_state = app.invoke(
        {"t2_output": t2, "industry": "製造業", "size_band": "100-300 名",
         "day1_target_date": "2026-09-01"},
        config={"configurable": {"thread_id": "e2e-smoke"}},
    )
    out = final_state["t3_output"]
    step("Step 9: e2e invoke returns T3Output", isinstance(out, T3Output), "T3Output literal returned")

    step("Step 10: 12 PlanNode (4 dim × Day 1/30/100)", len(out.plan_nodes) == 12,
         f"{len(out.plan_nodes)} nodes")

    dims = {pn.dimension for pn in out.plan_nodes}
    step("Step 11: 4 dimensions all covered",
         dims == {"organization", "process", "system", "culture"}, ", ".join(sorted(dims)))

    step("Step 12: 8 DependencyEdge (4 dim × 2 transitions)", len(out.dependency_edges) == 8,
         f"{len(out.dependency_edges)} edges")

    step("Step 13: 12 RiskScore (each PlanNode 5 dim)", len(out.risk_scores) == 12,
         f"{len(out.risk_scores)} scores")

    step("Step 14: 5 CommunicationKit (5 audience cascade)", len(out.communication_kits) == 5,
         ", ".join(sorted({k.audience for k in out.communication_kits})))

    # Step 15: LLM augment (genuine reasoning literal 蓄積)
    print("\n[Phase 4: LLM augmentation + dependency graph (Week 3 + Week 2 layer)]")
    genuine_count = sum(1 for h in out.jp_day1_hits if "genuine" in h.mitigation_recommendation_redacted)
    step("Step 15: Stage 2 LLM augment reasoning 蓄積",
         genuine_count >= 1, f"{genuine_count} genuine hits")

    # Step 16: NetworkX dependency graph
    g = build_plan_node_graph(out.plan_nodes, out.dependency_edges)
    step("Step 16: NetworkX graph 構築",
         g.number_of_nodes() == 12 and g.number_of_edges() == 8,
         f"{g.number_of_nodes()} nodes / {g.number_of_edges()} edges")

    # Step 17: cycle detection (DAG verify)
    cycles = detect_cycles(g)
    step("Step 17: cycle 不在 (DAG literal verify)", len(cycles) == 0, f"{len(cycles)} cycles")

    # Step 18: topological sort
    try:
        order = topological_critical_path(g)
        step("Step 18: topological sort literal possible",
             len(order) == 12, f"{len(order)} nodes ordered")
    except Exception as e:
        step("Step 18: topological sort", False, str(e))

    # Summary
    print(f"\n=== e2e smoke: {PASSED} PASS / {FAILED} FAIL ===")
    if FAILED > 0:
        print("❌ e2e smoke FAILED")
        return 1
    print("✅ e2e smoke 18/18 PASS literal 全 green ★★★")
    return 0


if __name__ == "__main__":
    sys.exit(main())
