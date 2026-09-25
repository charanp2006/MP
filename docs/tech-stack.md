# Technology Stack

Canonical technology choices for the project, aligned with the final
presentation (slides 6 and 8), the `Tools & Technologies` image, and
`project.md` section 17.

> Version pins belong in a `requirements.txt`/lock file created during
> implementation. The labels below describe roles, not pinned versions.

## Stack summary

```
Predict · Plan · Optimize · Scale
        │
        ▼
┌──────────────────────────────────────────────┐
│  ML / AI Layer                               │
│  Python · pandas · NumPy · PyTorch           │
│  TFT (forecast) · Qwen3 (plan) · PPO (act)   │
├──────────────────────────────────────────────┤
│  Infrastructure Layer                        │
│  Kubernetes · OpenFaaS · Docker              │
├──────────────────────────────────────────────┤
│  Observability Layer                         │
│  Prometheus · Grafana                        │
└──────────────────────────────────────────────┘
```

## Decision table

| Category | Tool / Library | Role in the project | Notes |
| --- | --- | --- | --- |
| Programming | Python 3 | Orchestration, ML/RL pipelines, executor glue | Use a virtual env (`venv`/`.venv`) |
| Data processing | pandas | Cleaning, resampling, windowing, feature engineering | Chronological resampling to control interval |
| Data processing | NumPy | Array ops, metrics (MAE/RMSE/MAPE), reward math | |
| Configuration | PyYAML | Load `configs/project.yaml` defaults | Single source of truth |
| Validation | pydantic / jsonschema | Plan + action schema validation (Qwen3 output, PPO action) | Security boundary — untrusted until validated |
| Deep learning | PyTorch | Model implementation and training | Backend for TFT and PPO |
| Forecasting | Temporal Fusion Transformer (TFT) | Short-horizon workload forecast (history 30 → horizon 5) | e.g. built on PyTorch or `pytorch-forecasting`; keep configurable |
| Agentic AI | Qwen3 | High-level planning/reasoning over forecast + state + SLA | Structured JSON output only; no infra commands |
| RL control | PPO | Bounded container action selection in the closed loop | Action set: NoOp, PreWarm, ScaleOut, Reuse, ScaleIn, Terminate; e.g. `stable-baselines3` or custom PyTorch |
| Serverless runtime | OpenFaaS | Function execution / serverless layer on K8s | Execution target, not dataset source |
| Containerization | Docker | Build and run function containers | Non-root, pinned image versions |
| Orchestration | Kubernetes | Container lifecycle and scaling | RBAC, namespaces, quotas, no cluster-admin for the controller |
| Monitoring | Prometheus | Metrics collection and storage | cAdvisor/node-exporter for container/node and energy metrics |
| Dashboards | Grafana | Workload, infra, performance, efficiency, AI-control panels | See `docs/design.md` section 22 |
| Dataset | Azure Functions traces | Historical workload data (DATA SOURCE ONLY) | Anonymized/synthetic preferred for demos |
| Development | Jupyter Notebook / VS Code | Experimentation and implementation | |
| Version control | Git / GitHub | Source + docs; branches `main`, `files`, `docs` | See `AGENTS.md` |
| Testing | pytest (unit/component), pytest-benchmark / custom harness (system/perf) | Test IDs U01–U12, D01–D04, T01–T04, Q01–Q06, R01–R04, I01–I06, S01–S06, F01–F06 | From `docs/test_plan.md` |

## Per-pipeline-stage mapping

| Pipeline stage | Tools |
| --- | --- |
| Ingestion | pandas, OpenFaaS/K8s metrics, Prometheus exporters |
| Preprocessing | pandas, NumPy, PyYAML (config-driven) |
| Feature engineering | pandas (lag/rolling/temporal features) |
| Forecasting | PyTorch + TFT |
| Planning | Qwen3 (structured schema) |
| Control | PyTorch + PPO |
| Validation | pydantic/jsonschema + custom SLA guard |
| Execution | executor → Kubernetes API → OpenFaaS/Docker |
| Monitoring | Prometheus + Grafana |
| Logging/persistence | experiment logger (JSON), metrics DB |
| Evaluation | pandas/NumPy metrics, notebook/report scripts |

## Implementation notes

1. Keep `configs/project.yaml` as the only source for experiment defaults
   (forecast window, horizon, control interval, capacity bounds, SLA).
2. The AI stack must never issue arbitrary shell/Kubernetes commands — actions
   pass schema → bounds → SLA guard → authorization checks.
3. Create `data/raw/` and `data/processed/` with `.gitkeep`; they are
   git-ignored (see `.gitignore`).
4. Add `models/`, `checkpoints/`, `runs/`, `logs/` at first training run;
   they are git-ignored.
5. Pin exact versions only after the first end-to-end prototype runs;
   record them in `requirements.txt` (+lock file) and in experiment logs
   (see `docs/prd.md` NFR-03 reproducibility).