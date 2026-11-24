# ImplementationV2 — Predictive Container Management for Energy-Efficient Serverless Computing

**Canonical repository:** `charanp2006/MP`

## Owner clarifications

- The raw Azure Public Dataset is approximately **1.5 GB**, downloaded locally and gitignored intentionally. Do not interpret its absence from Git as evidence that it was not downloaded. Verify local files, source provenance, manifest and pipeline. Never commit raw data.
- Do not evaluate from documentation, dashboards or recorded status alone. Inspect actual source, configs, tests, checkpoints, outputs, logs and artifacts; rerun checks where practical.
- Qwen3 will be used through a **Hugging Face-hosted deployment/inference endpoint**, not a model process that must run on the user's laptop. Use managed HF Inference Endpoints as the primary path after verifying model support, cost, latency and deployment needs. Do not provision paid resources without approval. Never commit tokens.
- Preserve current work and continue from `MP`; do not rebuild.

## Target architecture

3. TFT forecast trained/evaluated on verified Azure workload data; 4. Qwen3 planner through hosted Hugging Face inference; 5. PPO policy selects bounded actions; deterministic safety shield validates; 6. bounded Kubernetes/OpenFaaS executor verifies action results; 8. Prometheus/Grafana monitoring and feedback; decision replay connects observations, forecast, plan, action, safety, execution, outcome and feedback.

Components 1 (user/simulation), 2 (general ingestion/application integration) and 7 (broader application/service examples) remain deferred except interfaces needed for integration.

## Non-negotiable rules

- Audit working tree, branch, history, configs, tests, scripts and branches first.
- Raw data, secrets, tokens, large artifacts and sensitive logs remain outside Git.
- Check for existing local Azure data before downloading anything.
- Never fabricate model scores, training, inference, tests, live execution or energy measurements.
- Label synthetic, simulated, estimated, proxy and measured values explicitly.
- Do not claim production readiness based on local Kubernetes.
- The LLM is advisory; it must not directly execute arbitrary commands or control credentials. The deterministic safety gate and bounded executor authorize actions.
- Live execution is opt-in, allowlisted, bounded, verifiable and rollback-capable.
- Hosted inference has cost, quota, latency, privacy and availability implications. Use secret management, timeouts, bounded retries, error handling, redaction and fail-safe fallback.
- Keep schemas and experiment configs versioned; protect test-set separation and avoid temporal leakage.

## Milestones

### M0 — Complete repository and artifact audit (mandatory first, then stop)
Inspect:
- git status, branch, history, branch list and merge status;
- complete relevant source tree, project config, dependencies, scripts, CI, tests, `.gitignore`, deployment and secrets handling;
- local Azure dataset inventory, files, sizes, structure, source notes, hashes if feasible (do not commit/upload);
- data loading, preprocessing, features, actual train/test paths;
- TFT training, checkpoint, evaluation, metrics and actual inference;
- Qwen planner adapter, fallback, schemas, validator, telemetry and successful inference evidence;
- PPO environment, observations, actions, reward, training, checkpoints, evaluation and evidence;
- safety shield, executor, live gates, Kubernetes/OpenFaaS and actual live action evidence;
- Prometheus/Grafana/exporter, metrics samples and feedback;
- replay, generated results and scripts;
- rerun relevant tests/checks where possible and identify discrepancies between code and docs.

Write `docs/implementationv2/m0-audit.md`. For each claim, map it to code, artifact, command or test; indicate confidence and gaps. List files inspected and exclusions honestly. Fix only safe, narrow audit issues. **Stop and wait for owner review after M0.** Do not implement further milestones in the same run.

### M1 — Azure data provenance and pipeline
Locate/inventory the locally downloaded raw dataset. Verify source, version/release, schema and coverage. Keep raw data gitignored. Add/verify a provenance manifest (metadata, relative paths, sizes, hashes where useful, instructions; no raw data). Audit timestamp handling, ordering, duplicates, missing values, outliers, resampling, features, deterministic/restartable processing, chronological splits and leakage. Fit transformations only on train data. Generate data-quality reports and tests. Deliver reproducible config/commands and verified processed artifacts.

### M2 — TFT reproduction and evaluation
Reproduce existing experiment with exact config, data manifest, revision and seed. Verify splits and checkpoint inference. Compare matched baselines (persistence, seasonal naive where supported, and existing relevant baselines). Evaluate MAE/RMSE and justified additional metrics; avoid misleading percentage metrics for zero-heavy data. Report horizon and workload-segment performance. Produce actual-vs-predicted, residual, training curves, baseline plots, machine-readable results and reproducibility notes.

### M3 — Hosted Qwen3 on Hugging Face
Reuse provider interface. Select and pin an appropriate Qwen3 model/revision after assessing support, latency, cost and deployment. Provide endpoint instructions; provisioning requires owner approval. Implement HF adapter with environment/secret-managed credentials, compact versioned request, structured output parsing/schema validation, bounded retries, timeouts, rate-limit handling and fail-safe fallback. Log sanitized model/version, latency, status, validation and usage if available. Test successful real inference through the project's code path plus timeout, endpoint unavailable, rate limit, malformed output and invalid plan. Evaluate a fixed scenario suite (schema validity, constraint violations, latency, consistency, fallback rate). Planner recommendations are advisory. Avoid capturing hidden chain-of-thought; use concise rationale/evidence fields.

### M4 — PPO research training
Audit environment realism, state/action space, reward terms, cooldown, resource/SLA/energy objectives and leakage. Define scenario sets and held-out evaluation. Train using a justified budget, multiple seeds and validation-selected checkpoints. Record curves, returns and stability. Test on held-out Azure-derived and clearly labelled simulation scenarios. Compare with matched reactive/threshold/heuristic baselines. Report seed/scenario-level results and uncertainty. Add safety tests and feasible ablations. Deliver configs, checkpoints, plots, results and report.

### M5 — Integrate 3→4→5
Version state/decision interface. Connect real TFT forecast, validated hosted Qwen plan and PPO action. Specify exactly how planner advice affects PPO (feature, candidate guidance or constraint); don't allow silent LLM override. Keep deterministic safety separate. Handle stale/missing data, conflicts and model failures. Record unique decision IDs and timestamps. Build replay from actual records. Test normal, spike/drop, stale-data, endpoint-failure, invalid plan, PPO failure and safety intervention.

### M6 — Execution hardening
Audit executor permissions, allowlists, namespace/deployment restrictions, gates and rollback. Dry-run default. Require explicit live opt-in. Executor accepts only validated bounded actions. Check preconditions, cooldown, quotas and freshness. Verify post-action state, record audit and rollback/failure. Ensure LLM/training processes do not have cluster credentials. Test unauthorized targets, overflow, missing deployment, failure, rollback, stale telemetry and unavailable cluster. Perform controlled low-risk local live tests.

### M7 — Monitoring and feedback
Audit metric definitions/units/labels/scrape intervals/cardinality. Verify real CPU, memory, workload, latency, cold-start, SLA, forecast, planner, safety and execution metrics. Correlate with decision/execution IDs. Validate feedback linkage to observed outcomes; do not silently online-update models. Verify dashboard values from actual samples. Distinguish physical energy, estimator and proxy. Deliver metric catalog, dashboard, replay and tests.

### M8 — Evaluation and energy
Freeze protocol, dataset manifest, scenarios, model versions, baselines, seeds, run durations, resource limits and metrics. Evaluate forecast error by horizon; latency including tail; SLA violations; cold starts; resource utilization; action churn/oscillation; execution failures; planner latency/fallback; energy. Prefer physical power measurement where possible. Otherwise document estimator, assumptions, scope and calibration. Proxies must be labelled and cannot support claims of measured energy savings. Perform matched baseline experiments, forecast ablation, planner ablation, safety/failure tests, multiple seeds and appropriate uncertainty. Deliver reproducible scripts, result tables, plots and report.

### M9 — Demonstration
Show observed workload/system state → TFT forecast → hosted Qwen plan and validation → PPO action → safety gate → actual execution or clearly labelled dry run → observed state → monitoring → feedback → replay. Include repeatable synthetic scenarios, clearly distinguished from Azure experiments and live observations. Provide startup/shutdown/recovery runbooks. Do not expose secrets.

### M10 — Final audit
Completion requires source review, tests, reproducible artifacts, dataset provenance, real Qwen inference, adequate PPO training, baselines, matched experiments, qualified energy claims, verified live safety/execution, monitoring/feedback, accurate replay, consistent docs/runbooks and security review.

## Decision replay event record
Record decision ID and timestamps; observation and freshness; forecast model/checkpoint, values, horizon and latency; planner model/revision, sanitized input/output, rationale summary, validation and fallback; PPO version, state and action; safety checks and result; executor mode, target, action, outcome, verification and rollback; post-action latency/SLA/cold-start/resource and energy type; feedback and retraining status. Missing values must be explicit; demo data must be labelled simulated.

## Milestone report format
Outcome (complete/partial/blocked); inspected files; changed files; exact commands; test pass/fail/skipped and limitations; experiment config/artifacts; actual vs simulated distinction; hosted service cost/security implications; acceptance criteria evidence; risks; next milestone. Do not declare complete without evidence.
