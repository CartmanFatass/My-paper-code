# RCLE B03 seed20 pair — source-read-only feasibility

2026-09-09. Preparation only, requested by DM following Root selection. Inspected
`codex/rcle` at `2299d09d30f3ed63d333ca17a02a067aa5cbae15`; starting status clean.
Accepted implementation surface is `4e89f24197a79d0b4fc724018f0223ca2c1e4289`.
No implementation, test, diagnostic, model, learner, native, admission, benchmark,
remote staging or scientific invocation occurred. Only source/document reads and
stdlib hash/count arithmetic were used. This report is the only owned edit.

## 1. Feasible minimal change

One fresh pair is technically feasible by propagating the selected seed explicitly.
The current CLI accepts only19 and never passes `args.seed`; study `make_rng()` and
summary metadata both use module `SEED=19`. Changing a CLI label alone would rerun19.

Propose changes confined to the existing B03 study/CLI and one fixed seed20 shell
command list. Preserve `OBJECT_ID="RCLE-TBCFV-B03-ACTOR100"` as the RNG namespace,
block0, and `SEED=19` as the default. Add a seed argument to `make_rng(seed=SEED)`;
add trailing keyword parameters to `run`, retaining existing positional call meanings,
and pass the parsed CLI seed into `run` and onward into `make_rng`. Permit19/20 in
argparse, default19. No module-global reassignment or monkeypatch in production.

Use a separate reporting-object argument, defaulting to the existing OBJECT_ID;
seed20 commands explicitly supply `RCLE-TBCFV-B03-ACTOR100-S20`. It changes summary
`object` only. Summary `seed` and `root_key_hex` must use the actual supplied seed;
`block_digest_hex` remains read from the authority actually passed to SemanticRNG.
Keep the reporting label, arm, coefficient, path and launch SHA out of both root
construction and semantic addresses. All three seed20 commands use the same seed and
reporting object. Default19 commands retain their original identity, root and input
contracts; the historical/recovery wrappers need not change.

No shared host/native/model/loss/optimizer/evaluator change is needed. No engineering
scope §4 machinery is proposed: `scope: none`. A fixed command list and ordinary
argparse/data plumbing suffice. Retain ordinary 2,000 new source/600 runner line
budgets; this report introduces no separate line cap or compatibility framework.

## 2. Actual propagation and independence

| Boundary | Current consumer and required effect |
| --- | --- |
| CLI -> study | `scripts/run_rcle_tbcfv_b03.py:main` must pass actual seed, not merely emit it. |
| Root -> block | `study.make_rng(seed)` computes `host.seed_root_key(f"{OBJECT_ID}/seed/{seed}")`, then `host.block_digest_hex(key, OBJECT_ID, 0)`. Both explicit namespace and block remain fixed. |
| Block -> semantic/native RNG | B01BlockAuthority exposes the digest; SemanticRNG stores its bytes as `_key`. `uniform`, native `uniform_many`, `claim_many` and `claim_compact` all consume this key. No independent native seed argument is missing. |
| Initialization | `initialize_block_models(rng)` draws common-initial-parameter uniforms through this same RNG, applies affine fixture initialization and copies the helper state into five package models. Keep FLEX only for training. The two invocations reconstruct identical initial tensors from the shared fresh root. |
| Training policy/scenarios | `training_update` passes rng and true package FLEX to both native batches per update. Fixture position/survivor/demand/event draws, manager-plan draws and actor claim sampling descend from this RNG. Changed policies may produce different trajectories despite paired random coordinates. |
| Held-out panels | `panel` -> `host.evaluate_learned(..., FLEX, rng, 256)`; reference -> `host.evaluate_scripted(rng,256)`. Existing purpose/cell domains and held-out index addresses remain unchanged. |
| Publication | `object` reports S20; `seed=20`, actual root and authority digest identify the generating root. Checkpoints remain output artifacts; none is an input. |

Stdlib SHA256 over ASCII confirmed:

- seed19: `4b17629c25d71afceed93bbe657c0b5799d468d1f5673d90a7ceee644ec474c5`.
- seed20: `065798a1a4115ac244accada16fc267f814deb622cfd05b9657418892c656e3b`.

Changing the root while retaining the existing namespace yields the intended new
pseudorandom training pair: independent from seed19 by the existing keyed RNG design,
paired within seed20 by the common root and semantic coordinates. It is not a proof
of statistical independence from observed outcomes, nor training-population certainty.
W1/W100 labels and weight never enter random addresses; both use package FLEX.

## 3. Pair source and sequential topology

The existing `host.load_control_summary` checks file/readable JSON-object shape only.
B03 `primary` checks matched unique cell/index sequences, not seed/root/object identity.
Therefore a historical W1 with the same indices could silently be compared if passed.
This is the specific affected publication boundary to cover, not a reason to add a
schema/provenance validation system. The new fixed wrapper must pass only
`$root/W1/summary.json` to W100, where `$root` is the fresh seed20 attempt root and
successful W1 precedes W100. No external control argument, historical control staging,
fitted model loading, checkpoint reuse or fallback path belongs in that wrapper.
Acceptance will read the new W1 and W100 metadata and initial tensors before accepting
the paired primary. Preserve the existing old-input API for historical19 consumers.

Proposed complete command list, after a later implementation/execution allocation
(frozen SHA, fresh root, configured interpreter and exact remote cwd supplied then):

1. Same-node `admit-memory --out "$root/W1-admission.json" &&` timed complete runner:
   `--arm W1 --seed 20 --reporting-object RCLE-TBCFV-B03-ACTOR100-S20 --wall-cap 600
   --out "$root/W1" --launch-sha "$sha" --admission-receipt "$root/W1-admission.json"`.
2. Fresh same-node W100 admission `&&` timed runner with corresponding W100 paths,
   the same seed/object/SHA and600s cap, plus `--control-summary "$root/W1/summary.json"`.
3. Fresh same-node reference admission `&&` timed runner with corresponding reference
   paths, same seed/object/SHA, `--arm reference --wall-cap 30`.

Each learned interpreter also receives outer timeout600; reference receives timeout30.
Stop the list on failed admission or nonzero exit; no retry/extra panel. Poor finite
W1 results do not stop W100. W1 owns init ->200 updates ->final publication. W100 owns
fresh init ->200 updates ->final evaluation ->primary using new W1. Reference is the
unchanged INDEPENDENT-NEAREST, with unavailable Y null. No model state crosses processes.
Three sequential interpreters on wsl_4070, CPU FP64, one compute thread each; unchanged
public native host, original in-process batches and no worker/process parallelism.
Commit/push before detached exact-SHA execution under configured agent-task; admission
immediately precedes each runner before scientific allocations. No execution performed here.

Actual training calls are two32-episode native batches per64-episode update (four cells
per batch, eight episodes per cell), then one joint backward/full-vector step. Held-out
256 episodes per cell use eight batches of32; eight cells give64 batches per panel.
Thus the complete pair has800 training batch calls plus256 panel batch calls. The
existing initializer creates six models per learned invocation, not just one.

## 4. Exposure and cost proposal

Stdlib arithmetic over the read loop constants produced:

| Work | Episodes | Primitive ticks | Backward/step calls | Models/fits/helpers |
| --- | ---: | ---: | ---: | --- |
| W1 training + init + final | 16,896 | 1,081,344 | 200 | 6 / 1 / 5 |
| W100 training + final | 14,848 | 950,272 | 200 | 6 / 1 / 5 |
| Reference | 2,048 | 131,072 | 0 | 0 / 0 / 0 |
| Total | 33,792 | 2,162,688 | 400 | 12 / 2 / 10 |

Training is2×200×64=25,600 episodes; evaluation is4×8×256=8,192.
400 step calls do not imply400 nonzero updates; record actual zero/nonzero counts.
Per-arm parameter path length is at most200×0.02=4; actual seed20 initial norm is
unmeasured until the allocated run. Historical seed19 norm21.23099 implies roughly0.1884
as a planning scale only. Agent ticks/claim decisions depend on actual episodes and
must be collected rather than fabricated as independent samples. Future technical
fixture exposure, if allocated, is separate from these scientific counts.

| Complete arm | Existing measured analogue | Proposed cap |
| --- | ---: | ---: |
| W1 including common init panel | Original B03 W1 time file79.24s | 600s |
| W100 including final publication | Recovery W10070.95s | 600s |
| Reference | Recovery reference2.59s | 30s |

These are complete same-host B03 paths; their sum152.78s is a historical planning
reference, not a seed20 measurement. Roughly150–200s runner work plus actual support
is plausible; initialization/build/cache/host contention and new checks/publication
remain unmeasured. Neither failed53.20s W100 nor recovery's100s incremental charge is
a fresh-pair throughput estimate. Each projected arm is below its original learned
cap; no arm or required panel needs removal to fit this proposal.

Propose1,500s cumulative complete-object execution wall, including at most30s for the
future focused seed-wiring check and all necessary startup/build/admission/staging/
collection/arithmetic/final publication support. Arm caps sum1,230s, leaving240s for
support after a30s check at the arm maxima. Charge actual support once and set the
outer chain timeout from the remaining object allowance; no cap reset across scripts,
no automatic extension. Reserve publication support when freezing that command.

The sequential chain critical path is close to the arm-wall sum plus admissions;
whole study elapsed also includes control-plane gaps and must be reported separately.
Aggregate CPU was not measured for the analogue and remains unknown, not zero or
identical to wall despite one compute thread. Ordinary existing timing/RSS suffices;
no profiler or resource telemetry system is proposed. The1,500s card cap is stricter
than the toy2,700s engineering investigation threshold; threshold is not extra budget.

## 5. Focused future acceptance, limits and next owner

After allocation, one bounded focused check should exercise CLI -> run -> make_rng
seed forwarding and emitted metadata, with supplied fixtures/fakes for native/model
work; compare default19 and explicit19 against the preserved root/block derivation,
then20 against the declared hash. Check label/weight/reporting/SHA changes cannot enter
root derivation and that package FLEX remains fixed. Exercise the post-learner primary
publication with distinguishable supplied new-W1 and old-W1 data so use of the wrong
control is observable; inspect the fixed wrapper's new-root path and stop-on-failure
sequence. This need not construct a scientific model or call the native backend.
No extra smoke at launch, no full historical replay and no new diagnostic experiment.

Independent semantic review is needed for changed RNG wiring and primary input binding;
reuse the existing reviewer with this narrow diff and the DM-frozen card. Review must
trace the real production consumers above, not accept metadata-only seed coverage.
At result acceptance, inspect both new initial tensors, actual seed/root metadata,
complete counts, all required final/init/reference rows, curves and paired primary.
The already working publication path is reused; the focused supplied-output check
covers its changed seed/control boundary. No historical crash cure is claimed.

Scientific interpretation remains with DM. Preserve [original card §§2–5](RCLE_TBCFV_B03_ACTOR100_SCIENCE_CARD_20260909.md)
except the explicitly selected new seed/reporting identity, and [recovered intake §§3–7](RCLE_B03_RECOVERY_RESULT_INTAKE_20260909.md):
small below-MEI U signal, saturated tau, four final-roster12 F losses, strong simple
reference, unknown H_A1 and whole-law/one-pair claim limits. The seed20 observation is
an outcome-informed selected B follow-up, not retrospective confirmation or a remedy
for missing training-population variance. No new scientific decision is made here.
Applicable evidence rules: [§4 and §5.2](../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#4-common-integrity-requirements),
[§11.4](../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#114-what-may-gate-a-b-launch), and
[§11.8.6–7](../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#1186-proportionate-verification).

No incompatible dependency was found. Current unmodified CLI/study cannot execute20;
the proposed change must be implemented and checked before a result-bearing launch.
DM next freezes card/selection; Root separately allocates implementation and execution.
The existing B03 CM is the proposed engineering owner, retaining technical acceptance;
this preparation grants no implementation or invocation allowance.
