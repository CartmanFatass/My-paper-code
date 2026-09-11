Claim: This fixed-policy evaluation tests whether executing the four already-trained N7 B01 final policies by one masked-categorical sample per decision (the training-time execution) changes native post-loss recovery relative to the token-greedy execution used in the B01 evaluation, on one fresh shared episode panel.
Binding MARL structure: (a) roster change; one unannounced executor loss changes available entities and multi-agent recovery coordination. The learners are unchanged; only the deployment-time action extraction differs.

# VNFC N7 B01 deployment-mode evaluation science card

Object: `VNFC-N7-B01-DEPLOYMENT-MODE-EVAL`. Evidence class: `B/EXPLORE`, fixed-policy
performance extension of the existing B01 two-seed evidence. Selected by the complete
2026-09-05 direction Convergence decision (`PRO_FINAL`, archive
`pro_packets/20260905_b01_two_seed_convergence/archive/RESPONSE.md`, full-file SHA256
`76ad3a5704677182556a1b985a4ac8903f73449537dc136bf2eeab991f787c62`), applied in
`VNFC_B01_TWO_SEED_CONVERGENCE_INTAKE_20260905.md`. Frozen by the Claude Code research hub on
2026-09-05 after the owner's resume instruction (21:26 PDT). This card fixes the observation,
its inputs and its budget; it authorizes no training, no new Pro request and no launch by itself.

Evidence spec §11.8.3 applies verbatim: "repeated evaluation of one checkpoint, another fold on
the same data, or more rollouts is not a new training sample." The object adds zero training
instances, zero optimizer work and zero new learners. It is not another B01 seed, not a diagnostic
made prerequisite to future learning, and not a search over policies, temperatures or checkpoints.

## Question, population and preserved task

The B01 runner draws one masked-categorical command per decision from the learned distribution
during training rollout (uniforms supplied) and evaluates checkpoints with token-greedy extraction
(uniforms `None`). The Convergence answer names this source-supported difference and asks whether
deployment mode changes recovery. The falsifiable hypothesis is that the two modes give different
native post-loss returns for the same trained policy; sampling may be worse, and DIRECT may
benefit as much as MAPR. Nothing here is an observed defect of B01.

Population and task are the accepted B01 host, unchanged: the R02 two-zone native host with one
unannounced executor loss, post-loss roster N7, six post-loss joint decisions, 240 native ticks and
the complete 120 s post-loss process per episode; public actor observations, canonical entity and
role mapping, legal masks, the four-token physical action grammar, CPU binary64 and the existing
single compute thread. Native service and demand definitions and the complete terminal are
preserved. Administrative identifiers (episode, world, seed, mode, checkpoint) never enter actors.

## Inputs: the four saved final policies

| Training seed record | Arm | Checkpoint | Source sha of the training run |
| --- | --- | --- | --- |
| `b01_formal_20260905_02` (masters 2026090501/2026090502) | MAPR-4 | round-64 final | `33e08f440c2117dcfd9457d825f42fef7b38ccd7` |
| `b01_formal_20260905_02` | DIRECT-SET-AR | round-64 final | same |
| `b01_seed02_20260905_01` (masters 2026090503/2026090504) | MAPR-4 | round-64 final | same |
| `b01_seed02_20260905_01` | DIRECT-SET-AR | round-64 final | same |

Local copies: `C:/Projects/HMASD-worktrees/cm-vnfc-n7-b01-20260905/temp/directions/variable_n_fleet_churn/<record>/checkpoints/MAPR_final.pt` (2,168,441 bytes) and `DIRECT_final.pt` (3,607,517 bytes), written by the B01 runner's `checkpoint()` as `torch.save` dicts with keys `arm`, `checkpoint`, `round`, `model_state`, `optimizer_state`, `dtype="float64"`, `device="cpu"`, `presentation`; remote copies in each accepted task's exact-source cwd on `wsl_4070`. CM verifies the actual files, records their SHA256 and the load path, confirms `round == 64` and the parameter count on load, and stages them to the execution node at those digests before any launch. `optimizer_state` is loaded by nothing. No initial or midpoint checkpoint, no replacement policy, no parameter update.

## Treatments and comparison

Two preset execution modes for every one of the four policies, nothing else:

- `GREEDY`: the existing evaluation path, token-greedy extraction with uniforms `None`: the
  masked-logit maximum with the deterministic opaque-rank tie-break already in the shared
  forward (`variable_n_fleet_churn_bpcr_r09/torch_models.py`, the `uniforms is None` branch).
- `SAMPLE`: one masked-categorical command per decision from the same masked softmax, the
  inverse-CDF branch of the same forward with one uniform per token, exactly the training-rollout
  extraction, fed from a dedicated evaluation action-draw stream (new domain string, never the
  training `actions/<arm>` stream or its coordinates).

Both modes share the forward, the masks, the fixed-occupant override and the softmax; only the
final choice line differs. No third decoding path is introduced.

No temperature, top-k, nucleus, mixture, best-of-many, trajectory search, multiple draws per
world, or per-world choice of the better mode. Neither mode is tuned. Fixed BCRH-PERSIST is
executed once on the same panel as the native reference, with its complete internal
controller/checker work.

Primary contrast, per policy (four values): paired `SAMPLE` minus `GREEDY` `R_fail_60` over the
64 shared episodes. Secondary, all retained and reported: the same contrast per failed zone;
same-mode MAPR minus DIRECT within each training seed; each policy-mode against BCRH; `U_total`,
`U_intact`, `J_ext`, all episode flags and the existing 20-second context. Modes and episodes
are not independent training seeds; the independent unit remains the training seed, of which
there are two.

## Panel, RNG and prospective exposure

One new shared panel of 64 complete episodes, 32 per failed zone, disjoint from every B01 training
and evaluation episode. Namespace `VNFC-N7-B01-DEPLOYMENT-MODE-20260905`; world master seed
`2026090505`; action master seed `2026090506`. Action-draw addresses distinguish training seed
record, arm, world, epoch and token, using the existing addressed RNG mechanism. `GREEDY` consumes
no action draws. World randomness is paired across all eight policy-mode cells and BCRH.

| Planned quantity | Learned policies | BCRH-PERSIST |
| --- | ---: | ---: |
| Policies × modes | 4 × 2 = 8 cells | 1 |
| Evaluation episodes | 8 × 64 = 512 | 64 |
| Post-loss joint decisions | 3,072 | 384 complete calls |
| Native ticks including prehistory | 122,880 | 15,360 |
| Training instances, rounds, optimizer steps | 0 | 0 |

Total 576 episodes and 138,240 native ticks. These are plan counts, not completed exposure.
The runner prints actual counts and the machine-generated exposure line from actual values
(loaded parameter counts, zero parameter displacement, zero updates, actual episodes and ticks).

Minimum effect of interest (this card's own): the descriptive `.10` `R_fail_60` scale inherited
from B01, applied to the per-policy paired mode difference. Reason: B01 declared the same scale
for a learner comparison on this host, and the question is whether deployment mode moves the
same outcome by an amount that would matter to that comparison. Smaller differences are
reported, not dismissed. Headroom record: none; BCRH is a native reference whose field-by-field
information equivalence with the learners has not been established (unchanged from B01).

## Reading rule, written before the data

Report all four primary paired differences with per-episode rows retained. Descriptive branches:

1. All four `SAMPLE − GREEDY` differences at or beyond `+.10`: deployment mode is a candidate
   explanation for part of the learner-versus-BCRH gap; report, and return the question of a
   changed evaluation protocol to Convergence. This does not select training.
2. All four at or beyond `−.10`: greedy extraction is the better deployment for these policies;
   B01's evaluation protocol stands and the question closes at this exposure.
3. Mixed signs or all within `(−.10, +.10)`: no useful deployment-mode signal at this exposure;
   the question closes at this exposure without escalation to temperature, more draws, more
   panels or more checkpoints.

Same-mode MAPR–DIRECT and BCRH contrasts are context; they cannot be re-read as a new learner
result, and a positive branch does not automatically select subsequent training. Mixed per-zone
signs and service costs are retained and reported in every branch.

Predictions on record. DM (hub): branch 3 is most likely; if a mode effect exists it is more
likely negative for `SAMPLE` (greedy already extracts the mode of a distribution trained to
peak), and any mode effect is smaller than the B01 learner-versus-BCRH gap. Owner prediction
slot: not taken (unattended) unless the owner replies before launch.

## Complete cost and stop boundary

The complete selected invocation is capped at **180 s wall** on the executing node, covering
import, native build or load, checkpoint loading, world setup, all eight policy-mode cells, the
BCRH panel, output and readback. It is charged to B01's original 2,700 s cumulative formal
budget: 783.29 s wall is already spent; full use of this cap gives 963.29 s. Dominant work is
`8 × 64 + 64 = 576` complete episodes at 240 native ticks, with `3,072` four-token policy
decisions and `384` BCRH calls. Reusable timing from the accepted B01 technical acceptances: the
three-checkpoint greedy evaluation phase took 3.29 s (MAPR) and 3.43 s (DIRECT) for 192 episodes
in formal_02, about 1.1 to 1.4 s per 64-episode checkpoint; one BCRH panel pass took 46.38 s
(formal_02) and 37.75 s (seed02). Projection: 8 cells × about 1.4 s plus one BCRH pass of about
46 s is under 60 s of evaluation wall; the native shared-library build, checkpoint loading, the
new entry's own setup and publication are unmeasured, and unknown is not zero. The 180 s cap is
the complete bound, not a target.

If the complete path does not fit the cap, or a primary dependency (checkpoint bytes, native
library, panel construction) is missing, the CM returns that concrete gap. No smaller
outcome-selected comparison, no partial cell set called a result, no automatic retry.

## Implementation and proportionate verification assignment

CM adds one evaluation-only entry that loads the four final checkpoints and runs the two modes
and BCRH on the shared panel, reusing the B01 module's model classes, `rollout`, `worlds`,
`bcrh`, native adapter and JSON publication without changing their semantics. The B01
`experiment.run` always initializes fresh models and trains, so the new entry imports the B01
module directly and never calls `run`. Facts the CM must respect, from the read-only map of
2026-09-05: `rollout` builds uniforms only under its `training` flag, which also switches PPO
bookkeeping, so the module may gain one optional argument that supplies evaluation uniforms with
`training=False` and leaves every existing call byte-identical in behavior when the argument is
absent; a DIRECT model reconstructed outside `initialize` needs `residual_observation` set before
its first forward; model construction needs exact-shape finite float64 CPU placeholders before
`load_state_dict`; `readout` assumes the six B01 cells and is not reused unmodified for the
policy × mode grid. Owned paths: `scripts/run_vnfc_n7_direct_b01_deployment_mode_eval.py` (one
argparse entry, fixed card defaults, one result root); `experiments/candidates/variable_n_fleet_churn_n7_direct_b01/`
(the B01 module, owned by this direction) for the minimal additions above;
`tests/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/` for the focused check;
direction-local implementation record. R09/R02 modules, `scripts/run_vnfc_bpcr_*.py` and shared
core are read-only reuse inputs; a needed modification there returns to the hub first. The
existing B01 formal and check invocations must remain unchanged in behavior: the focused check
includes a greedy-path equality check against a recorded B01 evaluation row where the panel and
checkpoint make one available, or states why none is.

Engineering Scope Spec §4 additions: none. Ordinary source and test budgets apply. No pool,
retry system, repeated smoke, registry, telemetry beyond wall and peak RSS, or root-cause
investigation of the historical HMAC/SIGSEGV events; the existing fatal-stack observation is
retained as it is.

Focused check, one invocation: load one checkpoint; on a two-episode panel confirm that
`GREEDY` reproduces the B01 evaluation decoding for the same inputs, that `SAMPLE` consumes
declared action draws and respects legal masks, that BCRH executes, that episode identities are
disjoint from B01's namespaces, and that the summary reports zero updates and the exposure line.
No historical replay, bit-equality gate or all-intermediate output.

Execution: remote-first on `wsl_4070` under `.codex/hmasd-compute.toml`, CPU binary64, one
compute thread, exact committed and pushed source, detached `agent-task` supervision, fresh
memory admission immediately before the invocation with both 4 GiB floors. Checkpoint bytes are
frozen evidence inputs staged at their declared digests. Launch conditions are the evidence-spec
§11.4 items and nothing else.

## What technical success cannot establish

A completed run establishes the paired mode difference for these four policies on this panel.
It cannot establish MAPR superiority or equivalence, a population-stable deployment effect, an
optimal execution protocol, the cause of the learner-versus-BCRH gap, cross-N or churn transfer,
or any correctness defect in B01. It is one bounded observation under `B/EXPLORE` on the
declared host and device.
