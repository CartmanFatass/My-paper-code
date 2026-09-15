# ACVC_M_DEPLOYMENT_TRANSFER_B02 — E0 result evidence

## Bound object, source and rule

B/EXPLORE, one further independently initialised M fit of the frozen block-2 recipe, MASTER
28631 / evaluation namespace 38631, with the unchanged three private final panels M / F(M) /
own-dwell(M) from the single final snapshot; selected by `em:acvc:convergence` in its result
review of B01 (B, [intake](pro_packets/20260915_m_deployment_transfer_result_review/INTAKE.md))
and funded by `portfolio:cross_direction` (G2,
[decision](../../portfolio/decisions/2026-09-15-acvc-m-deployment-transfer-b02-grant.md)).
Object, panels, laws, labels and reading rule are the
[prospective card](ACVC_M_DEPLOYMENT_TRANSFER_B02_PROSPECTIVE_CARD_20260915.md). Thin entry
`scripts/run_acvc_m_deployment_transfer_b02.py` rebinding the identities on the unchanged B01
transfer runner, wrapped evaluator and reducer (independent Opus review of `6a3967065`, accept,
no material finding; 16 focused tests green on the node). Exact launch source
`c006c0b2453a44902ebfda827099823a28e136f1` (`codex/acvc`); pinned on-policy
`de66d7a4b23fac2513f56f96f73b3f5cb96695ac` re-staged
([DEPENDENCY.json](evidence/m_deployment_transfer_b02_20260915/DEPENDENCY.json)). Nothing was
transferred from the B01 fit.

Primary reading rule applied verbatim to the unrounded `T_F,2 = mean64[J(F(M_2)) − J(M_2)]`:
- `T_F,2 > .01`: TRANSFERS.
- `−.01 ≤ T_F,2 ≤ .01`: WITHIN_MEI, a small signed point observation, not equivalence and not
  non-transfer.
- `T_F,2 < −.01`: ADVERSE.
- Missing or invalid operand: INCOMPLETE, no imputation.

J is the complete native team episode sum divided by 256. The fit and all three sole-final
64-world panels are complete. The unrounded primary is **T_F,2 = +.002859470696673056 J**, so
the frozen point rule gives **WITHIN_MEI**. Supporting `T_D,2 = +.0026775973111561728 J`
(WITHIN_MEI) and paired `U_2 = +.0001818733855168831 J` (WITHIN_MEI). No interval, significance
or seed-SD gate replaces the rule; no accumulation with B01 or with blocks 1 or 2 is performed.

## Absolute scores and every declared contrast

| Panel | Mean J | Mean episode sum S |
|---|---:|---:|
| M_2 (unwrapped `mappo.evaluate`) | .42921916801387766 | 109.88010701155268 |
| F(M_2) (retrace on `Binding` opportunities) | .43207863871055074 | 110.61213150990099 |
| own-dwell(M_2) (zero command on the same predicate, own history) | .43189676532503385 | 110.56557192320867 |

| Contrast | Mean delta J | Sample SD J | Conditional SE J | Adverse/favorable/zero worlds | Worst / best delta J | Frozen reading |
|---|---:|---:|---:|---:|---|---|
| T_F,2 = F(M_2) − M_2 (primary) | +.002859470696673056 | .026378232601472408 | .003297279075184051 | 22/41/1 | −.1375220507892072 / +.09571652294969374 | WITHIN_MEI |
| T_D,2 = own-dwell(M_2) − M_2 | +.0026775973111561728 | .027400971945163714 | .0034251214931454643 | 28/35/1 | −.12862561567305603 / +.11387702413858614 | WITHIN_MEI |
| U_2 = F(M_2) − own-dwell(M_2) (paired) | +.0001818733855168831 | .029398268700156903 | .003674783587519613 | 21/42/1 | −.13172536408381086 / +.14079389889715516 | WITHIN_MEI |

The one zero difference is world 46, where neither wrapped panel met an opportunity
(`opportunities` 0 in F(M_2) and own-dwell(M_2)) and all three panels scored the identical
.0018483290330577502 J: with no substituted command the equal-seeded panels coincide exactly,
which is the conditional coupling of card §2 observed, not a defect. The SD/SE are conditional
on the one attained fitted policy over the 64 matched reset worlds; they are not
training-population precision. The runner's `--mode reduce` output
([reduce/summary.json](evidence/m_deployment_transfer_b02_20260915/reduce/summary.json)) and
[WORLD_DIFFERENCES.json](evidence/m_deployment_transfer_b02_20260915/WORLD_DIFFERENCES.json)
retain every absolute score and matched difference (`u(e) = dF(e) − dD(e)` holds to 1e-12 on
every world). Largest gain world 8 (M .3606 / F .4563 / dwell .4744 J); largest loss world 14
(M .4589 / F .3214 / dwell .4531 J).

**Wrapper counters** (per panel over 16,384 ticks × 5 agents = 81,920 agent-ticks):

| Panel | Opportunities | Retrace | Dwell | Apply | Distinguishable |
|---|---:|---:|---:|---:|---:|
| M_2 | 0 (no `Binding` in the unwrapped path) | 0 | 0 | 0 | 0 |
| F(M_2) | 6,510 (7.95 % of agent-ticks) | 6,510 | 0 | 0 | 6,510 |
| own-dwell(M_2) | 5,037 (6.15 % of agent-ticks) | 0 | 5,037 | 0 | 5,037 |

Every opportunity was substituted and every substitution differed from the proposal; `apply`
is 0 by construction (the mask is the choice, no learned gate). The two wrapped panels count
different opportunities because each panel's predicate runs on its own history after the first
changed command; the per-row counters sum exactly to the summary's totals.

## The two M-transfer instances side by side (per instance; no pooled verdict)

Read B02 on its own first (above). The card then asks for the two instances displayed beside
each other with their own conditional uncertainties; nothing below is pooled, averaged,
majority-read or accumulated with the C/M blocks.

| Instance | M | F(M) | own-dwell(M) | T_F (SE; adverse/favorable/zero) | Reading | T_D (SE) | U (SE) |
|---|---:|---:|---:|---|---|---|---|
| B01 (28531/38531) | .3786 | .3969 | .3877 | +.018338 (.0055; 11/53/0) | TRANSFERS | +.009070 (.0041) | +.009268 (.0055) |
| B02 (28631/38631) | .4292 | .4321 | .4319 | +.002859 (.0033; 22/41/1) | WITHIN_MEI | +.002678 (.0034) | +.000182 (.0037) |

The MEI-sized package increment observed on B01 did not recur on B02: the B02 primary is
positive but about a third of the MEI, the dwell package matches the F package to four decimal
places (U_2 ≈ 0), and both wrapped panels sit within the band of the unwrapped M_2. The
difference between the two instances' T_F (about .0155 J) exceeds either conditional SE, which
is a descriptive statement about two attained policies, not an estimate of between-fit
variation (two fits cannot decompose training from panel variation). The absolute M_2 score
(.4292 J) is above every earlier M on record (.3338, .3786, .3942); the ordering is descriptive
context only and establishes neither typicality nor competence.

## Actual exposure, implementation and measurement limits

Counts from the native summary: 4,096 H256 training episodes, 1,048,576 training team ticks,
2,048 two-episode rollouts, 8,192 actor + 8,192 critic Adam steps, one final checkpoint
(`final.pt`, after episode 4,096) loaded three times (`post_fit_loads` 3), 192 evaluation
episodes (three 64-world panels, 49,152 ticks), five environment constructors; 1,097,728 team
ticks in all, exactly the grant. Empty `limits`; `upstream_sha` de66d7a4b; `launch_sha`
c006c0b24; master 28631 and namespace 38631 stamped on every episode and update row (training
resets 2863101000..2863105095; panel resets 3863102000..3863102063, identical across the three
panels). All 4,288 episode rows (4,096 train + 3 × 64 eval) have 256 steps, finite `S`/`J`,
`terminated` true and `truncated` false; all 2,048 update rows are finite. Training moved: mean
training J .101 over the first 256 episodes to .377 over the last 256; value loss .447 → .059;
policy entropy 4.26 → 6.36; parameter displacements finite (actor 8.718, critic 8.679, action
head 1.629). Training motion shows learning, not tuned headroom. The inherited unwired auxiliary
counters stay unmeasured (§11.8.7) and the primary does not depend on them. No retry, tuning,
midpoint, pilot or extra panel occurred; nothing from the B01 fit was reused.

Checks before launch: five focused B02 binding tests plus the ten unchanged B01 tests, run on
the control plane (15 passed, 1 skipped) and on the node in the launch worktree with the staged
on-policy root (16 passed, including the wrapped-no-substitution identity with `mappo.evaluate`);
independent Opus review (accept, no material finding, two minor points resolved by the node run);
technical acceptance (ledger row 35). No separate launch review (grant).

## Complete native cost and preservation

| Original | Handle | PID | Whole native wall s | User + system CPU s | Peak RSS KiB | Native/supervisor exit |
|---|---|---:|---:|---:|---:|---|
| M_2 fit + 3 panels | acvc-transfer-m-b02-28631-c006c0b24 | 3754217 | 989.80 | 987.74 + 1.13 | 588,916 | 0/0 |

Process wall to the summary 989.47 s: training complete at 949.14 s (0.905 ms per training
tick), then the three panels at about 12.2 / 14.2 / 14.0 s. The fit ran alone on an otherwise
idle node; the pre-launch projection was about 1,000 s alone with a 1,200 s plan (not a cap),
and the actual wall is 0.82 of the plan and 1.005 of B01's 985.12 s. Admission passed at
15,613,599,744 B physical and effective available (floor 4 GiB;
[admission.json](evidence/m_deployment_transfer_b02_20260915/native/admission.json)). Support,
provider and lifetime costs remain UNKNOWN.

The original nine-file set (eight native files plus the supervisor `task.log`) was collected
with per-file sha256 byte-identical to the remote `sha256sum` listing
([COLLECTION.json](evidence/m_deployment_transfer_b02_20260915/COLLECTION.json),
[task_records/](evidence/m_deployment_transfer_b02_20260915/task_records/)). The five
non-checkpoint, non-log native files and the task log (as `.txt`) are committed under
[evidence/…/native/](evidence/m_deployment_transfer_b02_20260915/native/); `final.pt`,
`stdout.log` and `stderr.log` (0 bytes) are excluded from Git by `.gitignore` and retained with
the full set in the local archive
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/retained/m_deployment_transfer_b02_20260915/M_original.tar.gz`
([PRESERVATION.json](evidence/m_deployment_transfer_b02_20260915/PRESERVATION.json) carries the
archive and member digests, verified against the remote digests). Launch facts, cost projection
and the terminal record: [EXECUTION.md](evidence/m_deployment_transfer_b02_20260915/EXECUTION.md).
Remote reclamation of the worktree, staging and task record follows the push (CLEANUP.json).

## Bounded reading and prediction

On this second fresh instance of the conventional private recurrent proposer, the fixed retrace
package adds +.003 J with 41 of 64 matched worlds favorable, 22 adverse and one exactly zero,
inside the ±.01 J band: the card's WITHIN_MEI branch, "useful-size recurrence is not observed at
this point scale; preserve the sign and uncertainty; reconsider further unchanged spending". The
simpler zero-command package adds +.003 J on the same instance and the paired F-over-dwell
difference is +.0002 J (42/64 favorable), so on this instance the two complete deployment
packages are indistinguishable at the point scale; that is not equivalence, and U_2 remains a
contrast between complete execution packages with different realised schedules (6,510 versus
5,037 substitutions). Displayed beside B01's TRANSFERS, the two M-transfer instances disagree on
whether the fixed package adds an MEI-sized increment to M; the design claims recurrence or
discrepancy of observed outcomes, and discrepancy is what was observed. No pooled verdict,
training-population mean, majority rule or best-instance selection is drawn; B01's TRANSFERS
reading stands as recorded, and B02's WITHIN_MEI stands beside it. Between-fit variation of the
expected deployment contrast is not estimated by two fits. No stable superiority, no adverse
instance, no evidence that C can be discarded, no F(C) versus F(M) comparison, no tuned
headroom, no equivalence, no mechanism, no default change and no C promotion follow. The
two-block C/M claim and its label are unchanged. The G2 allocation ends with this original
regardless of sign; a further object is a direction-tier question.

Predictions (card §3, recorded before launch): T_F,2 TRANSFERS .45 / WITHIN_MEI .35 / ADVERSE
.20, realized WITHIN_MEI, multiclass Brier .665, the modal forecast (TRANSFERS) did not occur;
T_D,2 UP .35 / WITHIN .45 / DOWN .20, realized WITHIN_MEI, Brier .465, modal forecast occurred
([PREDICTIONS.json](evidence/m_deployment_transfer_b02_20260915/PREDICTIONS.json)). B01's
forecasts are not revised. Owner prediction not taken (unattended); canonical review inbox
checked at intake.
