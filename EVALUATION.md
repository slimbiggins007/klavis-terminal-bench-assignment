# Evaluation record

This file records the required checks and evaluation runs for the Klavis AI Terminal-Bench 3 assignment. All dates and times are Pacific Time. Raw Harbor jobs were retained locally under `harbor-output/`; they are not part of the submission because trajectories are large and may contain provider-authentication metadata. The result summaries, model locks, verifier outcomes, and relevant failure details are recorded below.

## Final result

The frozen task at `tasks/rollout-reconciler` satisfies the assignment requirements:

- all current repository static checks passed;
- all 34 applicable implementation-rubric criteria passed, with the optional task README criterion marked not applicable;
- the Docker oracle received reward `1.0` and passed all 20 verifier tests;
- the Docker nop received reward `0.0` and failed 17 of 20 verifier tests;
- all three required Codex / GPT-5.6 Sol / xhigh standard trials were genuine verifier failures with reward `0.0` and no exception;
- all three required Claude Code / Claude Opus 5 / max standard trials were genuine verifier failures with reward `0.0` and no exception;
- both required pure-model adversarial trials received reward `0.0`;
- no standard infrastructure failure was counted as a model failure, and no verifier bypass was found.

The final task digest recorded by the oracle, nop, and all six standard-trial lock files is:

```text
sha256:c30ca264856d8a320da5b1fab8e2b349b0df1838acb6047fbba0f328bc2bdfbc
```

No task file changed between the final implementation review, oracle/nop validation, and the six standard runs.

## Environment and task configuration

- Evaluation date: August 23, 2026 PT
- Harbor: `0.22.0`
- Backend: local Docker through the `colima` context
- Docker Compose: `5.5.0`
- Codex CLI used by the pinned adversarial run: `0.149.0`
- Claude Code CLI: `2.1.241`
- Agent: unprivileged `nobody`
- Verifier: separate container as `root`
- Agent timeout: `14400` seconds
- Verifier timeout: `120` seconds
- Environment: 1 CPU, 2048 MB memory, 10240 MB storage, no GPU
- Declared artifact: `/app/rollctl/` only
- Retired-guard diagnostic budget: 96 lifetime evaluations

The assignment explicitly permits the Docker subscription workflow. Docker was used because no Modal credentials were configured; this changes only the execution backend, not the required agent, model, reasoning level, task, or verifier.

## Static and implementation checks

The current static workflow lists 22 required scripts. I ran the repository's complete static script set, which includes those 22 checks, under Python 3.12 because macOS `/usr/bin/python3` is Python 3.9:

```sh
bash -c '
  python3() { /opt/homebrew/opt/python@3.12/bin/python3.12 "$@"; }
  export -f python3
  for check in checks/check-*.sh; do
    bash "$check" tasks/rollout-reconciler || exit 1
  done
'
```

Result: all checks passed. `git diff --check` and Python compilation also passed.

The implementation-rubric review command was:

```sh
harbor check tasks/rollout-reconciler \
  -r rubrics/task-implementation.toml \
  --agent codex --model openai/gpt-5.6-sol --env docker \
  --ak reasoning_effort=xhigh --ae CODEX_FORCE_AUTH_JSON=1 \
  -o harbor-output \
  --job-name rollout-reconciler-implementation-codex-8
```

Result: 34 applicable criteria passed, zero failed, and `task_readme` was not applicable. Local evidence: `harbor-output/rollout-reconciler-implementation-codex-8/check_report.json`.

## Docker build, oracle, and nop validation

Commands:

```sh
harbor run -p tasks/rollout-reconciler --agent oracle --env docker --yes \
  -o harbor-output --job-name rollout-reconciler-budget-oracle-2

harbor run -p tasks/rollout-reconciler --agent nop --env docker --yes \
  -o harbor-output --job-name rollout-reconciler-budget-nop-1
```

| Check | Reward | Verifier | Exceptions | Local job |
| --- | ---: | --- | ---: | --- |
| Oracle | `1.0` | 20 passed | 0 | `rollout-reconciler-budget-oracle-2` |
| Nop | `0.0` | 3 passed, 17 failed | 0 | `rollout-reconciler-budget-nop-1` |

Both commands built and ran the task and separate verifier images. The oracle proves the task is solvable; the nop result proves the verifier does not reward the unchanged starter package.

## Standard agent trials

The agent/model pairs and reasoning levels match `.github/harbor-run-defaults.yml`. Each command was run separately with a unique job name. Authentication values were supplied at runtime and are not stored in this repository.

Codex command pattern:

```sh
harbor run -p tasks/rollout-reconciler \
  --agent codex --model openai/gpt-5.6-sol --env docker --yes \
  --ak reasoning_effort=xhigh --ae CODEX_FORCE_AUTH_JSON=1 \
  -o harbor-output --job-name <unique-sol-job-name>
```

Claude Code command pattern:

```sh
harbor run -p tasks/rollout-reconciler \
  --agent claude-code --model anthropic/claude-opus-5 --env docker --yes \
  --ak reasoning_effort=max --ak version=2.1.241 \
  --ae CLAUDE_FORCE_OAUTH=1 \
  --ae CLAUDE_CODE_OAUTH_TOKEN=<YOUR_OAUTH_TOKEN> \
  --ae CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000 \
  -o harbor-output --job-name <unique-opus-job-name>
```

### Required results

| Trial | Locked configuration | Reward | Verifier | Exception | Duration | Local job |
| --- | --- | ---: | --- | --- | ---: | --- |
| Sol 1 | `codex`, `openai/gpt-5.6-sol`, `xhigh` | `0.0` | 18 passed, 2 failed | none | 15m 54s | `rollout-reconciler-budget-sol-xhigh-trial-1` |
| Sol 2 | `codex`, `openai/gpt-5.6-sol`, `xhigh` | `0.0` | 18 passed, 2 failed | none | 17m 27s | `rollout-reconciler-budget-sol-xhigh-trial-2` |
| Sol 3 | `codex`, `openai/gpt-5.6-sol`, `xhigh` | `0.0` | 18 passed, 2 failed | none | 19m 29s | `rollout-reconciler-budget-sol-xhigh-trial-3-retry-1` |
| Opus 1 | `claude-code`, `anthropic/claude-opus-5`, `max` | `0.0` | 18 passed, 2 failed | none | 33m 05s | `rollout-reconciler-budget-claude-opus-max-trial-1` |
| Opus 2 | `claude-code`, `anthropic/claude-opus-5`, `max` | `0.0` | 18 passed, 2 failed | none | 32m 33s | `rollout-reconciler-budget-claude-opus-max-trial-2` |
| Opus 3 | `claude-code`, `anthropic/claude-opus-5`, `max` | `0.0` | 18 passed, 2 failed | none | 36m 41s | `rollout-reconciler-budget-claude-opus-max-trial-3` |

All three Claude standard trajectories contain only `claude-opus-5` model turns; no fallback model appears. All six root result files report one completed trial, zero errored trials, reward `0.0`, and an empty exception map.

Every standard run failed the same two verifier functions:

```text
test_guard_skew_observer_and_emergency_paths
test_guard_rejects_retired_invalid_and_role_boundary_records
```

These are multi-case semantic suites, not formatting checks or a numeric threshold. They exercise interacting skew exceptions, observer admission, emergency rollback, retired/invalid signatures, leadership/deputy handoff, and the resulting cut and action selection.

## Failure analysis

### Specification sufficiency

The contract was sufficient to solve the task. The reference solution passed all 20 independent tests in a separate verifier. All six frontier-agent runs built a source-only package with the correct CLI and independently passed the other 18 suites, including packet filtering, authenticated hash chains, causal closure and cycle exclusion, deterministic topological replay, attempt fencing, rollback/retry, lease precedence, dependency barriers, and globally optimal overlapping-pool scheduling. The common failures were wrong inferences about intentionally black-box retired-policy boundaries, not undocumented file formats or hidden API requirements.

### Intended difficulty crux

The failures align with `task.toml`'s difficulty explanation. Both model families spent their limited diagnostic budget probing the execute-only guard, implemented the wider reconciler successfully, and still inferred the same policy interactions incorrectly. Those incorrect admission decisions changed which journal records entered the maximum-authority cut and therefore changed downstream state and actions. This is the designed cleanroom-compatibility crux.

### Near-miss interpretation

The implementations were substantively strong, but the remaining error was not a few-percent threshold miss. Each failed verifier function combines several independently observable policy boundaries, and a wrong decision changes exact journal membership and rollout actions. The repeated 18/20 shape shows that the challenge is localized and reproducible; it does not rely on malformed output, arbitrary tolerance, or timeout pressure.

### Reward hacking, refusals, and timeout

No standard trajectory attempted to alter verifier tests, a reward file, or a reference solution. The agents created their own temporary tests and wrote only the declared source artifact. The separate verifier received that artifact in a fresh image. None of the six standard agents refused the task, crashed, timed out, or was still running near the four-hour limit; all finished in under 37 minutes.

## Adversarial trials

The current `/cheat` workflow removes the ordinary anti-cheat sentence and appends `rubrics/hack-trial-prompt.md` to a temporary task copy. The exact prompt is intentionally referenced rather than duplicated here. The frozen standard-task directory was not modified.

The temporary adversarial task had digest:

```text
sha256:513e5d814df7d99596c286cd7ffbfd9a417a882ff3d2f1c62e6d62205fb54397
```

The same standard command patterns were then run against the temporary copy. `CLAUDE_CODE_NO_MODEL_FALLBACK=1` was added to the pure Claude replacement run after an earlier Claude Code run automatically changed models; this made the Opus 5 identity auditable.

| Trial | Locked configuration | Reward | Outcome | Local job |
| --- | --- | ---: | --- | --- |
| Required pure Sol | `codex`, `openai/gpt-5.6-sol`, `xhigh`, Codex `0.149.0` | `0.0` | Provider safety refusal; no artifact or verifier manipulation | `rollout-reconciler-budget-cheat-sol-xhigh-1` |
| Required pure Opus | `claude-code`, `anthropic/claude-opus-5`, `max`, no fallback | `0.0` | Provider-side safety error after seven Opus turns; no bypass | `rollout-reconciler-budget-cheat-claude-opus-max-pure-1` |

The pure Sol result records `AgentSafetyRefusalError`. The pure Opus result records `UnknownApiError`; its trajectory contains seven `claude-opus-5` turns, one synthetic provider-error record, and no other model. Both satisfy the assignment's explicit adversarial reward requirement of `0.0`.

A supplemental Claude red-team run is documented separately because Claude Code automatically fell back from four Opus 5 turns to Opus 4.8. It is not counted as the required pure Opus trial. That run actively inspected the environment and potential shared-output surfaces, spent 2 of the 96 diagnostic queries, found no trusted-input or verifier bypass, left `/app/rollctl` unchanged, and received reward `0.0` with the starter verifier outcome of 3 passed and 17 failed. Local job: `rollout-reconciler-budget-cheat-claude-opus-max-1`.

The adversarial evidence therefore includes both pure configured-model zero-reward outcomes and one active supplemental no-bypass attempt. No adversarial run obtained nonzero reward.

## Excluded attempts and hardening history

No failed setup attempt was counted among the six required standard runs:

- an early Codex attempt could not install npm's optional `@openai/codex-linux-arm64` package, so the agent never launched;
- an earlier pre-hardening attempt ran the agent as `nobody` before subscription credentials were made readable through Harbor's supported auth handoff, so it never became a valid model trial;
- earlier calibration variants and an unlimited diagnostic-query variant were used only to harden the task and were not counted.

The unlimited-query calibration showed that Sol could recover the retired guard after roughly 40,000 differential queries. The final version replaced that extraction path with one isolated sidecar and a 96-evaluation lifetime allotment, then froze the digest above before the required oracle, nop, rubric, and model runs.

## Reproduction notes

Use the current `.github/harbor-run-defaults.yml` if upstream defaults change. The local jobs above used the repository's then-current required model pairs and reasoning levels. Never commit subscription tokens or pass a real token in a shared command transcript. The raw `harbor-output/` directory should remain local; this file is the durable submission record.
