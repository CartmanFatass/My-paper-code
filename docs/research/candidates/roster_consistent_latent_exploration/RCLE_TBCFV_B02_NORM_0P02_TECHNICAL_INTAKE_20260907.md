# RCLE B02 technical closeout and post-A02 delivery boundary — 2026-09-07

The retained B02 evidence supports its already accepted complete B/EXPLORE comparison. This
technical closeout replaces the stale “technical intake pending” status; it adds no training,
evaluation, model execution, test run, Pro send or scientific successor. The post-A02 response
is still missing, and its recorded destination is **Innovator**, not Convergence.

Assignment: Root relayed Portfolio's instruction to reconcile the existing post-A02 binding and
complete technical intake of B02 launch `8ad01cb9ea69b77a2e907947bef59bf716a8b45a`, with no
successor or Pro send. Authoring checkout is the retained
`C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906`, now the reusable `codex/rcle` branch, based on
clean main `02728db5a385d0e7990beef3e037983bef021ecd`. The accepted Pro output branch and all
historical evidence remain unchanged. Root integrates this delivery; Portfolio owns the next command.

## 1. Evidence checked and acceptance scope

Read the B02 [card](RCLE_TBCFV_B02_NORM_0P02_SCIENCE_CARD_20260906.md) §§2–7, existing
[scientific intake](RCLE_TBCFV_B02_NORM_0P02_RESULT_INTAKE_20260906.md) §§1–5, and the
[CM record](RCLE_TBCFV_B02_NORM_0P02_CM_RECORD_20260906.md) §§3, 6 and 9. Applied evidence-spec
§§4, 5.2, 11.4 and 11.8.1/5/6/7: the real learner counts and readable comparison are required;
this bounded B does not require another training run, exact parameter replay or causal diagnosis.

Directly read the retained `c1p1`, `flex` and `reference` summaries, the standalone initialization
panel, all five admission receipts, GNU-time files, exit records and original launch script under
[b02_tbcfv_norm0p02_20260906](b02_tbcfv_norm0p02_20260906). Read the retained primary-checkout
`pytest.log` and `task.log`; their byte-identical copies are now
[pytest_retained_20260907.txt](b02_tbcfv_norm0p02_20260906/pytest_retained_20260907.txt) and
[task_retained_20260907.txt](b02_tbcfv_norm0p02_20260906/task_retained_20260907.txt), so the raw
observations survive a clean checkout. No tests were repeated.
The raw pytest copy retains its original whitespace-only warning line; it is preserved evidence,
the sole known whitespace-check exception, rather than edited console output.

A short Python calculation over those JSON/text bytes produced
[technical_readback_20260907.json](b02_tbcfv_norm0p02_20260906/technical_readback_20260907.json).
It counts published rows and recomputes the declared paired-scenario arithmetic. It imports no
environment or model. Source reading was limited to B02's `fixed_norm_sgd_step`, `run_arm` and
allocation record plus TBCFV's `initialize_block_models`, directly at the launch SHA. This is
technical acceptance of the retained execution and measurement, not a new independent code review.

## 2. Counts, learning law and comparison

All three final summaries report `COMPLETE`, the full launch SHA, seed 18, root key
`fd3cd5cf0f085e880a424f7a546017a62d300676e385e1174676b9f4c14e5093` and block digest
`82593ad701533212112f1e29d22f3d0b701fd8360b88d9bfcb61ac565f6b2210`, matching the card. Recomputing
SHA256 of the card's seed string reproduces the root key. The recorded initial norm is
21.205717682888885 in both arms.

| Quantity | C1P1 | FLEX | Shared initialization | Scripted reference |
| --- | ---: | ---: | ---: | ---: |
| Completed update records | 200 | 200 | 0 | 0 |
| Nonzero / zero updates | 200 / 0 | 200 / 0 | — | — |
| Training episodes counted from curve cell rows | 12,800 | 12,800 | 0 | 0 |
| Evaluation scenarios | 2,048 | 2,048 | 2,048 | 2,048 |
| Evaluation cells × scenarios per cell | 8 × 256 | 8 × 256 | 8 × 256 | 8 × 256 |

Each arm has update indices 0–199, all eight training cells with eight episodes on every curve,
and `parameter_update` before `baseline_update` on every record. The committed loop performs one
backward/joint update per complete block. Thus the study has **one paired training seed, two
trained instances, 400 backward/joint-update calls, 25,600 training episodes, 8,192 evaluation
episodes, 33,792 total episodes and 2,162,688 environment ticks**. These are the frozen algorithm
counts; historical focused-test exposure is separate and adds no independent training replicate.

Every curve prescribes 0.02. The reported update-vector norms range from
0.019999999999999993 to 0.020000000000000007 in each arm. Source lines 121–158 compute the norm
of `multiplier * gradient`, using the same multiplier passed to the parameter addition. This is
an observed update-vector measurement, **not** a subtraction/readback of every parameter's
realized floating-point delta. No claim of exact per-coordinate or per-step bit identity follows.
The separately recorded final-minus-initial vector norms are 0.47288939377781736 and
0.4729438987020604; the path bound of 4 is not either displacement.

Allocation scope also needs precision. The JSON's five package models describe each initializer
call, while its two training-instance names describe the comparison. The launch has one helper
call per arm process. Static source therefore implies ten package allocations plus two temporary
initialization-reference models across the two arm invocations; only two instances train. This
is not a new runtime allocation census, and unused initialization copies are not learner seeds.

Every final/init panel has exactly the same 2,048 unique `(cell, index)` keys, covering all eight
held-out cells and indices 0–255. The standalone initialization rows equal the copies embedded in
both arm summaries. FLEX's `paired_primary_error` is null. All initialization and learned rows
have τ=40; the reference has 2,011/2,048 such rows and null Y with its published reason.

The build record and all final summaries identify the same native source and artifact SHA256
(`18d45b95…` / `5b918da7…`). The request build root and default cache have different path-dependent
build keys but the same recorded artifact bytes. This resolves the CM record's Linux/default-root
execution uncertainty for this run. The later accepted
[A02 E0](RCLE_TBCFV_A02_RESULT_EVIDENCE_20260906.md) already verified both retained final parameter
files and all 30 tensors; that evidence is reused without loading the models again.

## 3. Primary readback and unchanged bounded reading

| ACTIVE_CONTINUATION path | U init | U C1P1 | U FLEX | FLEX − C1P1 | Reference U |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8→12 | 0.696744792 | 0.695312500 | 0.695345052 | +0.000032552 | 0.245646159 |
| 12→8 | 0.721240234 | 0.718701172 | 0.718664551 | −0.000036621 | 0.318652344 |

Recomputation from aligned scenarios gives ΔU = **−0.000002034505208333**, conditional paired
Monte Carlo SE **0.0000244986868871915**, G_U(C1P1) = **0.00198567708333330** and G_U(FLEX) =
**0.00198771158854166**; Δτ = 0. The ΔU discrepancy from the published aggregate is
2.60e−17 from reduction order, with no change of sign or card reading. The SE describes the fixed
seed's evaluation panel, not variation across independent training seeds.

Card §5 row 4, applied verbatim:

| Observation | Current change and advice | Not inferred |
| --- | --- | --- |
| `ΔU` inside the MEI, both arms barely improved on the start, τ still saturated | this 0.02 / 200 movement attempt gave no useful learning signal; end this spend and return to the next object selection with the complete counterexample | automatic 4,000 updates, step sweep or warm-started heads; that the normalisation principle is wrong or the host unlearnable |

The result remains the already accepted **row-4 B observation**. Both G_U values are positive but
small relative to the 0.05 MEI; the two path differences have opposite signs. Strongest support is
the complete comparison's small package difference and small start-to-final service gain at the
selected budget. Strongest contradiction to literal “nothing changed” is the nonzero learning
updates, 0.47 vector displacements, small positive G_U, and 14 differing C1P1/FLEX U outcomes.
The scripted active-path mean U≈0.282 versus learned≈0.707 is a same-panel diagnostic gap, not
upper-minus-tuned-baseline headroom.

One descriptive qualification to the old intake: direct stored-float inequality finds 1,918
initialization/C1P1 U differences. Of these, 44 are only 1.11e−16 to 4.44e−16; 1,874 exceed 1e−15,
consistent with the old substantive-difference count. The historical sentence did not state that
threshold. This annotation preserves its bytes and does not introduce a tolerance into ΔU or
rewrite its result rule. Likewise, “no useful signal” is the card's effect-scale reading, not
exactly zero improvement or package equivalence. No cause of weak learning, stable superiority,
host unlearnability or family closure is established.

Prediction scoring remains the existing intake §4: Pro's working improvement forecast did not
occur; its weak-learning alternative did. The DM's G_U≥0.05 component failed, its small-package-
difference/saturated-τ components held, and its large FLEX-gain alternative failed. Owner
prediction: not taken. This closeout does not make another prediction about the same result.

## 4. Receipts, timing and remaining technical limits

The retained supervisor log records `rcle_b02_chain_20260906` on `wsl_4070`, from
2026-09-06T22:23:39Z to 22:26:11Z, exit 0. All five step exit files and GNU-time exits are zero.
Each step has its own preceding successful `/proc/meminfo` admission; physical and effective
availability range from 15,254,589,440 to 15,678,771,200 bytes, above the 4,294,967,296-byte floor.
The original launch requests one CPU thread with unchanged FP64/RNG semantics.

| Complete process | GNU-time wall (s) | User + system CPU (s) | Peak RSS (KiB) |
| --- | ---: | ---: | ---: |
| Native build | 3.04 | 2.79 | 430,288 |
| Focused tests | 4.05 | 3.99 | 602,492 |
| C1P1, including shared initialization panel | 71.47 | 71.42 | 575,040 |
| FLEX | 71.23 | 71.13 | 580,532 |
| Reference | 2.62 | 2.61 | 429,628 |

Sum of these process walls is **152.41 s**, aggregate measured process CPU **151.94 s**; the
recorded sequential chain wall is **152.622 s**, including the recorded **7.173 s** preparation.
Do not add preparation to the chain a second time. GNU-time RSS is KiB (C1P1 588,840,960 bytes;
FLEX 594,464,768 bytes), and the summary's internal wall/CPU/RSS cover a narrower scope. The
remote raw test report is **23 passed, one warning, 3.72 s pytest time / 4.05 s whole process**;
the warning is the unused pytest `cache_dir` configuration. All four retained stderr files are empty.

The prelaunch CM record also reports local **18 passed in 5.22 s**, with a cached MSVC artifact.
It must not disappear from preparation accounting. Remote chain plus that recorded local test
duration is 157.842 s, a combination of known durations rather than an exact all-history whole-
process total; local interpreter overhead/CPU were not recorded. Both remote arms are inside
their 600 s caps, and all measured components are inside the 1,500 s object cap. No cap breach
is observed; complete historical resource accounting remains partially unmeasured. Resource flag:
`resources_unmeasured` for the full historical preparation total only; the remote invocation
telemetry is present. These limits do not damage the independently readable comparison.

The historical CM report is preserved as a prelaunch report. Linux execution, the changed step,
actual seed-18 norm and complete arm timing are now observed. Per-update isolated cost and
SIGALRM behavior during an overrun remain unmeasured; this successful run did not test them.
No such extra probe is selected. The CM reported 853 new non-test source lines and a 135-line
runner, inside its stated budgets, with no engineering-scope §4 machinery. This closeout adds
only documentation and retained evidence, no source or new machinery, and records no source
budget breach.

## 5. Exact post-A02 missing response

| Binding field | Retained value |
| --- | --- |
| Request | `2026-09-06-rcle-post-a02-innovator-01` |
| Node / binding | `em_innovator` / `em:roster_consistent_latent_exploration:innovator` |
| Existing conversation | `6a9d9a3a-fd40-83e8-9e80-ad720582aaee` |
| Fixed TASK commit | `c5c96eecb27f60609d195320467b6dbc29af013d` |
| Expected response branch | `codex/pro-rcle-post-a02-20260906` |
| Expected response path | `pro_packets/20260906_post_a02_innovator/archive/RESPONSE.md` under this direction |

Read-only GitHub inspection at 2026-09-07T20:00:18Z still returned response-branch head
`5a335eaff0f2242c515f6867e22d04bdd8d832ef`; `git cat-file` confirms that exact commit has no
expected response. Issue 8 still has only historical comments 5560789984, 5562367990 and
5564117795. Root's recorded P07 observation reopened the exact conversation and found the older
post-B01/post-B02 pairs but no matching post-A02 user node, provider Send identity or response;
no matching primary Transport registry/archive was found. That observation is reused, not repeated.

The [HANDOFF](pro_packets/20260906_post_a02_innovator/HANDOFF.json) supplies a known scientific
binding, while [DISPATCH](pro_packets/20260906_post_a02_innovator/DISPATCH.json) proves app
dispatch acceptance only. **Missing facts are a matched provider Send/response identity and a
complete immutable post-A02 decision**, not the destination conversation ID. There is no
post-A02 Convergence binding in these records. The archived post-B02 decision `6c0d1ca55` selected
the already completed A02 and supplies no successor. An absent response is no scientific polarity.

## 6. Decisions this intake produces

1. **Object-tier technical closeout.** Options: (a) accept the retained B02 technical completion
   with the measurement/resource qualifications above; (b) quarantine a concretely damaged
   primary; (c) repeat execution to close a stale status line. Recommendation and selection: (a).
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** No dependent primary
   defect was found. The prior B02 scientific acceptance and row-4 reading remain in force.
2. **Current routing boundary.** Options: (a) return the precise missing post-A02 Innovator
   response to Root/Portfolio with no Send or successor; (b) treat the old post-B02 response as a
   new decision; (c) send or regenerate the pending question. Execute (a), **OWNER_DIRECT** under
   the current Portfolio command relayed by Root. This records missing evidence at direction
   tier; it forms no direction-tier scientific decision and selects no new object.

Owner flags: none; no close call, critic dissent, recast or Portfolio disposition. Primary owner
reviews were empty and relevant RCLE audit owner columns blank at this boundary. Ordinary
technical facts receive no separate P1/P2 console item. The existing scientific intake and
Chinese brief remain; the short [technical brief](../../portfolio/owner/briefs/roster_consistent_latent_exploration/2026-09-07_TBCFV-B02-technical-closeout.md)
records this closeout. No new mechanism-level science is added to DIRECTION.md.

**Next owner:** Root integrates the named delivery and reports the missing response to Portfolio;
Portfolio supplies the next bounded command. The next necessary decision evidence is the correctly
matched post-A02 node response or an explicit instruction about its unresolved transport state.
No experiment, additional A diagnostic, Pro send or automatic successor follows from this intake.

scope: none
