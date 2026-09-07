Claim to test: The shared-data count-conditioned return learner retains a useful mean native acquisition gain over BLIND and IMMEDIATE-4 on two fresh independent training datasets after B02's single-dataset signal.
Binding structure: **systems / information flow**. The finite coordinator host does not instantiate multi-agent partial observability or non-stationarity; no MARL population claim is made.

# UCOPE shared-data return model B03 — two-dataset follow-up

Object: `UCOPE-SHARED-DATA-RETURN-MODEL-B03`. Class: **B/EXPLORE**.
Status: **prospectively selected and frozen before either new dataset output**.
Authority: Root's **P08-UCOPE-TWO-DATASETS-01**, plus the existing object-tier delegation.
The command covers this selection, the original CM's implementation/checks, exactly two remote
invocations and joint scientific intake. It does not authorize a third seed, B02 replay, pilot
or Pro Send. Scientific selection does not create a direction or Portfolio disposition.

## 1. Question, source and retained evidence

The next observation asks whether the useful B02 signal survives two independent new datasets,
and whether the observed seed variation supports another bounded investment. It does not seek
an exact policy maximum or a causal explanation of B01 before sampled performance exploration.

Reuse [B02 card §§1–5](UCOPE_SHARED_DATA_RETURN_MODEL_B02_SCIENCE_CARD_20260907.md), frozen at
`c4687f6f2`, for the eight contexts, native reward/information path, full/blind table learner,
shared immediate fit, balanced collection, ties and per-dataset final evaluation. The B02 source
anchor is `bcd55750b29014e21dd855df5ac320296256b62e`; its model, evaluator, runner and four
native host modules match preparation base `70b419a2ba29a1b912d438c1301f8a9543faf42b` by Git diff.
Only the explicit seed binding and B03 result identity change as specified below.

[B02 intake §§2–6](UCOPE_SHARED_DATA_RETURN_MODEL_B02_INTAKE_20260907.md) remains the prior
outcome-informed motivation: seed 6401 gave RM-A, native/information gains 0.0030012207031250046,
conditional MC SE 0.0005533139087041887, with FULL acquiring in one LINKED low-cost context.
BLIND and IMMEDIATE-4 deployed identically, so those two equal gains were not independent evidence.
Keep seed 6401 and every historical result unchanged; it is **excluded from B03's prospective
primary average**. B01's two nulls, historical false-probe losses and the stopped retained-policy
root-residual/numerical-locus family retain their meanings.

**Headroom and MEI.** No tuned generic current-host headroom record exists. The historical
0.00267963765625 oracle/reference diagnostic is not a new baseline ceiling. The MEI remains
**0.001 absolute native return for each comparison**, because host, cost scale and contrasts are
unchanged. The observed B02 controller is prior evidence, not another arm trained or replayed here.
Reuse FULL/BLIND/IMMEDIATE-4 with identical observation/action/information and per-dataset budgets.
The proposal's verified literature already motivates the native endpoint; no new mechanism,
comparator retrieval, architecture or reward change is commissioned.

## 2. Exactly two fresh datasets and preserved numerical/RNG semantics

Select **seed 6501, then seed 6502**. Each runs in a distinct process/output root with a newly
zero-initialized 264-value state and integer counts. No learned values, histogram, parameters,
checkpoint, evaluation episode or first-seed score initializes or tunes the second.

All B02 learning semantics remain: 1,024 batches × 256 rows; source `CONTEXTS` order then
`j=0..31`, with 16 IMMEDIATE-4 and 16 PROBE rows/context/batch; even support `(2,4,6,8)`;
full native return `R` from the completed actual action; update `N <- N+1`, then
`q <- q+(R-q)/N`. Probe updates full, blind and histogram from the same observation; immediate
updates the shared table once. Python binary64 scalar order, `math.fsum` expectations/moments,
unseen-cell fallback and root/tail tie choices are unchanged. There is no Torch optimizer,
bootstrap, parallel reduction or additional fitting pass.

The only scientific randomization change from B02 is the independent seed:

- The private behavior streams are `random.Random(2006501)` and `random.Random(2006502)`.
  Each supplies one `random()` per training row, including discarded immediate draws;
  probe period is `K_EVAL[int(4*uniform)]`, ignoring the count during fixed exploration.
- For either `seed`, environment ancestry is
  `("UCOPE-SHARED-DATA-RETURN-MODEL-B02", f"seed-{seed}", context_id(c))`.
  The existing **B02 RNG-family literal is intentionally retained**; B03 is the new card/result
  identity, while this replication changes only the seed component of environment addresses.
  Do not replace that family literal with B03 or mutate a global seed between datasets.
- Training index remains `32*u+j`, `evaluation=False`. Final evaluation uses indices `0..4095`,
  `evaluation=True` and existing `eval-*` namespaces. FULL, BLIND and IMMEDIATE-4 share addresses
  within each seed; the seed component separates both training and evaluation across datasets.
  Initialization and deterministic evaluation draw no policy RNG. No global RNG is used.

Root choice uses only public context and fitted training values. FULL sees the current displayed
count only after paying and uses it for duration; BLIND ignores it. Actual-mark reward in SEVERED
arrives after duration choice. Full sampled native return includes the original service, time,
energy and probe terms. No analytic value, latent regime, actual marks or unchosen-action target
enters either learner. The path remains event → public purchase → paid display → duration →
native reward → observed-action learning. No roster/lifetime or partner-adaptation claim is added.

## 3. Primary average, reading branches and prediction

Evaluate only each final batch-1,024 pair: 4,096 fresh paired indices/context/policy, all eight
contexts and all three policies. Retain each dataset's means, paired differences, conditional MC
SE, final actions, probes, costs and every context loss. Apply the unchanged per-dataset B02 RM
rule to each complete result. A negative first score does not cancel or alter seed 6502.

For `s in {6501,6502}`, use B02's `Delta_native_s` and `Delta_information_s` (uniform mean of
eight context means). The **primary** is `Delta_native_bar = (Delta_native_6501 + Delta_native_6502)/2`;
the information discriminator is the analogous `Delta_information_bar`. Report BLIND-minus-
IMMEDIATE-4 for each seed and its mean. Seed 6401 is listed as prior evidence separately;
do not add it to this primary, select the better new seed or replace a negative/incomplete result.

The independent unit is the dataset/seed, **n=2**. Report the two endpoint scores and their
sample SD (`ddof=1`); that small-sample dispersion includes evaluation noise and is not a precise
training-population variance estimate. Conditional evaluation MC SE of either two-seed mean is
`sqrt(SE_6501^2 + SE_6502^2)/2`, using the existing within-seed paired SEs. It does not replace
the independent-run dispersion or support stable superiority. No significance threshold or
all-positive-seed requirement is imposed.

With both selected datasets complete, apply these **joint** branches:

| Branch | Joint reading rule |
| --- | --- |
| **RM-A** | `Delta_native_bar > 0.001` and `Delta_information_bar > 0.001`, with actual FULL evaluation acquisition in at least one selected dataset |
| **RM-D** | `Delta_native_bar > 0.001` and `Delta_information_bar <= 0.001` |
| **RM-B** | `-0.001 <= Delta_native_bar <= 0.001` |
| **RM-C** | `Delta_native_bar < -0.001` |

Any missing/damaged required dataset primary makes the **joint** comparison INCOMPLETE; preserve
the other dataset's independently trustworthy measurements and branch. Positive native gain
without any FULL acquisition is the existing information/path integrity gap. Optional resource
telemetry gaps retain `resources_unmeasured` and do not annul this non-resource claim.

**How the result will be interpreted.** Joint gain above both MEIs supports a preliminary
repeated useful-acquisition signal at this small budget, with variation and any adverse seed
retained. Gain over IMMEDIATE-4 without the information increment narrows the attribution.
An average inside the native MEI or of opposite sign limits the B02 follow-up; it does not erase
the initial positive or close paid-information research. No branch automatically adds another
seed, promotes to C, establishes stable superiority or explains the historical learner failure.

**DM prediction before output:** joint RM-A; FULL will acquire only in
LINKED-p17_20-c9_100 in each dataset, and BLIND will remain immediate in all contexts in both.
Confidence is moderate for the joint branch and lower for exact action-location repeatability.
Score the joint branch, each FULL location prediction and each BLIND prediction separately;
do not turn these forecasts into conditions for acceptance or continuing the second invocation.
Owner prediction: **not taken (unattended)**.

## 4. Exposure, cost and execution bounds

Python arithmetic from the accepted constants fixes:

| Work | Per dataset | Both datasets |
| --- | ---: | ---: |
| Real training episodes / paid training episodes | 262144 / 131072 | 524288 / 262144 |
| Scalar value updates / histogram increments | 393216 / 131072 | 786432 / 262144 |
| Final evaluation episodes | 98304 | 196608 |
| Total episodes | 360448 | 720896 |
| Possible host-event transitions, actual required | 1507328–1900544 | 3014656–3801088 |
| Complete invocation cap | **600 s** | **1200 s summed** |

Prospective machine-generated exposure: `datasets=2; seeds=[6501,6502];
train_episodes=524288; scalar_value_updates=786432; eval_episodes=196608;
value_entries_per_dataset=264; initial_l2=0; first_observation_step_size=1;
new_exposure_at_freeze=0`. The actual summaries retain component update counts and absolute
L2/max movement; a finite ratio to zero initial scale is undefined. Table updates are not
optimizer steps, and the two fits share their dataset rather than doubling environment work.

Dominant factors are two independent collections, two small shared-label fits/dataset and
three final policies × eight contexts × 4,096 evaluations/dataset. There is no policy search,
nested trajectory/controller sweep or new validation arm. The per-dataset cost law remains
`T_init + 1024*T_batch256_shared_fit + 32768*T_three_policy_eval + T_publish`.
The observed B02 whole call was 7.73 s: a same-shape planning point is **7.73 s/dataset,
15.46 s summed**, far below the selected caps, but not a runtime guarantee. Individual phase
coefficients are unmeasured; no calibration run follows. Added validation is one focused
synthetic seed-binding/publication check and the required independent affected-path review.

Each cap covers the complete native command including adjacent fresh memory admission,
interpreter/import startup, collection, both fits, all three evaluations, publication and exit.
Use the existing external whole-command timeout at 600 s without extra scientific allowance,
plus whole wall/peak RSS. Sum the two actual whole walls; staging/control intervals are separate.
Do not split the cap by learner or add smoke, replay, pilot, retry, third seed or extra endpoint.

Use `.codex/hmasd-compute.toml`: remote `wsl_4070` / `hmasd-wsl-node`, Python
`/home/wu/.venvs/hmasd/bin/python`, CPU binary64, one scientific process/compute thread per
invocation. The processor is not the estimand; this command selects remote execution and no
local fallback invocation. Each seed needs its own adjacent destination admission with both
physical and effective available memory at least 4 GiB, distinct output/handle, and detached
exact-source execution. Use existing successful committed bundle/SCP staging if needed; there
is no new transport experiment. Never overwrite an old output or relaunch to transfer observation.

Invoke **6501, then 6502**, with terminal reconciliation between them. The second proceeds
irrespective of the first valid score, and no treatment/budget is adapted from that score.
A concrete shared reward/information/training/primary defect or failed admission is returned
as a dependent execution gap; it is not scientific polarity or authority for a third invocation.
All partial/failed outcomes remain. Ordinary in-scope technical repairs preserve the frozen
question and do not supply a scientific retry allocation.

**ENGINEERING_SCOPE_SPEC §4: needs none.** Ordinary §5 limits apply: 2,000 new non-test lines,
600 runner lines, five-minute focused test allowance; 30% orchestration is a review signal.
No worker pool, registry, new supervisor, resume/retry framework, guard or schema layer is needed.

## 5. Five-item CM assignment — P08 implementation and two invocations

1. **Deliverable/goal:** minimally bind independent seeds to the existing learner/evaluator and
   provide the B03 runner; complete focused acceptance, then the two selected remote invocations
   and their collection. This command already authorizes execution after technical acceptance;
   no additional Pro/owner round or real-host pilot is required.
2. **Owned checkout/paths:** the one direction authoring checkout
   `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch `codex/ucope`.
   Reuse `experiments/candidates/ucope/shared_data_return_model_b02/{model,evaluation}.py` and,
   if needed, its runner's ordinary run function for minimal explicit seed propagation; add
   `scripts/run_ucope_shared_data_return_model_b03.py` and focused tests in the corresponding
   UCOPE test area. Preserve B02's seed-6401 behavior/evidence and native modules. Record source,
   focused acceptance, exact commands and all results in
   `UCOPE_SHARED_DATA_RETURN_MODEL_B03_RESULT_EVIDENCE_20260907.md` in this direction directory.
3. **Preserved semantics:** §2 and the linked B02 sections fix actual reward/information,
   initialization, row/update order, both RNG seed paths, family literal, final-only evaluation,
   pairing, costs, ties and fallback. Propagate `seed` explicitly; no per-process global seed
   mutation, retained model or new algorithm. Ordinary implementation details remain CM's.
4. **Acceptance/collection:** one synthetic check verifies both seed bindings reach private
   behavior and environment/evaluation ancestry, with isolated state and preserved B02 behavior,
   then exercises compact primary publication. Reuse existing rule/host checks and the existing
   independent reviewer for the affected RNG/comparison path. Evidence-spec §§4, 5.2, 11.4,
   11.8.3, 11.8.5–11.8.8 and card §§2–4 control. Commit/push exact source before launch;
   record each exact argv before output. Send accepted node/handle/SHA/cwd/log/result/receipt
   facts to Root, observe until adoption ACK or terminal, then collect. Root integrates the CM
   delivery; the original DM takes both datasets in jointly and writes the Chinese brief.
5. **Budget/stop and outputs:** exactly seeds 6501 then 6502, §4 caps and fresh admissions;
   future outputs `temp/directions/ucope/exp/shared-data-return-b03-seed6501/` and
   `.../shared-data-return-b03-seed6502/`, handles
   `ucope-shared-return-b03-seed6501-20260907` and `ucope-shared-return-b03-seed6502-20260907`.
   Use one detached remote source worktree at the accepted implementation SHA and separate
   output roots, not extra authoring branches. Return any concrete dependent gap with completed
   work and all partial artifacts; do not replace a score, add a seed or exceed either cap.

DM owns this checkout through card commit. The actual CM dispatch transfers editing ownership
through implementation/collection commits; DM then resumes intake authoring after that return.
Root integrates explicit accepted paths. No concurrent shared-index writers are selected.
