# ACVC_M_DEPLOYMENT_TRANSFER_B01 — E0 result evidence

## Bound object, source and rule

B/EXPLORE, one fresh M fit of the frozen block-2 recipe, MASTER 28531 / evaluation namespace
38531, with three private final panels M / F(M) / own-dwell(M) from the single final snapshot;
selected by `em:acvc:convergence` (B with corrections,
[intake](pro_packets/20260915_m_deployment_transfer_convergence/INTAKE.md)) and funded by
`portfolio:cross_direction` (G,
[decision](../../portfolio/decisions/2026-09-15-acvc-m-deployment-transfer-grant.md)). Object,
panels, laws, labels and reading rule are the
[prospective card](ACVC_M_DEPLOYMENT_TRANSFER_B01_PROSPECTIVE_CARD_20260915.md) as corrected by
the node (card §7). Runner `scripts/run_acvc_m_deployment_transfer_b01.py`, wrapped evaluator
`experiments/candidates/acvc/m_deployment_transfer_b01/wrapped_eval.py` (independent Opus
review of `fb7f859d9`, corrections at the launch sha). Exact launch source
`a741758a11e6c9d9888cbc852095544f3df4e04f` (`codex/acvc`); pinned on-policy
`de66d7a4b23fac2513f56f96f73b3f5cb96695ac` re-staged
([DEPENDENCY.json](evidence/m_deployment_transfer_b01_20260915/DEPENDENCY.json)).

Primary reading rule applied verbatim to the unrounded `T_F = mean64[J(F(M)) − J(M)]`:
- `T_F > .01`: TRANSFERS.
- `−.01 ≤ T_F ≤ .01`: WITHIN_MEI, a small signed point observation, not equivalence and not
  non-transfer.
- `T_F < −.01`: ADVERSE.
- Missing or invalid operand: INCOMPLETE, no imputation.

J is the complete native team episode sum divided by 256. The fit and all three sole-final
64-world panels are complete. The unrounded primary is **T_F = +.018338005502877976 J**, so
the frozen point rule gives **TRANSFERS**. Supporting `T_D = +.009069800680064894 J`
(WITHIN_MEI) and paired `U = +.00926820482281308 J` (WITHIN_MEI). No interval, significance
or seed-SD gate replaces the rule; no accumulation with blocks 1 or 2 is performed.

## Absolute scores and every declared contrast

| Panel | Mean J | Mean episode sum S |
|---|---:|---:|
| M (unwrapped `mappo.evaluate`) | .3786100500884796 | 96.92417282265077 |
| F(M) (retrace on `Binding` opportunities) | .3969480555913576 | 101.61870223138754 |
| own-dwell(M) (zero command on the same predicate, own history) | .38767985076854444 | 99.24604179674738 |

| Contrast | Mean delta J | Sample SD J | Conditional SE J | Adverse/favorable worlds | Worst / best delta J | Frozen reading |
|---|---:|---:|---:|---:|---|---|
| T_F = F(M) − M (primary) | +.018338005502877976 | .04399877294938132 | .005499846618672665 | 11/53 | −.1614043800748056 / +.16955367611791633 | TRANSFERS |
| T_D = own-dwell(M) − M | +.009069800680064894 | .03310258686338158 | .004137823357922697 | 14/50 | −.07590783987934333 / +.12286813807577418 | WITHIN_MEI |
| U = F(M) − own-dwell(M) (paired) | +.00926820482281308 | .04426093446459615 | .0055326168080745185 | 16/48 | −.17089950875818674 / +.13008416867707573 | WITHIN_MEI |

No zero world difference occurs. The SD/SE are conditional on the one attained fitted
policy over the 64 matched reset worlds; they are not training-population precision. The
runner's `--mode reduce` output
([reduce/summary.json](evidence/m_deployment_transfer_b01_20260915/reduce/summary.json)) and
[WORLD_DIFFERENCES.json](evidence/m_deployment_transfer_b01_20260915/WORLD_DIFFERENCES.json)
retain every absolute score and matched difference (`u(e) = dF(e) − dD(e)` holds to 1e-12 on
every world).

**Wrapper counters** (per panel over 16,384 ticks × 5 agents = 81,920 agent-ticks):

| Panel | Opportunities | Retrace | Dwell | Apply | Distinguishable |
|---|---:|---:|---:|---:|---:|
| M | 0 (no `Binding` in the unwrapped path) | 0 | 0 | 0 | 0 |
| F(M) | 6,752 (8.24 % of agent-ticks) | 6,752 | 0 | 0 | 6,752 |
| own-dwell(M) | 5,110 (6.24 % of agent-ticks) | 0 | 5,110 | 0 | 5,110 |

Every opportunity was substituted and every substitution differed from the proposal; `apply`
is 0 by construction (the mask is the choice, no learned gate, as on the C side). The two
wrapped panels count different opportunities because each panel's predicate runs on its own
history after the first changed command (card §2, correction 1); the C-side F executed 6,610
retraces in block 2 for comparison of order, not of value.

**Descriptive context, never pooled** (card §3): T_F +.0183 J on the conventional proposer
beside the C-side F−C increments +.0474962536 (block 2), +.0347495498 (block 1), pooled
+.0411 J; U +.0093 J beside the C-side F−own-dwell +.0317 (block 2) and +.0122 (block 1). These
are different training instances and different proposers; nothing is matched across them.

## Actual exposure, implementation and measurement limits

Counts from the native summary: 4,096 H256 training episodes, 1,048,576 training team ticks,
2,048 two-episode rollouts, 8,192 actor + 8,192 critic Adam steps, one final checkpoint
(`final.pt`, after episode 4,096) loaded three times (`post_fit_loads` 3), 192 evaluation
episodes (three 64-world panels, 49,152 ticks), five environment constructors (two training
lanes as in block 2, one per panel); 1,097,728 team ticks in all, exactly the grant.
Empty `limits`; `upstream_sha` de66d7a4b; `launch_sha` a741758a1; master 28531 and namespace
38531 stamped on every row. All 4,288 episode rows (4,096 train + 3 × 64 eval) have 256 steps,
finite `S`/`J`, `terminated` true and `truncated` false; all 2,048 update rows are finite.
Training moved: mean training J .162 over the first 256 episodes to .378 over the last 256;
value loss .618 → .029; policy entropy 4.26 → 6.38; parameter displacements finite (actor
8.825, critic 8.352, action head finite). The absolute M panel (.3786 J) sits between block 1's
M (.3338) and block 2's M (.3942); the ordering is descriptive context only and does not
certify a typical draw, exclude an outlier or establish competence (corrected 2026-09-15 per
`em:acvc:convergence`, [review intake](pro_packets/20260915_m_deployment_transfer_result_review/INTAKE.md)). Panel reset seeds are identical across the three panels (`100000·38531 + 2000 + e`)
and the per-episode actor generators equal-seeded; coupling is conditional, not guaranteed.
The inherited unwired auxiliary counters stay unmeasured (§11.8.7) and the primary does not
depend on them. No retry, tuning, midpoint, pilot or extra panel occurred.

Checks before launch: eleven focused tests (identity binding, early-import refusal, wrong
seed and missing input refusal, substitution semantics on a synthetic link-loss fixture,
unwrapped-panel identity with `mappo.evaluate` over 32 traced events, private state per
episode, panel-order determinism, reduce edges, CLI reduce binding), the independent Opus
review with its three fixes applied, technical acceptance (ledger row 31). No separate launch
review (grant).

## Complete native cost and preservation

| Original | Handle | PID | Whole native wall s | User + system CPU s | Peak RSS KiB | Native/supervisor exit |
|---|---|---:|---:|---:|---:|---|
| M fit + 3 panels | acvc-transfer-m-b01-28531-a741758a | 3745266 | 985.12 | 982.04 + 1.47 | 585,028 | 0/0 |

Process wall to the summary 984.64 s: training complete at 944.99 s (0.90 ms per training
tick), then the three panels at about 11.9 / 13.9 / 13.9 s each. The fit ran alone on an
otherwise idle node; the pre-launch projection of about 2,500 s was scaled from block 2's M
wall of 2,427.41 s measured beside five concurrent FSD fits, and block 1's M (1,521.04 s) was
the less contended reference. The 2,600 s plan was not a cap and the actual wall is 0.38 of it.
Admission passed at 15,621,808,128 B physical and effective available (floor 4 GiB;
[admission.json](evidence/m_deployment_transfer_b01_20260915/native/admission.json)). Support,
provider and lifetime costs remain UNKNOWN.

The original nine-file set (eight native files plus the supervisor `task.log`) was collected
with per-file sha256 byte-identical to the remote `sha256sum` listing
([COLLECTION.json](evidence/m_deployment_transfer_b01_20260915/COLLECTION.json),
[task_records/](evidence/m_deployment_transfer_b01_20260915/task_records/)). The five
non-checkpoint, non-log native files and the task log (as `.txt`) are committed under
[evidence/…/native/](evidence/m_deployment_transfer_b01_20260915/native/); `final.pt`
(313,423 bytes), `stdout.log` and `stderr.log` (0 bytes) are excluded from Git by `.gitignore`
and retained with the full set in the local archive
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/retained/m_deployment_transfer_b01_20260915/M_original.tar.gz`
([PRESERVATION.json](evidence/m_deployment_transfer_b01_20260915/PRESERVATION.json) carries the
archive and member digests, verified against the remote digests). Launch facts, cost projection
and the terminal record: [EXECUTION.md](evidence/m_deployment_transfer_b01_20260915/EXECUTION.md).
Remote reclamation of the worktree and staging follows the push (CLEANUP.json).

## Bounded reading and prediction

In this one instance the fixed retrace law adds an MEI-sized increment to the conventional
private recurrent proposer: +.018 J with 53 of 64 matched worlds favorable, on a proposer that
never trained through the law. The simpler zero-command law on the same predicate adds +.009 J
(within the band), and the paired retrace-over-dwell difference U is +.009 J (within the band, 48/64 favorable). T_D numerically about half of T_F describes three
panel means, not a mediation decomposition. U contrasts two complete deployment packages
(unequal realised intervention schedules, 6,752 versus 5,110 substitutions, with diverging
downstream states), not an isolated retrace-direction component: an MEI-sized incremental
preference of F over dwell is not established, and the packages are not shown equivalent
(corrected 2026-09-15 per `em:acvc:convergence`, [review intake](pro_packets/20260915_m_deployment_transfer_result_review/INTAKE.md)). This is the card's TRANSFERS branch: it motivates the development question "M plus
the fixed transformation" and makes a later matched F(C) versus F(M) comparison worth asking.
It is evidence for one attained finite-learning instance on this host with conditional-world
precision only. Between-fit variation of the expected deployment contrast conditional on the fitted M
policy is unmeasured here: one fitted policy cannot identify it, and the .0055 J SE
describes finite-panel variation at this attained policy only. The .044 J dispersion of the
two F(C)−M block contrasts is a different contrast on different fitted proposers and is not
the variability of T_F (corrected 2026-09-15 per `em:acvc:convergence`, [review intake](pro_packets/20260915_m_deployment_transfer_result_review/INTAKE.md)). No stable superiority, no evidence that C can be
discarded, no F(C) versus F(M) comparison, no tuned headroom, no equivalence, no mechanism, no
default change and no C promotion follow. The two-block C/M claim and its label are unchanged.

Predictions (card §3, recorded before launch): T_F TRANSFERS .40 / WITHIN_MEI .30 / ADVERSE
.30, realized TRANSFERS, multiclass Brier .54, modal forecast occurred; T_D UP .30 / WITHIN
.35 / DOWN .35, realized WITHIN_MEI, Brier .635, one of the two modal categories occurred
([PREDICTIONS.json](evidence/m_deployment_transfer_b01_20260915/PREDICTIONS.json)). Owner
prediction not taken (unattended); canonical review inbox checked at intake.
