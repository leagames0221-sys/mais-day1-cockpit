# MAIS — Day-1 Cockpit

> **M&A Intelligence Suite (MAIS)** の 3 番目のツール。
> M&A 成約後の **Day-1 統合 100 日計画** を、 買収側 / 被買収側の system / 組織 / process 比較から
> **dependency graph + risk score + communication kit + 中堅日本企業 Day-1 文化 fit 反映** で自動生成する PoC。

[![pip-audit](https://img.shields.io/badge/pip--audit-0%20CVE-brightgreen)]()
[![python](https://img.shields.io/badge/python-3.11+-blue)]()
[![license](https://img.shields.io/badge/license-PoC%20demo-lightgrey)]()

---

## 何ができるか

| 機能 | 内容 |
|---|---|
| **4 軸 statefull plan generator** | LangGraph state graph で organization / process / system / culture を 4 並列 agent で plan 生成 |
| **System integration dependency graph** | NetworkX で system 統合依存 graph + topological sort + critical path + cyclic 検出 |
| **5 audience cascade communication kit** | 広報資料 / 従業員レター / FAQ / 顧客通知メール / vendor / 規制当局 / 投資家 各 audience cascade plan + draft 一式 |
| **過去 PMI 失敗事例 surface** | 5-stage hybrid pipeline で類似案件の地雷を auto-surface |
| **中堅日本企業 Day-1 文化 fit detector** | 組合対応 / 取引銀行折衝 / 同族統合 / 商習慣 / 取引慣行 5 軸 pattern library |
| **risk score 5 dim** | 各 PlanNode + DependencyEdge に 0-100 score |
| **黒×金 brand UI** | FastAPI + Jinja2、 Day-1 plan visualizer + dependency graph view + kit preview |

---

## 想定ユースケース

- **M&A advisory firm** が Day-1 plan 起草を 数日 → 数時間に圧縮
- **コーポレート M&A 部門** の post-deal team が internal cockpit として deploy
- **PE / VC** の portfolio company integration 標準化

---

## tech stack

| 層 | 採用 | source |
|---|---|---|
| Orchestrator | **LangGraph 1.0+** (stateful DAG + checkpoint replay + parallel execution、 CVE-2026-28277 元削除済 pin) | https://www.langchain.com/langgraph |
| Orchestrator fallback | **Pydantic AI** (LangGraph red flag 検出時 literal 切替先、 type-safe + MCP-native) | https://ai.pydantic.dev/ |
| Dependency graph | **NetworkX 3.x** (system 統合依存 graph + topological sort + critical path + cyclic 検出) | https://networkx.org/ |
| Citation infra | **LlamaIndex CitationQueryEngine** | https://docs.llamaindex.ai/ |
| LLM pipeline | 5-stage hybrid (BM25 + dense + RRF + cross-encoder + LLM listwise rerank) + LLMProvider Protocol | (本 suite 共通) |
| Day-1 plan template | 業界 standard 構造 (Dealroom / NMS / Deloitte / Korn Ferry / M&A Science / MergerIntegration.com) decomposed prior art | proprietary (構造のみ inherit) |
| Web UI | FastAPI + uvicorn + Jinja2 | MIT |
| Security | python-ml-stack 5-layer 防御 + Vault Pattern | (本 suite 共通) |

---

## 期待効果

- **Day-1 plan 起草の reduction** ★★
- **communication kit 起草の speed up** ★★
- **2026 industry benchmark**: AI で M&A 統合 12-18 ヶ月 → 3-6 ヶ月圧縮 ★★ (top-tier PMI advisory firm research)

---

## DD ↔ Day-1 入出力契約 (sibling tool 連携)

DD Workbench (mais-dd-workbench) の API output:
- **Citation array** (DDP / DOC / CHK / Q / A / CIT prefix、 source 文書 link back 付き)
- **JP fit pattern hits** (中堅 fit: 同族経営 / 名義株 / オーナー私的経費)
- **質問票回答** (DD Question 数百項目への構造化回答)

Day-1 Cockpit が **入力として literal 流用**:
- DD 結果 → integration plan の **risk score 入力** (JP fit hits が 5 軸 JP Day-1 detector の trigger)
- 質問票回答 → Day-1 plan node の **dependency edge weight**
- Citation array → communication kit の **source link back**

---

## 4-Week roadmap (PoC scope)

| Week | scope | deliverable |
|---|---|---|
| **Week 0** | Discovery → Requirements → Design → Tasks、 GitHub PRIVATE repo + drift CI install、 採用 OSS audit gate | scaffold + design doc |
| **Week 1** | 合成 Day-1 案件 data 生成 + DD output ingestion + LangGraph state graph 設計 | 1 commandlet で DD output → IntegrationPlan literal 動作 |
| **Week 2** | LangGraph state graph 実装 (4 軸 agent) + NetworkX dependency graph + risk score (topological sort + critical path + cyclic 検出) | 4 agent 並列実行 + dependency graph 可視化 smoke |
| **Week 3** | Communication kit 生成 (5 audience cascade、 LLM + Citation link back) + 中堅日本企業 Day-1 文化 fit detector | kit draft 5 種 + JP day1 pattern hit literal |
| **Week 4** | FastAPI/Jinja UI + Vault Pattern + e2e_smoke | 実機 demo (Cloudflare quick tunnel) |

---

## 環境設定

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-week0.txt
copy .env.example .env
```

### 必須 env var

```bash
ANTHROPIC_API_KEY=sk-ant-...           # Week 2+ で active
VAULT_KEY=<fernet key>                  # vault PII 暗号化
SYNTHETIC_SEED=20260513
DATA_DIR=./data
```

---

## 制約 (PoC scope)

- **無料 + クレカ不要範囲** で完走
- **consumer laptop** で完走前提
- **合成 Day-1 案件 data only** — 実 M&A 案件 / 実従業員情報 / 実 vendor 一切扱わない
- **vendor lock-in ZERO**

---

## 移植段階の追加要件

- 実 Day-1 案件投入時 = sandbox (Docker / WSL2) + 顧客 sandbox dry-run + 1 週間 stability
- LangGraph + LlamaIndex + NetworkX の 2026 advisory 履歴 sweep
- 大型案件 = external pentesting 推奨

---

## related tools (M&A Intelligence Suite)

- **mais-deal-matching** — sourcing stage
- **mais-dd-workbench** — Due Diligence automation
- **mais-day1-cockpit** ← 本リポジトリ (Day-1 readiness)
- **mais-pmi-cockpit** — 100-day PMI dashboard
- **mais-pmi-knowledge-base** — knowledge layer (全 tool 共通参照)

---

## license

PoC demo — 設計思想 + コード構造を portfolio 公開、 合成データのみ含む。 商用 deploy は別途相談。
