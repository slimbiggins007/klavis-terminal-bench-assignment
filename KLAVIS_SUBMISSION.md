# Klavis AI coding assignment

This repository contains one original Terminal-Bench 3 task: `tasks/rollout-reconciler`.

The task asks an agent to reproduce a retired production journal guard from an execute-only diagnostic with a fixed audit-query budget, then repair a deterministic deployment controller. The repaired controller must recover a maximum-authority causally closed acyclic cut from forked authenticated journals, replay it safely, and schedule rollout actions under overlapping capacity limits.

## Repository contents

- `tasks/rollout-reconciler/instruction.md`: concise agent-facing task contract
- `tasks/rollout-reconciler/task.toml`: metadata, resources, artifacts, and isolation configuration
- `tasks/rollout-reconciler/environment/`: starter package, normative protocol, synthetic incident data, and budgeted diagnostic sidecar
- `tasks/rollout-reconciler/solution/`: standalone reference implementation used by the oracle
- `tasks/rollout-reconciler/tests/`: independent root-owned verifier in a separate container
- `EVALUATION.md`: commands, locked configurations, required results, exclusions, and failure analysis

## Design summary

The difficulty comes from interacting operational semantics rather than scale or clerical work. The agent must spend at most 96 black-box evaluations to infer weighted quorum, signer retirement, leadership handoff, emergency rollback, skew exceptions, and authority scoring. Those decisions determine which records can enter a cross-source journal cut. The selected cut must be causally closed and acyclic, replay must be deterministic under duplicate and shuffled delivery, leases must fence stale attempts, rollback must precede retry, and action planning must optimize globally across overlapping failure domains.

Only `/app/rollctl/` is collected. It may contain source-only non-executable Python files and is copied into a fresh verifier image where the diagnostic, reference solution, and tests are absent from the agent environment. Candidate code runs as `nobody` with `no-new-privs`; root-owned tests publish a binary reward.

## Completed evaluation

The final task passed every required static check, all 34 applicable implementation-rubric criteria, Docker build, oracle validation, and nop validation. The oracle passed all 20 verifier tests with reward `1.0`; nop received reward `0.0`.

Three Codex / GPT-5.6 Sol / xhigh trials and three Claude Code / Claude Opus 5 / max trials each completed without exceptions and received reward `0.0`. Every run passed 18 of 20 suites and failed the same two retired-policy boundary suites, which localizes the failure to the intended black-box inference crux. Both pure-model adversarial trials also received reward `0.0`, and a supplemental active red-team run found no verifier bypass.

The exact commands, job names, model-audit details, excluded infrastructure attempts, and failure analysis are in `EVALUATION.md`. The Klavis assignment does not require a pull request against the upstream Terminal-Bench repository.
