# VNFC B01 first focused-check intake and one selected retry

Date: 2026-09-05. Object tier, `OWNER_DELEGATED`; kind `selection`, owner flag `none`.
The DM selects one unchanged non-target focused-check invocation in a new directory. This is
an explicit decision under standing delegation, not an automatic retry or a formal B launch.
The scientific card, source, inputs, comparison and existing per-invocation bounds are unchanged.

## Evidence read and bounded observation

Read the complete B01 science card, CM handoff, engineering contract at `14d4190b4`, engineering
status and all four retained logs/receipts at `82401338b`. Inspected the actual runner configuration
and initialization boundary. Read current main AGENTS, evidence-spec §11.8–11.9, scientific-tool
skill and GitHub collaboration guide. Owner-console reviews returned `[]`; the September4/5
audit owner columns contain no new instruction conflicting with this selection. The existing
VNFC continue-at-low-priority reply remains applied. Root owns the shared audit and owner-console
write for this direction handoff.

[Draft PR #2](https://github.com/CartmanFatass/My-paper-code/pull/2) was read through the GitHub
connector: open, draft, head `82401338bfc7ba129c8ca450454f8ce0a367a57e`, not merged. Its body
correctly distinguishes independent source review from incomplete runtime verification and refers
to Issue #1. The review reports no unresolved material source finding; it does not prove runtime
correctness.

The first focused check ran exact source `33e08f440c2117dcfd9457d825f42fef7b38ccd7` on
`wsl_4070`, task `vnfc_b01_check_33e08f440_20260905_01`, and exited1. Fresh admission passed with
15,423,397,888 physical/effective available bytes. The full failed chain consumed 3.90s wall,
2.90 user + 0.38 system = 3.28 CPU-s; maximum RSS was381,308KiB as measured by `/usr/bin/time`.

Native build/load completed, then the unchanged R01 RNG helper called `hmac.new` during
`learning.initialize`. Python3.10 stdlib raised:

> AttributeError: 'HMAC' object has no attribute 'digest_size'

No native world reset/rollout, learner update or evaluation occurred, and output pytest was
not reached. Non-target RNG initialization had begun; this is not a claim of zero RNG activity
or zero partial parameter construction. Formal seeds/namespace were not run. These facts support
only an incomplete engineering preparation, with no positive or negative algorithm reading.

The following counterevidence is retained separately:

- Four literal HMAC calls with stdlib alone, four after importing the committed learning module,
  and10,000 after loading the same built library all passed, as recorded by CM.
- The same committed `learning.initialize(2026090591, "B01-ENGINEERING-CHECK")`, same actual
  library and one-thread setting completed both model/optimizer initializations after a fresh
  admission. It exited0; the supervisor reported6s elapsed. No training or evaluation was run.

The full-context original failure remains unreproduced. The successful narrower checks neither
locate its cause nor establish that the full runner is healthy. There is no direct evidence for
a source repair, a node defect, an HMAC implementation substitution or a dependency upgrade.

## Rule and decision

Evidence-spec §11.8.7 says: “Root-cause attribution requires direct evidence, but reproducing and
uniquely locating every historical cause is not a universal prerequisite for later work.”
The engineering contract says: “Stop on a concrete failure or bound; preserve partial facts,
do not automatically relaunch or change inputs.” CM complied by returning the first failure.
That clause requires a new object-tier selection; it does not require a repeated owner vote,
a Pro round, or a complete causal diagnosis before that selection can be made.

| Option | Decision value and risk | Selection |
| --- | --- | --- |
| A. One unchanged full non-target check in a new directory | Reaches the still-unobserved real collection/update/evaluation/output path and its applicable costs; same initialization has subsequently succeeded. The original symptom may recur. | Recommended and selected |
| B. Continue only smaller HMAC/root-cause diagnostics | May eventually explain the exception, but the completed smaller checks have not discriminated a cause and do not cover the needed learner/output path. | Not selected now |
| C. Patch HMAC, replace dependencies or change the experiment | No source-supported repair; changes RNG/runtime semantics or scientific work without a demonstrated need. | Not selected |
| D. Launch formal B directly | Lacks a completed changed-path check and complete learner-cost evidence; exposes the actual scientific seed before the concrete gap is resolved. | Not selected |

Owner-delegated decision (unattended, 2026-09-03 instruction): **A, exactly one unchanged
non-target retry**, designated check02. This is a reversible object-tier engineering selection
inside the accepted B mechanism. It changes no arm, scientific seed, population, reward,
information, checkpoint selection, recast count, lifecycle or Portfolio priority.

The strongest objection is a latent intermittent failure that the narrower checks missed. The
selected full check is useful precisely because it exercises that context and the real learning
and primary-output dependencies. A second success would not prove the cause absent; another
failure would be preserved as a concrete observation and returned without an automatic third
invocation. No claim is conditioned on obtaining a favorable non-target return.

## Unchanged prospective work and cost

The scientific-tool counting method was applied to the actual `config = dict(...)` AST in
`scripts/run_vnfc_n7_direct_b01.py`, with `profile=engineering-check`, seed2026090591 and
eval-seed2026090592. Only the configuration expression was evaluated; no learner, model, RNG,
simulation or experiment was created by this calculation.

| Planned check02 quantity | Each learner | Whole check |
| --- | ---: | ---: |
| Rounds × complete training episodes | 2 × 32 | 128 training episodes |
| Joint training transitions | 384 | 768 |
| PPO epochs × minibatches per round | 4 × 8, minibatch24 | matched arms |
| Optimizer steps | 64 | 128 |
| Learned-policy evaluation episodes | 24, three checkpoints × 8 | 48 |
| Fixed BCRH evaluation episodes | none | 8 |
| All complete episodes | 88 | 184 including BCRH |
| All joint decisions | 528 | 1,104 including BCRH |
| All native ticks | 21,120 | 44,160 including BCRH |
| Complete BCRH calls | none | 48 |

The namespace remains `B01-ENGINEERING-CHECK`; training/evaluation seeds remain2026090591/592.
These are prospective totals, not exposure achieved by check01. The original300s complete
per-invocation check bound remains, including imports/build, both learner paths, BCRH, publication
and output pytest. This explicitly selected additional invocation does not erase the prior3.90s
or diagnosis work. Preserve each actual cost and its measurement type; the initialization
diagnostic's6s supervisor duration is not a precise `/usr/bin/time` wall/CPU measurement.

The formal object's cumulative complete2,700s wall bound is unchanged. Its per-arm collection,
update and evaluation costs, BCRH cost, complete publication cost and overall fit remain unknown.
Do not fill them with zero, extrapolate from the failed3.90s initialization, or treat the successful
initialization diagnostic as a learner benchmark. Obtain applicable phase costs in this same
necessary full check; no independent cost A, extra profile or repeated smoke is selected.

## Exact selected check02 handoff

CM reuses the reviewed committed source with no code, library-source, input or environment
changes. Build the same native source normally into the new output directory; do not substitute
an old checkpoint, HMAC implementation or undocumented prebuilt library. The only administrative
changes are the task, worktree/output/receipt paths and their new invocation identity.

- Source SHA: `33e08f440c2117dcfd9457d825f42fef7b38ccd7`.
- Node: configured `wsl_4070`, existing Python interpreter; CPU binary64 and single-thread
  Torch/BLAS/native settings unchanged.
- Detached worktree/cwd: `/home/wu/hmasd-worktrees/vnfc_b01_check_33e08f440_02`.
- Supervisor task: `vnfc_b01_check_33e08f440_20260905_02`.
- Relative root: `temp/directions/variable_n_fleet_churn/b01_check_20260905_02`.

The following is the one selected supervised command; line breaks are presentation only:

```sh
cd /home/wu/hmasd-worktrees/vnfc_b01_check_33e08f440_02 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/variable_n_fleet_churn/b01_check_20260905_02/memory.json && /usr/bin/time -v -o temp/directions/variable_n_fleet_churn/b01_check_20260905_02/whole_time.txt timeout 300s bash -lc '/home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_n7_direct_b01.py --profile engineering-check --seed 2026090591 --eval-seed 2026090592 --launch-sha 33e08f440c2117dcfd9457d825f42fef7b38ccd7 --out temp/directions/variable_n_fleet_churn/b01_check_20260905_02/output && VNFC_B01_CHECK_ROOT=temp/directions/variable_n_fleet_churn/b01_check_20260905_02/output /home/wu/.venvs/hmasd/bin/python -m pytest -q tests/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/test_output.py'
```

Commit and push this selection before launch. Run the fresh destination-node admission adjacent
to the invocation; an old receipt is not reusable. CM retains launch/technical acceptance, hands
the accepted task to the shared tracker and returns complete logs, actual exposure, readable
outputs, projection assumptions and any concrete failure to DM/Root. Keep check01 and the
diagnostic artifacts. An uncertain launch acceptance is resolved from the supervisor state,
not by creating another task. No accepted check02 exists at this intake's creation.

If check02 completes, interpret it only as technical evidence for the declared non-target path
and a conditional cost projection. Retain the original unexplained exception in subsequent
engineering intake. If it fails or times out, stop that invocation and return the precise
remaining dependency; no automatic third check, speculative patch or formal run follows.
The formal B remains unstarted until its actual changed path and complete budget can be assessed;
there is no requirement to uniquely explain every old failure or add another Pro approval.

## Shared-record handoff

Root should append an object-tier selection row and owner item with optionA `auto_applied`,
linking this intake and the first engineering status. The application state is “one unchanged
non-target retry selected; launch/terminal facts supplied by CM”, not “formal B ready”. No new
scientific result brief or prediction score is produced. CM may link this decision in existing
draft PR #2; no new issue, PR, approval queue or lifecycle action is needed.
