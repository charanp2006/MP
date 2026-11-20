# Pre-flight — Repository Audit and Contract Harmonization

| Field | Value |
|---|---|
| Milestone | M0 — Pre-flight repository audit and contract harmonization |
| Status | **Complete (audit/verification only)** |
| Date | 2026-11-19 |
| Branch | `feat/m1-audit-contract-harmonization` |
| Base/HEAD commit (audited) | `f41feecb2433b9a304ee1ee37b118b24fc0182bc` — "Merge pull request #5 from charanp2006/dev" |
| Scope of work | Inspection, test/smoke verification, contract/unit/schema/status audit. **No model training, no large dataset downloads, no M1+ implementation.** |

## Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-11-19 | Initial pre-flight audit report recorded from repository inspection and verification run. |
| v1.1 | 2026-11-20 | Renumbered as pre-flight M0 to follow `IMPLEMENTATION_PLAN.md`. |

## 1. Objective (M0)

- Inspect current implementation and test status.
- Identify and reuse existing modules.
- Harmonize (assess) units, workload semantics, metric definitions, state/action schemas, config and result format.
- Document what exists versus what is still a stub.
- Establish (assess) experiment reproducibility metadata and artifact layout.

## 2. Plan executed

1. Recorded branch/commit and created a dedicated feature branch from current `dev` HEAD.
2. Inspected repository docs, configs, CI, tests, modules, branches, artifacts, and working-tree state.
3. Ran existing tests and small smoke checks to verify current behavior.
4. Mapped implemented modules vs stubs/gaps; reviewed schemas/units/metrics/config/result contracts and reproducibility/artifact layout.
5. Reported findings and next concrete step only (no M1+ work).

## 3. Files inspected (evidence)

**Root/meta:** `AGENTS.md`, `README.md`, `project.md`, `plan.md`, `IMPLEMENTATION_AGENT_PROMPT.md`, `IMPLEMENTATION_PLAN.md`, `FINAL_IMPLEMENTATION_REPORT.md`, `.gitignore`, `pytest.ini`, `requirements.txt`

**Config:** `configs/project.yaml`, `configs/__init__.py`

**Docs:** `docs/architecture.md`, `docs/design.md`, `docs/prd.md`, `docs/security.md`, `docs/test_plan.md`, `docs/validation-report.md`, `docs/tech-stack.md`, `docs/references.md`, `docs/implementation/README.md`, `docs/implementation/p1-v1.0-*.md` … `p5-v1.0-*.md`

**CI:** `.github/workflows/tests.yml`

**Code (key):** `data/{__init__,ingestion,preprocessing,feature_engineering,pipeline,sample}.py`, `forecasting/{__init__,dataset,tft_model,train,evaluate,inference,tft_service}.py`, `rl/{__init__,environment,reward,policy,train_ppo,evaluate_ppo}.py`, `agent/{__init__,schemas,prompts/planner.txt,planner,validator}.py`, `orchestrator/{__init__,state_builder,sla_guard,action_validator,executor,decision_loop}.py`, `baseline/reactive.py`, `monitoring/{__init__,metrics,feedback,prometheus_exporter,README}.py|.md`, `experiments/run_experiments.py`, `scripts/*.py`, `infrastructure/README.md`

**Tests:** `tests/{conftest,test_ingestion,test_preprocessing,test_feature_engineering,test_pipeline,test_forecasting,test_rl,test_agent,test_orchestrator,test_executor,test_monitoring}.py`

**Runtime/artifacts inspected (state only):** `data/raw/`, `data/processed/features.csv`, `models/tft_checkpoint.pt`, `models/ppo_policy.pt`, `results/*.json`, `results/plots/`, `infrastructure/{docker,kubernetes,openfaas}/` (empty dirs), `monitoring/{grafana,prometheus}/` (dirs), `utils/` (empty)

## 4. Files changed

- **Git refs only:** created branch `feat/m1-audit-contract-harmonization` (pointing at `f41feecb`). No tracked source/config logic modified in the pre-flight audit.
- **Documentation added (this milestone reporting):** `docs/milestones/README.md`, `docs/milestones/m1-repository-audit-and-contract-harmonization.md` (audit record + milestone reporting convention).
- **Pre-existing/untracked working-tree items (not created/modified by this audit, preserved):** `IMPLEMENTATION_AGENT_PROMPT.md`, `IMPLEMENTATION_PLAN.md`, `FINAL_IMPLEMENTATION_REPORT.md`, `file.png`, and accidental path-artifact files (`CCharanMP*` / `C:CharanMP*`) plus `C:CharanMPscripts/` — left untouched; must be cleaned/excluded deliberately (not committed as-is).

## 5. Architecture impact (current, as-is)

No implementation changes to runtime logic. Verified current flow:

`data pipeline (sample/Azure-CSV path) -> TFT (compact PyTorch, checkpoint inference/service) -> StateSnapshot builder -> Qwen3 planner (stub default / Ollama adapter with fallback) -> plan validator -> PPO policy/env -> action validator -> SLA guard -> executor (noop/k8s kubectl-scale, dry-run/disabled by default) -> metrics/feedback (in-memory)`, with baseline/experiment/scripts scaffolding.

**Contracts/schemas observed:**
- `StateSnapshot` and `Plan`: strict pydantic models (`agent/schemas.py`, `extra="forbid"`). Strategies: `NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate`. Priorities/urgencies bounded; includes warm/active containers, SLA margin/threshold, trend, forecast horizon.
- PPO observation: 10-dim normalized vector (`rl/environment.py`) — predicted/current workload, CPU, memory, latency/SLA, p95/SLA, active/max, cold_starts placeholder (0 in obs; transient in step info), energy/ref, sla_margin/SLA.
- Decision/execution/metrics emitted as JSON-able records.

**Units/semantics observed (to harmonize explicitly in M1+):** control interval 60s; latency/p95 in ms; SLA 250ms (+20ms safety margin in guard); CPU/memory in [0,1]; capacities/counts ints (min 2 / max 30 / max_change 5); workload target `invocation_count` (env aggregates per-timestamp sum); energy/power simulated/proxy in env/metrics (not measured). Some fields have dual meanings across modules (e.g. `energy` gauge/unit, cold-start count vs rate, oracle vs TFT forecast source).

## 6. Dataset/model (current, verified)

- **Dataset:** no official Azure Public Dataset acquisition pipeline/manifest/hash/license record in code. Default `data.source: sample` synthetic trace (`data/sample.py`, 7d/30s/3 functions). `data.source: file` + `source_path` supported by ingestion, but no real trace bundled/validated. `data/processed/features.csv` exists locally (artifact); `data/raw/` empty except `.gitkeep`.
- **Models:** compact TFT and custom PyTorch PPO implementations present; local gitignored checkpoints exist (`models/tft_checkpoint.pt`, `models/ppo_policy.pt`, smoke/not production). Forecasting dataset uses chronological split/windowing; PPO trains in simulated env. **No pre-flight training performed.**
- **Planner:** Qwen3/Ollama adapter implemented but not exercised (Ollama/model unavailable in this audit); deterministic stub/fallback available.

## 7. Commands executed

```text
git branch -a --no-color
git status --short --branch
git log --oneline -5
git rev-parse HEAD && git rev-parse --abbrev-ref HEAD
git rev-parse main; git rev-parse origin/main; git log --oneline -1 main
git ls-files --cached --others --exclude-standard | wc -l; git ls-files | head -n 40
git show --name-only --oneline HEAD
find . -maxdepth 3 -type f | ... (repo layout scan)
find . -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.git/*" | sort
git grep -n "TODO|FIXME|STUB|NotImplemented|pass  # stub|placeholder" -- ':!*.pyc'
ls (root/modules/tests/results/data/models/infra/monitoring/scripts)
cat .github/workflows/tests.yml; cat requirements.txt; cat pytest.ini; cat .gitignore
cat configs/project.yaml; cat AGENTS.md; cat README.md; cat project.md; cat plan.md
cat docs/{architecture,design,prd,security,test_plan,validation-report,implementation/README}.md (+ phase docs)
cat (key modules: data/*, forecasting/*, rl/*, agent/*, orchestrator/*, baseline/reactive.py, monitoring/*, experiments/run_experiments.py, scripts/*, infra/monitoring READMEs)
git checkout -b feat/m1-audit-contract-harmonization
py -m pytest -q
python -c "from data.pipeline import run; from configs import load_config; df,s=run(load_config()); print('shape', df.shape); print('cols', list(df.columns)); print('summary_keys', list(s.keys()))"
python -m scripts.run_proposed_system --steps 3
mkdir -p docs/milestones
(wrote docs/milestones/README.md and docs/milestones/m1-repository-audit-and-contract-harmonization.md)
```

## 8. Tests

- `py -m pytest -q` → **103 passed, 1 warning in 13.67s**.
  - Wa
