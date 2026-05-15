"""LangGraph state graph construction (ADR-204 DAG literal 反映、 6 軸 mitigation 設計込み)。

ADR-204 flow:
    START → ingest_t2 → detect_jp_day1 → [4 軸 parallel: organization / process / system / culture]
    → build_dependency_graph → compute_risk_scores → generate_communication_kits → finalize_t3_output → END

6 軸 mitigation 設計反映:
    - memory-only checkpoint (CVE-2026-28277 + CVE-2025-67644 不発): MemorySaver only
    - Pydantic schema (CVE-2026-44843 不発)
    - prompt code embedded (CVE-2026-34070 不発): file loading 不使用
    - JsonPlusSerializer 不使用 (GHSA-wwqv-p2pp-99h5 不発): LangGraph default のみ
    - SQLite checkpoint 不使用 (CVE-2025-67644 不発)
    - untrusted source ZERO (CVE-2025-68664 LangGrinch 不発): T2 既 redact 済 input only
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.citation.link_back import link_t2_citations_by_audience
from src.communication.generate_kits import generate_kits_for_ip
from src.dependency.compute_risk_score import compute_risk_scores_for_plan_nodes
from src.integration.ingest_t2_output import ingest_t2_output_to_ip
from src.integration.schemas import CommunicationKit, T2Output, T3Output
from src.jp_day1.llm_augment import augment_jp_day1_hits
from src.orchestrator.state import T3State
from src.planner.agents import (
    culture_agent,
    organization_agent,
    process_agent,
    system_agent,
)


def _gen_id(prefix: str) -> str:
    import secrets

    return f"{prefix}-{secrets.randbelow(10**9):06d}"


# ============================================================
# Node functions
# ============================================================


def ingest_t2_node(state: T3State) -> dict[str, Any]:
    """T2 output → IntegrationPlan + jp_day1_hits 変換 + Stage 2 LLM augmentation (ADR-202 + ADR-205)。"""
    t2: T2Output = state["t2_output"]
    industry = state.get("industry", "製造業")
    size_band = state.get("size_band", "従業員 100-300 名")
    day1_str = state.get("day1_target_date", "2026-09-01")
    day1 = date.fromisoformat(day1_str)
    ip, stage1_hits = ingest_t2_output_to_ip(t2, industry=industry, size_band=size_band, day1_target_date=day1)

    # ADR-205 Stage 2 LLM augmentation: keyword false positive 排除 + reasoning literal 蓄積
    answers_by_id = {a.answer_id: a.answer_text_redacted for a in t2.questionnaire_answers}
    kept_hits, _dropped = augment_jp_day1_hits(stage1_hits, answers_by_id)
    return {"integration_plan": ip, "jp_day1_hits": kept_hits}


def build_dependency_graph_node(state: T3State) -> dict[str, Any]:
    """4 軸 PlanNode から DependencyEdge 推論 (PoC: Day-N 順 + dimension topology heuristic)。

    Heuristic: 同 dimension 内 Day-N order = blocks edge、 cross-dimension = critical のみ blocks。
    Week 3 で LLM augmentation により literal 精度向上。
    """
    plan_nodes = state.get("plan_nodes", [])
    edges = []

    # 同 dimension 内 Day-N 順序 = blocks (Day 1 → Day 30 → Day 100)
    from collections import defaultdict

    by_dim: dict[str, list] = defaultdict(list)
    for pn in plan_nodes:
        by_dim[pn.dimension].append(pn)
    for dim, pns in by_dim.items():
        pns.sort(key=lambda p: p.day_n)
        for i in range(len(pns) - 1):
            from src.integration.schemas import DependencyEdge

            edges.append(
                DependencyEdge(
                    de_id=_gen_id("DE"),
                    from_pn=pns[i].pn_id,
                    to_pn=pns[i + 1].pn_id,
                    dep_type="blocks",
                    weight=0.8,
                    risk_score_ref=_gen_id("RS"),  # placeholder
                    rationale_redacted=f"{dim} 軸 Day-{pns[i].day_n} → Day-{pns[i + 1].day_n} order",
                )
            )

    return {"dependency_edges": edges}


def compute_risk_scores_node(state: T3State) -> dict[str, Any]:
    """各 PlanNode に対する RiskScore 算出 (ADR-203 5 dimension 内訳)。"""
    plan_nodes = state.get("plan_nodes", [])
    hits = state.get("jp_day1_hits", [])
    scores = compute_risk_scores_for_plan_nodes(plan_nodes, hits)
    return {"risk_scores": scores}


def generate_communication_kits_node(state: T3State) -> dict[str, Any]:
    """5 audience cascade CommunicationKit (Week 3 完成: LLM body 生成 + T2 Citation link back + audience-specific redaction)。"""
    ip = state["integration_plan"]
    t2: T2Output = state["t2_output"]
    # T2 Citation array を 5 audience ごとに literal split (link_t2_citations_by_audience)
    citations_by_audience = link_t2_citations_by_audience(t2)
    kits = generate_kits_for_ip(ip, citations_by_topic=citations_by_audience)
    return {"communication_kits": kits}


def finalize_t3_output_node(state: T3State) -> dict[str, Any]:
    """T3Output (T3 → T4 出力 schema、 ADR-202) を Pydantic validation 経由で literal finalize。"""
    ip = state["integration_plan"]
    out = T3Output(
        ip_id=ip.ip_id,
        plan_nodes=state.get("plan_nodes", []),
        dependency_edges=state.get("dependency_edges", []),
        communication_kits=state.get("communication_kits", []),
        risk_scores=state.get("risk_scores", []),
        jp_day1_hits=state.get("jp_day1_hits", []),
        source_t2_ddp_id=ip.source_t2_ddp_id,
        generated_at=datetime.now(timezone.utc),
        confidence=ip.confidence,
    )
    return {"t3_output": out}


# ============================================================
# Graph construction
# ============================================================


def build_t3_graph(use_checkpoint: bool = True):
    """ADR-204 DAG literal construction (memory-only checkpoint、 6 軸 mitigation 設計反映)。

    Args:
        use_checkpoint: True なら MemorySaver checkpoint active (PoC default)、
                        False なら checkpoint なし (test 高速化用)。

    Returns:
        compiled LangGraph app (invoke 可能)。
    """
    g: StateGraph = StateGraph(T3State)

    g.add_node("ingest_t2", ingest_t2_node)
    g.add_node("organization_agent", organization_agent)
    g.add_node("process_agent", process_agent)
    g.add_node("system_agent", system_agent)
    g.add_node("culture_agent", culture_agent)
    g.add_node("build_dependency_graph", build_dependency_graph_node)
    g.add_node("compute_risk_scores", compute_risk_scores_node)
    g.add_node("generate_communication_kits", generate_communication_kits_node)
    g.add_node("finalize_t3_output", finalize_t3_output_node)

    g.add_edge(START, "ingest_t2")

    # 4 軸 agent parallel: ingest_t2 → [4 軸] (LangGraph 自動 parallel)
    for axis_node in (
        "organization_agent",
        "process_agent",
        "system_agent",
        "culture_agent",
    ):
        g.add_edge("ingest_t2", axis_node)
        g.add_edge(axis_node, "build_dependency_graph")

    g.add_edge("build_dependency_graph", "compute_risk_scores")
    g.add_edge("compute_risk_scores", "generate_communication_kits")
    g.add_edge("generate_communication_kits", "finalize_t3_output")
    g.add_edge("finalize_t3_output", END)

    if use_checkpoint:
        # memory-only checkpoint (ADR-204 6 軸 mitigation literal 反映、 SQLite/Persist 不使用)
        checkpointer = MemorySaver()
        return g.compile(checkpointer=checkpointer)
    return g.compile()
