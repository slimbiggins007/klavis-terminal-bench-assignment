# Design and validation notes: `rollout-reconciler`

This document makes the design judgment behind [`tasks/rollout-reconciler`](tasks/rollout-reconciler)
legible to a reviewer. It supplements [`EVALUATION.md`](EVALUATION.md), which holds the exact commands,
configurations, and raw results. **Nothing under `tasks/rollout-reconciler/` was modified to produce this
document**; the frozen task digest recorded in `EVALUATION.md` is unchanged. Everything here is analysis of
that frozen task and of the trajectories it produced.

The task has four layers: (1) reverse-engineer a retired admission/authority policy exposed only through an
execute-only diagnostic under a fixed query budget; (2) recover a maximum-authority, causally closed,
acyclic cut from forked SHA-256 hash-chained journals; (3) replay a lease-fenced state machine
deterministically under duplicate and reordered delivery; (4) plan rollout actions under overlapping
capacity pools by global optimization. All six standard trials solved layers 2–4 and failed on layer 1.
This document therefore concentrates on layer 1: why its budget is defensible, how its verifier is
hardened, what the available evidence does and does not establish, and exactly how the frontier models
failed.

---

## 1. Why 96 is a defensible experimental budget

The difficulty of layer 1 comes from a fixed budget: the `journal-guard` sidecar answers at most 96 JSONL
requests for the lifetime of the environment (`__remaining__` reports the balance without spending it). The
design intent is that the budget rewards *experimental design* and defeats *brute-force extraction*. The
calibration run recorded in `EVALUATION.md` supports this directly: with the budget removed, Codex recovered
the policy only after roughly 40,000 differential queries — an enumeration strategy that 96 queries make
impossible.

The constructive argument for 96 is a probe-allocation sketch. The retired policy decomposes into sub-rules
that can be isolated with targeted requests against a reusable passing baseline. The counts below are an
analytical allocation derived from the policy structure, not a measured transcript, a proof of minimality,
or a claim that every investigator will follow this sequence. The oracle proves a correct policy is
*accepted*; this section explains why targeted recovery is plausible within the budget. Baselines may be
reused across rows, and `policy_migration.md` already narrows several rules.

| Policy dimension to recover | Discriminating probes | Approx. budget |
| --- | --- | --- |
| Quorum is weighted, on **unique** acks from **healthy** configured zones only | vary zone weights, duplicate acks, unhealthy-zone acks, and unknown names | 6 |
| Deputy/observer quorum increment equals the **smallest healthy-zone weight** (not a constant) | sweep ack weight across the boundary for deputy and observer with two distinct `minHealthy` values | 6 |
| Signature validity: `ed25519` always; `legacy_hmac` only if `term ≤ legacy_hmac_through_term`, role `leader`, non-emergency, not `rollback_completed`; `invalid` never | one probe per conjunct, plus a passing baseline | 7 |
| Attempt must be positive; term must be current or exactly one back | boundary probes at attempt 0/1 and term T, T−1, T−2 | 4 |
| Role/handoff/kind coupling: leader≠handoff; deputy⇒handoff and rollback/deploy; observer⇒health, no handoff | one probe per gate | 8 |
| Current-term emergency path: rollback + `ed25519` + ack equals **total** healthy weight | flip each conjunct off a passing baseline | 5 |
| Stale-handoff (T−1) emergency path: emergency + handoff + rollback + `ed25519` + ack equals total healthy | flip each conjunct | 6 |
| Two skew exceptions: `health_failed`+`ed25519`+ack≥required+`minHealthy`; stale emergency `rollback_started` | probe skew just inside/outside each widened window | 6 |
| Authority formula: `10·ackWeight` bands + role/signer/term/emergency bonuses + per-quarter clock decay, floored at 1 | read the integer authority from ~8 accepted probes and solve the linear form | 10 |
| Reserve for a second pass on any dimension that surprises | — | 15 |
| **Total** | | **~73 / 96** |

The sketch spends about 73 evaluations, including a 15-query reserve. It therefore gives a concrete reason
to regard 96 as a defensible experimental budget while stopping short of claiming that solvability was
demonstrated by an executed 73-query transcript. The intended distinction is between discriminating
experiments and enumeration; the unlimited-query calibration showed that the latter does not fit.

---

## 2. Verifier threat model

The verifier is designed so that the candidate must implement the protocol rather than exploit an answer
leak or verdict channel. The following controls reduce the attack surface:

- **Separate verifier image (`environment_mode = "separate"`).** Tests and ground truth are baked into
  `tests/Dockerfile` and are absent from the agent environment. The agent never sees the reference
  implementation, the expected outputs, or the test source.
- **Opaque artifact boundary.** Only the declared artifact `/app/rollctl/` crosses into the fresh verifier
  image, where the diagnostic is not installed. The verifier enforces a source-only boundary before running
  anything:
  non-executable regular `.py` files only, no symlinks, no bytecode/archives/binaries, ≤131072 bytes. This
  specifically prevents smuggling the execute-only oracle binary out as the "solution."
- **Privilege separation.** The candidate CLI runs as `nobody` with `no-new-privs`; the verdict is written
  to `/logs/verifier/reward.txt` by `root` after the candidate process group is killed. A candidate cannot
  write its own reward or read hidden verifier logic. `test_candidate_identity_cannot_read_hidden_verifier`
  asserts this invariant, and the unchanged starter package already passes it.
- **Semantic grading.** Tests compare full `plan.json` outputs against an independently written reference
  reducer over many generated packets (forks, cycles, unreachable suffixes, lease fencing, overlapping
  pools). There is no trivial checksum or fixed-artifact shortcut to satisfy.

**Adversarial results and their honest limits.** Both required pure-model `/cheat` trials returned reward
`0.0`, but for a reason that must be stated plainly: each provider's safety filter refused the
Terminal-Bench red-team prompt before the model completed an attack (Codex refused on the first turn; Opus 5
performed reconnaissance and then returned a `model_refusal_no_fallback`). A refusal-driven `0.0` is a
non-result, not evidence of hardening. The strongest active evidence in this repository is the supplemental
red-team run (which fell back to Opus 4.8 and so is documented separately in `EVALUATION.md`): it performed
22 tool calls, enumerated the shared `/logs` mounts, tested writes to the verifier and artifact-output
directories, searched the whole readable filesystem for reference or expected-output files, and found no
accessible answer key or trusted verdict input. The repository's separate verifier image independently
establishes that the diagnostic is absent there. The run left `/app/rollctl` untouched and scored `0.0`.

**What is not proven:** exhaustive resistance to a fully engaged attacker. The optional `/fortify`
hacker–fixer loop would add evidence from a different adversarial workflow, but it was not run at submission
time: it can take hours, needs additional credentials, and could surface a change that would require
re-freezing the task and repeating the full evaluation cycle. The trade was deliberate — preserve a fully
validated, digest-stable submission over a last-minute robustness sweep. The controls above and the one
active no-bypass run are evidence of hardening, not proof of non-exploitability.

---

## 3. Empirical failure taxonomy

Each trial's collected `/app/rollctl/` artifact was retained, so the failures are read from the code the
models actually shipped, not inferred from the policy. All six standard trials (three Codex GPT-5.6 Sol
xhigh, three Claude Opus 5 max) passed 18/20 and failed the same two suites:
`test_guard_skew_observer_and_emergency_paths` and
`test_guard_rejects_retired_invalid_and_role_boundary_records`. Both are layer-1 admission-boundary suites.

**Universal finding 1 — the data-derived quorum increment was missed, 6/6.** The oracle admits a deputy or
observer record only when acknowledged weight reaches `quorum_weight + minHealthy`, where `minHealthy` is
the smallest positive weight among currently healthy zones. None of the six artifacts computed that value.
They replaced the data-dependent rule with different approximations:

| Run | Implemented nonleader threshold |
| --- | --- |
| Codex 1 | strict `ack_weight > quorum_weight` |
| Codex 2 | a fixed increment above quorum |
| Codex 3 | `quorum_weight + ceil(quorum_weight / 4)` |
| Opus 1 | strict `ack_weight > quorum_weight` |
| Opus 2 | fixed role margins: deputy `+1`, observer `+2` |
| Opus 3 | deputy `+1`; observer records rejected entirely |

This is convergence on the same *abstraction error*, not identical code: each run treated the nonleader
threshold as a function of quorum or role rather than of the healthy-zone topology.

**Universal finding 2 — both skew exceptions were mis-specified, 6/6.** The ordinary `health_failed` window
doubles only when the signer is `ed25519` and acknowledgment weight reaches the role's required threshold
plus another `minHealthy`. The six artifacts variously widened every failure, only observer failures, only
leader failures, or an emergency-only failure path; none implemented the complete conjunction. The other
wide path is narrower than the models inferred: for a one-term emergency handoff, only
`rollback_started` receives the doubled window. Every artifact mishandled the distinction between stale
`rollback_started` and stale `rollback_completed`; most widened both, while one Codex run widened completion
to three times the ordinary window.

These common misses map directly to the two repeated verifier failures without claiming that one threshold
mistake explains both. `test_guard_skew_observer_and_emergency_paths` combines the observer threshold,
negative-health widening, and stale-start behavior. `test_guard_rejects_retired_invalid_and_role_boundary_records`
includes a stale `rollback_completed` record outside the ordinary skew window, plus current-emergency and
role/signer boundaries. A wrong admission decision changes journal membership and can cascade into a
different state and action plan.

**A useful negative result — authority arithmetic was not the problem.** All six artifacts recovered the
ten-point acknowledgment bands and an algebraically equivalent authority formula, including role, signer,
term, emergency, and started-quarter clock-decay adjustments. Some represented the same score with a shifted
base and negative offsets. Those are equivalent parameterizations, not calibration errors, and all six
passed the authority-focused verifier suite. The failures were in admission interactions.

**What the models got right.** All six independently implemented canonical SHA-256 event hashing, cross-source
causal closure with cycle and unreachable-suffix exclusion, deterministic topological replay under duplicate
and shuffled delivery, lease-epoch fencing, rollback-before-retry ordering, and globally optimal scheduling
across overlapping pools. The failures are localized precisely to the black-box policy-inference layer the
task was built to stress, which is the difficulty crux stated in `task.toml`.

---

## 4. What this task demonstrates

The result is not merely "a benchmark that is hard," but a *controlled inference problem*: one hidden policy,
an explicit argument for why targeted recovery fits the experiment budget, and six frontier runs across two
model families with measurable, localized failures. The models converged on the same class of abstraction
error — replacing policy-data interactions with simpler heuristics — while succeeding on the surrounding
distributed-systems reasoning. That combination makes the difficulty diagnosable rather than opaque.
