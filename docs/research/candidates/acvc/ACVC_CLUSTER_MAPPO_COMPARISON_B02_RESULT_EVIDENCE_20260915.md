# ACVC_CLUSTER_MAPPO_COMPARISON_B02 — E0 result evidence

## Bound object, source and rule

B/EXPLORE, the second prospectively paired training block MASTER 28431 / EVAL 38431, exactly
two original fits, selected by `em:acvc:convergence` (A, k = 1,
[intake](pro_packets/20260915_cluster_mappo_comparison_b01_result_review/INTAKE.md)) and
funded by `portfolio:cross_direction` (G,
[decision](../../portfolio/decisions/2026-09-15-acvc-one-block-replication-grant.md)). The
object, protocol, C recipe, M recipe, adapter and reading rule are the unchanged
[block-1 card](ACVC_CLUSTER_MAPPO_COMPARISON_B01_SCIENCE_CARD_20260914.md); only the block
identities change, bound by the reviewed wrapper `scripts/run_acvc_cluster_mappo_comparison_b02.py`
(review at `3ae041d9e`). Exact launch source `2dc9631c8644464b8c4189a53344b2956c3eb3b4`
(`codex/acvc`); pinned on-policy `de66d7a4b23fac2513f56f96f73b3f5cb96695ac` re-staged
([DEPENDENCY.json](evidence/cluster_mappo_comparison_b02_20260915/DEPENDENCY.json)).

Primary reading rule applied verbatim:
- `delta_F_M > .01`: F_ABOVE_MEI.
- `-.01 <= delta_F_M <= .01`: WITHIN_MEI, a small signed point observation, not equivalence.
- `delta_F_M < -.01`: M_ABOVE_MEI.
- Missing/incomplete bound operand: INCOMPLETE for that contrast.

J is the complete native team episode sum divided by 256. Both fits and all four sole-final
64-world panels are complete. The unrounded primary D2 is **−.03919008143501977 J**, so the
frozen point rule gives **M_ABOVE_MEI**. This reverses block 1's F_ABOVE_MEI
(+.02343964960218458 J). No interval, significance or seed-SD gate replaces the rule.

## Absolute scores and every declared contrast (block 2)

| Package | Mean J | Mean episode sum S |
|---|---:|---:|
| C | .30753226910460413 | 78.72826089077866 |
| F | .3550285226822827 | 90.88730180666437 |
| own-dwell | .3233147586368092 | 82.76857821102315 |
| M | .3942186041173025 | 100.91996265402943 |

| Contrast | Mean delta J | Sample SD J | Conditional SE J | Adverse/favorable worlds | Worst delta J | Frozen reading |
|---|---:|---:|---:|---:|---:|---|
| F−M (primary, D2) | −.03919008143501977 | .08174563280528697 | .010218204100660872 | 49/15 | −.19628654994165962 | M_ABOVE_MEI |
| C−M | −.08668633501269826 | .09852381389866599 | .012315476737333249 | 57/7 | −.39164867534040215 | DOWN |
| F−C | +.0474962535776785 | .07185570767715804 | .008981963459644755 | 16/48 | −.1764493425652759 | UP |
| F−own-dwell | +.031713764045473436 | .05978973795031318 | .007473717243789147 | 16/48 | −.14234911322012034 | UP |

No zero world differences occur. [COMPARISON.json](evidence/cluster_mappo_comparison_b02_20260915/COMPARISON.json)
(the wrapper's `--mode reduce` output over the two collected summaries) and
[WORLD_DIFFERENCES.csv](evidence/cluster_mappo_comparison_b02_20260915/WORLD_DIFFERENCES.csv)
retain every absolute score and difference. These are conditional world summaries for the
attained fitted policies; two fitted arms form one training block; four panels are not four
fits.

## Fixed equal-block accumulation with block 1

Reported after D1 and D2 individually, per the grant's rule (`pooled_mean = (D1 + D2)/2`,
`block_SD = |D2 − D1|/√2`, `block_SE = block_SD/√2`, interval `pooled_mean ± 12.706 × block_SE`,
df = 1), labelled an iid-normal complete-block working-model description; two blocks cannot
validate its coverage, especially after outcome-informed continuation. Block 1 is not rescored.
[TWO_BLOCK_ACCUMULATION.json](evidence/cluster_mappo_comparison_b02_20260915/TWO_BLOCK_ACCUMULATION.json).

| Contrast | D1 (28331) | D2 (28431) | Pooled mean J | Block SD J | Block SE J | df = 1 interval |
|---|---:|---:|---:|---:|---:|---|
| F−M (primary) | +.02343964960218458 | −.03919008143501977 | −.007875215916417596 | .04428590752029677 | .031314865518602165 | [−.4057618971957767, +.3900114653629415] |
| C−M | −.011309900227360047 | −.08668633501269826 | −.048998117620029154 | .05329918817837822 | .03768821739266911 | [−.5278646078112829, +.4298683725712245] |
| F−C | +.03474954982954462 | +.0474962535776785 | +.04112290170361156 | .009013280658081447 | .006373351874066939 | [−.03985690720828296, +.12210271061550608] |
| F−own-dwell | +.012221377181678915 | +.031713764045473436 | +.021967570613576175 | .013783198932900685 | .00974619343189726 | [−.1018675631321104, +.14580270435926274] |

The primary reverses sign between blocks; its pooled mean sits inside the ±.01 J band with an
interval more than forty times wider. F−C and F−own-dwell are UP in both blocks with small
block-to-block dispersion; both df = 1 intervals still include zero.

## Actual exposure, implementation and measurement limits

Each fit: 4,096 H256 training episodes, 2,048 rollouts, 8,192 PPO minibatches, 1,048,576
native training team ticks (`counts` in both summaries). C: 8,192 joint Adam steps, 192
evaluation episodes (three 64-world panels: C, F, own-dwell); M: 8,192 actor + 8,192 critic
Adam steps, 64 evaluation episodes. Totals for the block: 2 fits, 2,162,688 native team ticks,
24,576 optimizer steps, 2 final snapshots, 4 final loads. Every episode row (4,288 C, 4,160 M
including panels) has 256 steps and finite fields; every update row (8,192 C, 2,048 M) is
finite; parameter displacements are finite (C actor 7.408, critic 14.408; M actor 9.170,
critic 8.592, head 1.744). F executed 6,610 retraces. The inherited placeholder fields
(`selected_final_checkpoints` 0 in both; M `velocity_decisions`/`recurrent_observations` 0)
are **unmeasured** as in block 1 (§11.8.7), not evidence of absent behaviour; the primary does
not depend on them. `upstream_sha` appears only in the M summary, as in block 1 (C has no
on-policy dependency). No retry, tuning, midpoint, pilot or extra panel occurred.

Checks before launch: the three wrapper identity tests and the Opus review at `3ae041d9e`;
`git diff 3ae041d9e 2dc9631c8` over runner, wrapper, launch scripts and `hmasd/` empty; the
remote working file hashes to the committed blob. No separate launch review (grant).

## Complete native cost and preservation

| Original | PID | Whole native wall s | User + system CPU s | Peak RSS KiB | Native/supervisor exit |
|---|---:|---:|---:|---:|---|
| C | 3732902 | 2495.72 | 2494.23 | 562308 | 0/0 |
| M | 3736172 | 2427.41 | 2394.46 | 585504 | 0/0 |

Summed native wall 4,923.13 s (block 1: 3,191.66 s); the increase is contention with four to
five concurrent FSD fits on the same node (C beside four I1280/FLAT fits, M beside five FSD
elements), not a recipe change. Ordinary plans C 1,800 s / M 1,600 s were not caps. Both
adjacent admissions passed 4 GiB (C 5,225,508,864 B; M 13,061,177,344 B available). Support,
provider and lifetime costs remain UNKNOWN.

Both original nine-file sets were collected with per-file sha256 in `C_COLLECTION.json` /
`M_COLLECTION.json`, byte-identical to the remote digests. The seven non-checkpoint,
non-log files per arm are committed under
[evidence/…/native/](evidence/cluster_mappo_comparison_b02_20260915/native/); `final.pt`
(281,853 and 313,423 bytes) and `task.log` are excluded from Git by `.gitignore` and are
retained with the full sets in local archives
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/retained/cluster_mappo_comparison_b02_20260915/{C,M}_original.tar.gz`
([PRESERVATION.json](evidence/cluster_mappo_comparison_b02_20260915/PRESERVATION.json) carries
the archive digests), as for block 1. Launch facts and the scheduling record: [EXECUTION.md](evidence/cluster_mappo_comparison_b02_20260915/EXECUTION.md).
Remote reclamation of the worktree and staging follows the commit (CLEANUP.json).

## Bounded reading and prediction

Reliance on the block-1 package advantage is weakened, not erased: the first positive
observation remains, and block 2 puts M above F by .039 J with 49/64 adverse worlds while C
alone trails M by .087 J. Strongest surviving support for the optional package: F exceeds its
own C source and its own-dwell control in both blocks (pooled +.041 and +.022 J) with small
block dispersion. Via F−M = (F−C) + (C−M): C−M is negative in both blocks and it is F−M that
reverses sign, because the positive internal correction does not overcome C's larger deficit
to M in block 2 (correction recorded by `em:acvc:convergence`, 17:08Z; the earlier wording
"the C/M recipe difference varies in sign" was wrong). This is evidence for the attained finite-learning packages,
not stable superiority of either, tuned same-information headroom, equivalence, or K/N/
component attribution. Matching tuned headroom remains absent.

Predictions: the DM did not record a prospective block-2 forecast before the result (process
gap, recorded; no post hoc forecast is added). Owner prediction not taken; canonical review
inbox empty at intake. Block-1 Briers stand unchanged.
