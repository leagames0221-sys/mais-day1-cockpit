# T3 Discovery Brief — MAIS / T3 Day-1 readiness plan generator

> Spec-Driven Workflow Stage 1 (Discovery) deliverable。
> user gate 通過済 (2026-05-13、 4 軸 + stack 7 件 OK 受領)。 本 brief 確定後 Stage 2 (Requirements) 移行。

---

## 1. PJ Identity (sibling 位置付け)

- **scope**: M&A advisory engagement 提案 § T3 application — **M&A 成約後 Day-1 統合 100 日計画自動生成 AI** PoC 試作
- **target**: プレゼン demo ready、 4 週で動く版完成
- **移植先**: client infrastructure (後日)、 本 repo は試作 only
- **sibling**: mais-deal-matching (T1 マッチング、 完成度 100%) + mais-dd-workbench (T2 DD 自動化、 完成度 100%) と MAIS ecosystem 共通基盤 (internal ADR) を citation reference で literal 共有
- **3rd sibling 位置付け**: T2 の API output (Citation array + jp_patterns hit + 質問票回答) を T3 が入力として literal 流用、 「DD → Day-1」 というoriginal proposal § 5-3 優先順位 (T2 → T3) に literal 順守

## 2. 機密度 + 取扱方針

- **PII**: 合成 M&A 案件 data only、 実 M&A 契約書 / 実買収案件 / 実従業員情報は literal 一切扱わない
- **credential**: ANTHROPIC_API_KEY のみ (.env、 gitignore 必須、 Week 2 LLM call phase で active 化、 試作期間中は MockProvider で API key 不要)
- **doctrine: sandbox-check**: 試作 scope + 合成データ only のため host PC OK (real M&A Day-1 案件投入時に Docker / sandbox 化必須)

## 3. 採用 stack 7 件 (doctrine: prior-art-first + doctrine: external-source-audit 順守、 Week 1 audit gate 通過後 active)

| # | ひな形 | license | 役割 | red flag | tier |
|---|---|---|---|---|---|
| ① | **LangGraph 0.3.x** (default) | MIT | DAG-based 4 軸統合 plan generator orchestrator (organization / process / system / culture)、 stateful checkpointing で iteration 可能 | LangChain ecosystem 2024-2025 advisory 履歴、 pin version + Dependabot 必須 | ★★★ (Week 1 audit + pip-audit 通過後 active) |
| ② | **Pydantic AI** (fallback) | MIT | LangGraph red flag 検出時の literal 切替先 (type-safe + MCP-native) | 同上 | ★★ fallback |
| ③ | **NetworkX 3.x** | BSD-3 | system 統合 dependency graph + topological sort + critical path + cyclic 検出 | 25 年 OSS、 advisory 0 件 | ★★★ |
| ④ | T1/T2 既存 **LLMProvider Protocol + LlamaIndex CitationQueryEngine** | MIT + Apache-2.0 | communication kit draft (5 audience) + Citation link back | (既存 audit 済) | ★★★ inherited |
| ⑤ | T1/T2 既存 **5-stage hybrid pipeline** (sentence-transformers + faiss-cpu + rank-bm25 + cross-encoder) | mixed (Apache-2.0 中心) | 過去 PMI 失敗事例 surface (T5 Ontology layer 先取り) | (既存 audit 済) | ★★★ inherited |
| ⑥ | **TTS engine-Engine 1.2.0 + Playwright + ffmpeg + auto-sync** (cross-PJ universal SSoT 経由) | LGPL-3.0 / Apache-2.0 / LGPL | 機能紹介動画 (T1/T2 で literal 完成済) | engine binary は T2 `.vendor/aivis-engine/` literal 共有 (port 10101) | ★★★ inherited |
| ⑦ | MAIS 自作 **中堅日本企業 Day-1 文化 fit detector 5 軸** | MAIS 内部 | 組合対応 / 取引銀行折衝 / 同族統合 / 商習慣 / 取引慣行 (original proposal § T3 末尾 literal 主張点 = 競合優位 core) | new、 ゼロ生成立証責任ここに literal 集中 | new (T3 専用) |

## 4. 2026.5 deeper scan 結論

### Day-1 plan template 構造 — decomposed prior art として inherit

OSS 「1:1 一致」 Day-1 generator は **literal ZERO** (GitHub / PyPI 全 scan、 2 round)。 商用 / コンサル提供のみ (top-tier consulting firm X / top-tier PMI advisor / Dealroom / Midaxo / Deloitte / Korn Ferry / NMS / M&A Science / MergerIntegration.com)。 業界 standard 構造 (4 audience × phase × message + 4 軸統合 + dependency graph) は **decomposed prior art** として literal inherit、 文言は MAIS 自作。

### agentic workflow framework 2026.5 SOTA

**LangGraph 0.3.x = enterprise default** (Klarna / Uber / JPMorgan / BlackRock / LinkedIn / Cisco / Elastic / Replit literal verified、 stateful DAG + checkpoint replay + parallel execution)。 **Pydantic AI = type-safe fallback** (Week 1 audit で LangGraph red flag 検出時 literal 切替、 MCP-native)。 Microsoft Agent Framework v1.0 (2026-04 GA) は新規すぎ、 Google ADK / OpenAI Agents SDK は cloud credential 強制依存で user 制約違反、 不採用。

### MCP future-proof path

2026 で MCP-native framework 群 (Pydantic AI / OpenAI Agents SDK / Google ADK / Claude Agent SDK / mcp-agent) が emergence、 tool integration が framework swap 不要に。 T3 PoC = LangGraph internal call、 **ADR-204 で 「受託案件移植時 MCP server 化 path」 を foundation に literal 確保** (doctrine: future-proof 順守、 rewrite cost ZERO)。

## 5. internal ADR 共通 doctrine 6 component inherit (citation reference のみ、 重複起草禁止)

1. brand identity — MAIS / T3 Day-1、 黒金 / Noto Serif JP / 年輪 SVG / tagline 「経営の責務を、 次の人へ。」
2. visual identity — 金 (`#d4af37` 等) × 黒、 motif + layout literal 不変
3. data 共通 doctrine — 会員制 two-sided + **PII/Op 分離** (T3 PII = 統合対象企業の連絡先・人事 PII、 Op = redact 済 plan node / synergy KPI / dependency edge) + 7-layer security
4. AI pipeline 共通 doctrine — 5-stage hybrid + LLMProvider Protocol (T3 = Day-1 plan retrieval + 過去 PMI 失敗事例 surface)
5. 動画 pipeline 共通 doctrine — TTS engine まお おちついた + auto-sync + 90s timeout (cross-PJ universal SSoT、 2026-05-13 完成)
6. infra / drift 防止 共通 doctrine — drift CI + pip-audit + Dependabot + e2e_smoke + internal knowledge base 5 file

## 6. T3 固有拡張 (ADR-200+、 重複起草禁止)

- **ADR-200**: T3 PJ scope 確定 (本 brief literal 反映、 完了)
- **ADR-201**: 採用 OSS 6 件 audit + Week 1 requirements (EARS 形式)
- **ADR-202**: T2 → T3 入出力契約 schema (Citation array + jp_patterns hit + 質問票回答 流用、 起草済 proposed status)
- **ADR-203**: T3 Object Type 6 件 (`IntegrationPlan` / `PlanNode` / `DependencyEdge` / `CommunicationKit` / `RiskScore` / `JPDay1Pattern`、 internal ADR § 3 PII/Op 分離 pattern 適用)
- **ADR-204**: LangGraph state graph 設計 (4 軸 agent + checkpoint replay + iteration + MCP future-proof path)
- **ADR-205**: 中堅日本企業 Day-1 文化 fit detector 5 軸 pattern library (組合対応 / 取引銀行折衝 / 同族統合 / 商習慣 / 取引慣行)
- (以降は実装中に literal 起草)

## 7. 4 週 PoC roadmap

| Week | 着手 task | deliverable |
|---|---|---|
| **Week 0** | GitHub PRIVATE repo 作成 + scaffold 全 file + drift CI / pip-audit / Dependabot active + ADR-200/201/202 起草 | green CI / internal knowledge base 5 file / 本 Discovery brief literal 採択 |
| **Week 1** | 採用 6 stack audit (LangGraph red flag scan + pip-audit + repo activity) + Requirements (EARS) + Object Type 6 件 ADR-203 + Design File Structure Plan | ADR-201/202/203 / `src/` 11 module dir + `tests/` |
| **Week 2** | LangGraph state graph 実装 (4 軸 agent: organization / process / system / culture) + NetworkX dependency graph + risk score + T2 API output 流用 ingestion | ADR-204 / 4 agent + dependency graph generator literal 動作 + smoke test |
| **Week 3** | Communication kit 生成 (5 audience cascade: 従業員 / 顧客 / vendor / 規制当局 / 投資家、 LLM + Citation array) + 中堅日本企業 fit detector (5 軸) | ADR-205 / kit draft 5 種 + jp_day1_pattern hit literal |
| **Week 4** | 動画 pipeline literal 適用 (cross-PJ SSoT 経由、 TTS engine まお おちついた、 T3 16 scene 程度) + e2e_smoke + UI / API 整備 + プレゼン demo | `out_video/mais_mantle_demo.mp4` (T3) + e2e_smoke 18 step PASS + プレゼン ready |

## 8. T2 → T3 入出力契約 (sibling 連携 literal 設計、 ADR-202 reference)

T2 (DD 自動化) の literal 完成 API output:
- **Citation array** (DDP / DOC / CHK / Q / A / CIT prefix)
- **jp_patterns hit** (中堅 fit pattern: 同族経営 / 名義株 / オーナー私的経費)
- **質問票回答** (DD Question 数百項目への構造化回答)

T3 が **入力として literal 流用**:
- DD 結果 → integration plan の **risk score 入力** (jp_patterns hit が 5 軸 jp Day-1 detector の trigger)
- 質問票回答 → Day-1 plan node の **dependency edge weight**
- Citation array → communication kit の **source link back**

→ T2 と T3 は **MAIS Ontology 共通基盤** で literal 連携 (original proposal line 310 「PMI Ontology を共通基盤として共有する AIP application 群」 順守)。

## 9. 制約 (T1/T2 と同)

- ✅ 無料 + クレカ不要範囲のみ
- ✅ 合成データ only (実 M&A 案件 literal 不在)
- ✅ consumer laptop 完走前提 (doctrine: consumer-hw)
- ✅ ADR-200+ で T3 固有起草、 internal ADR 重複禁止
- ✅ T2 API output literal 流用設計

## 10. 受託 deploy 前 ★★★ 化 残 task (T1/T2/T3 共通、 後日)

- TTS engine 1 週間 stability dry-run
- default model `22e8ed77-94fe-4ef2-871f-a86f94e9a579` literal 商用 license 確認
- 顧客案件 sandbox dry-run (doctrine: client-no-recovery)
- LangGraph + LlamaIndex の 2026 advisory 履歴 sweep (doctrine: external-source-audit)
