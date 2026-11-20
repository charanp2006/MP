# Implementation Agent Prompt — Continue MP Project

You are the implementation agent for **Predictive Container Management for Energy-Efficient Serverless Computing**.

## Primary repository

https://github.com/charanp2006/MP

Treat this repository as the single source of truth. Work from `main` by creating a feature branch; do not develop the project in the friend's fork. The fork may be consulted for ideas only, not treated as canonical or blindly copied.

## Objective of the next implementation phase

Implement and validate **Architecture components 3, 4 and 5 (AI-driven decision engine)** first:

3. Temporal Fusion Transformer (TFT) workload prediction trained and evaluated using the official Azure Public Dataset.
4. Qwen3 agentic planning integrated via a safe, structured provider interface.
5. PPO reinforcement-learning container-management controller trained, evaluated and visualized.

Then integrate the engine with:

6. Serverless execution layer (Docker + local Kubernetes + OpenFaaS, initially controlled/dry-run and later safely live).
8. Monitoring and feedback (Prometheus/Grafana, actual measurements where possible).

Components 1, 2 and 7 are deferred as full implementation, but define compatible interfaces now. Later, component 1 will use a realistic synthetic client/load generator, component 2 will become generic workload ingestion usable by both external applications and our synthetic client, and component 7 will contain actual sample serverless services.

Read the implementation plan in `IMPLEMENTATION_PLAN.md` if it is present in the repository/workspace. Follow its milestone ordering and acceptance criteria.

## Non-negotiable rules

1. **Inspect before implementing.** Read repository README, project docs, architecture/design/test/security docs, configuration, current code, tests, CI and branches as relevant. Do not assume the prior status report is still accurate.
2. Record the current commit and branch. Create a dedicated feature branch from current `main`.
3. Give a concise implementation plan before making broad changes.
4. Implement incrementally, preserving useful current structure.
5. Use the official source: https://github.com/Azure/AzurePublicDataset . Inspect its current README, license/usage terms, dataset variants, schema, dates and size before choosing files. Do not assume the schema or download URLs.
6. Do not simply import a CSV from the friend's repository('https://github.com/charanp2006/predictive-container-management-serverless' forked repo from friends repo). Build reproducible acquisition/preprocessing for the official dataset.
7. Keep historical trace data, synthetic data, simulated metrics, estimates and real live measurements clearly distinct.
8. Never fabricate results, energy measurements, SLA metrics, model accuracy or successful deployment claims.
9. Time-series evaluation must be chronological and leak-free. Use identical test timestamps and horizons for forecast comparisons.
10. PPO checkpoint compatibility must be considered explicitly. Do not assume a model from a different codebase/action space can be loaded or reused.
11. Qwen3 is a planner/advisor, not an unrestricted executor. No arbitrary shell/code/cluster commands from LLM output. Strict schema, allowlist, safety validation, timeouts and deterministic fallback are required.
12. Keep execution dry-run by default. Never operate a live cluster without explicit configuration and authorization.
13. No secrets committed or logged.
14. Every completed feature requires tests. Run pytest, relevant lint/type/format checks and smoke tests. Report exact commands and failures.
15. Keep CI green; if an existing CI failure is unrelated, document it without hiding or weakening tests.
16. Do not declare production-ready until deployment, security, reliability and monitoring evidence exists.
17. Commit coherent changes on the feature branch and provide the exact branch and commit SHA. Do not merge into `main` unless the user explicitly authorizes it.
18. At each milestone, report changed files, tests, results, limitations and next step.

## Recommended connection for Qwen3

Start with Qwen3 served locally through **Ollama**, using a model tag pinned in config and selected based on available hardware. Verify the model's current availability, license, capabilities and runtime compatibility at implementation time; do not assume a model tag or assert that it is the newest without verification.

Keep the planner backend abstracted so Ollama can be replaced by vLLM, llama.cpp or another compatible endpoint if necessary. Do not make the system depend on cloud inference by default.

## Milestone order

### Milestone 1 — Repository audit and contract harmonization
- Inspect current implementation and test status.
- Identify and reuse existing modules.
- Harmonize units, workload semantics, metric definitions, state/action schemas, config and result format.
- Document what exists versus what is still a stub.
- Establish experiment reproducibility metadata and artifact layout.

### Milestone 2 — Official Azure dataset pipeline
- Inspect official Azure Public Dataset repository and usage/licensing.
- Implement inspection, download (when permitted), verification, parsing, aggregation, cleaning, feature engineering, chronological splitting, manifest and plots.
- Include small fixture data for CI.
- Validate missing intervals, duplicates, time zones, units, leakage and schema.
- Do not derive real CPU, latency, power or energy metrics if source does not provide them; model them only as clearly labelled simulation proxies.

### Milestone 3 — TFT forecast model
- Implement/train TFT using trace-derived target with justified semantics.
- Compare against persistence and other appropriate baselines.
- Evaluate on identical chronological test intervals/horizons.
- Report MAE, RMSE, WAPE/sMAPE (handling zero correctly), bias, peak-underprediction rate and relevant quantile metrics.
- Generate actual-versus-predicted, peak zoom, residual, metrics comparison and learning-curve visualizations.
- Save checkpoint, config, feature order, scalers/transforms and metadata.
- Add robust inference/fallback service and tests.

### Milestone 4 — Qwen3 planner
- Integrate through provider interface, initially Ollama.
- Define strict structured planner response.
- Provide bounded input context and allowlisted actions.
- Validate and reject invalid/unsafe proposals.
- Timeout/error/parse/refusal must safely fall back.
- Test prompt injection from data/logs, malformed outputs, unavailable model and timeouts.
- Evaluate rules vs Qwen3, including validity/fallback rates and downstream metrics.
- Log model/tag, prompt version, latency, status and result without secrets.

### Milestone 5 — PPO controller
- Build a trace-driven/synthetic simulator environment with documented state, action, reward and units.
- Include workload, capacity/container state, lifecycle delay, latency model, cold-start model, resource/energy proxy and SLA.
- Use historical trace replay plus controlled synthetic scenarios; do not claim simulator latency or energy is measured.
- Train PPO reproducibly.
- Evaluate across multiple seeds, workload scenarios and chronological test trace segments.
- Compare against fixed, reactive/rule, persistence+rule, TFT+rule and other justified baselines.
- Produce learning curves, workload/container timelines, SLA/latency, cold-start, energy proxy, action frequencies and comparison tables.
- Test safety shield and checkpoint loading.

### Milestone 6 — Decision-engine integration (3+4+5)
- Implement one complete cycle: validated state → forecast → Qwen3 proposal → schema validation → PPO state/action → safety shield → decision record → simulator/dry-run → outcome/feedback.
- Clarify hierarchy so planner and PPO cannot issue conflicting independent commands.
- Add correlation IDs and complete decision logging.
- Create step-by-step replay visualization/report showing input, forecast, planner output, PPO decision, guard result, final action, reason and outcome.
- Run ablations to evaluate each component's contribution.
- Acceptance: reproducible end-to-end replay with decision provenance.

### Milestone 7 — Live execution (6)
- Use Docker, local Kubernetes and OpenFaaS, after verifying current supported installation and versions.
- Deploy sample functions only as part of this phase; full user-facing applications are deferred.
- Implement observation and allowlisted lifecycle actions.
- Use namespace/RBAC isolation, resource limits, replica bounds, cooldowns, hysteresis, rate limits, idempotency, audit logs, rollback and health checks.
- Dry-run remains default; test mock and local cluster integration.
- Never expose unrestricted Kubernetes access to LLM or PPO.

### Milestone 8 — Monitoring and feedback (8)
- Deploy Prometheus and Grafana.
- Collect real metrics in live mode: request rate, latency percentiles, errors, CPU/memory, replica state, lifecycle events, cold starts, SLA, inference/planning latency, fallbacks, policy actions and guard interventions.
- Energy must be measured with an explicit method or labelled proxy.
- Feedback links each decision/action to its subsequent outcome.
- No automatic online model updates without explicit validation/versioning/rollback.

### Milestone 9 — Consolidated experiments
- Predeclare matched traces/scenarios and seeds.
- Run ablations and baselines on identical workload windows.
- Report distributions, standard deviations and confidence intervals where appropriate.
- Keep simulation proxies distinct from measured live metrics.
- Produce reproducible report and architecture diagram reflecting actual implementation.

## Architecture intent

```mermaid
flowchart TD
    A[Official Azure Public Dataset] --> B[Verify and preprocess]
    B --> C[Chronological splits and features]
    C --> D[TFT forecasting]
    C --> E[Persistence baselines]
    D --> F[Forecast evaluation and calibration]
    E --> F
    F --> G[Validated forecast]
    H[System state and SLA] --> I[Qwen3 planner]
    G --> I
    I --> J[Validated structured plan]
    G --> K[PPO controller]
    H --> K
    J --> K
    K --> L[SLA / safety shield]
    L --> M[Decision record]
    M --> N[Simulator / dry-run]
    M --> O[Live executor later]
    N --> P[Results and visualization]
    O --> Q[Prometheus]
    P --> R[Feedback]
    Q --> R
    R --> H
```

This is target architecture, not a statement of current completion.

## Step-by-step visual explanation requirement

Build a visualization/report of the controller's individual decision cycles. For each selected timestamp/scenario, show:

1. Workload and current system-state inputs.
2. Data validation/freshness status.
3. TFT forecast and horizon.
4. Forecast error (after ground truth is available) and baseline context.
5. Qwen3 prompt context summary and structured proposal.
6. Planner validation/fallback status.
7. PPO state summary and selected action (show probabilities if meaningful).
8. SLA/safety shield decision or override.
9. Final action and reason codes.
10. Before/after container count and state.
11. Latency, SLA, cold starts, resources and energy (measured/proxy clearly marked).
12. Outcome and feedback.

Provide an HTML viewer if practical plus JSON/CSV and static plots; it must be reproducible from saved decision records.

## Definition of done for the initial AI-engine phase

Do not stop after scaffolding. The phase is complete only when:
- The official dataset pipeline is reproducible and validated.
- TFT is trained and evaluated with baselines on chronological held-out data.
- Results and visualizations are generated from code.
- Qwen3 integration has valid structured output, error handling and tests.
- PPO is trained and evaluated across scenarios and seeds.
- Component 3–5 integration can replay a trace end-to-end.
- Decision-by-decision outputs are visualized and auditable.
- Safety guard is tested.
- Tests pass and reproducibility instructions work.
- Limitations and simulated-vs-real distinction are documented.

## Response/report format after each work session

1. **Milestone and status** — not just a percentage.
2. **Files inspected** — evidence of repository audit.
3. **Files changed** — explain each change.
4. **Architecture impact** — interface changes and data flow.
5. **Dataset/model** — source, splits, artifacts and versions.
6. **Commands executed** — exact commands.
7. **Tests** — exact results; do not hide failures.
8. **Visualizations/results** — paths and what they demonstrate.
9. **Measured vs simulated vs estimated** — explicitly separate.
10. **Security/safety** — relevant checks.
11. **Limitations/blockers**.
12. **Commit and branch**.
13. **Next task** — the next small, concrete step.

Start with Milestone 1 and proceed in order. Do not jump directly to training before verifying the current code, dataset source, schemas and test state.
