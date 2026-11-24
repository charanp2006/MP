# ImplementationV2 — Coding Agent Prompt

Work in the canonical repository `charanp2006/MP`. Read `IMPLEMENTATIONV2.md` fully and follow it.

## Owner notes
- The raw Azure Public Dataset is approximately 1.5 GB, already downloaded locally and gitignored intentionally. Check local inventory/provenance and pipeline; absence from Git is not proof it is missing. Never commit raw data.
- Verify the **actual source code, configs, outputs, results, checkpoints, logs and tests**, not only docs, dashboards, screenshots or status summaries. Rerun checks where feasible.
- Qwen3 should use a hosted Hugging Face deployment/inference endpoint (managed HF Inference Endpoint is the planned primary approach), not require a model running on the user's laptop. Verify current model support, cost, latency and deployment requirements. Do not provision paid resources without explicit approval. Never hard-code or commit tokens.
- Preserve working code; do not rebuild from scratch.

## First task: M0 audit ONLY
Inspect working tree, branch, history, branches/merge status; source tree; configs/dependencies/scripts/CI/tests; `.gitignore`, secret handling and deployment config; local Azure data files and source notes; actual data processing and train/test path; TFT training, checkpoint, metrics, results and inference; planner adapter, stub/fallback, schemas, validation, telemetry and inference evidence; PPO environment/state/action/reward/training/checkpoint/evaluation; integration/safety/executor/live gates and actual live evidence; monitoring exporters, dashboards and actual metrics; replay and outputs. Run relevant tests and verification scripts if possible. Identify docs/code/artifact discrepancies. Do not claim exhaustive inspection unless you list the files reviewed and exclusions.

Write `docs/implementationv2/m0-audit.md` with an evidence table mapping claims to file/artifact/command/test, status and confidence; dataset inventory/provenance; verified state of each component; commands and tests; discrepancies; risks; blockers; and recommended next milestone.

Make only safe, narrowly scoped audit fixes. **Stop after M0 and report to the owner; wait for approval before M1.** Do not train models, download large datasets, provision hosted endpoints, or proceed to later milestones during this audit.

## Rules
- Do not fabricate any result, metric, inference, test, dataset provenance or live action.
- Clearly label measured, estimated, proxy and simulated results.
- Avoid temporal leakage and preserve test isolation.
- Keep raw data, secrets, tokens and sensitive logs out of Git.
- HF hosted inference costs, quotas, latency, privacy and availability must be considered; secret-managed credentials, timeout, bounded retry, error handling and fallback are mandatory.
- LLM planner is advisory and cannot directly execute arbitrary commands. Deterministic safety gate and bounded executor authorize actions.
- Live actions are gated, allowlisted, bounded, verified and rollback-capable; dry-run is default.
- Local-cluster success is not production readiness.
- Use mocks for automated tests but separately verify real inference when M3 is reached.
- Obtain owner approval before paid or external endpoint provisioning.

## Future milestones (wait for M0 approval)
M1 Azure provenance/pipeline audit; M2 TFT reproducibility; M3 hosted Qwen3; M4 full PPO; M5 decision-cycle integration/replay; M6 execution hardening; M7 monitoring/feedback; M8 experiments/energy; M9 demo; M10 final audit. See the plan for acceptance criteria.

## M0 report
Include status, branch/commit/working tree, source paths inspected, local raw data inventory and provenance (without exposing sensitive data), verified TFT/Qwen/PPO/execution/monitoring status, exact commands, test outcomes/limitations, evidence matrix, docs-versus-code discrepancies, risks, changed files/commits and a proposed next milestone. Stop and wait.
