# RCLE TBCFV A02 — terminal result evidence

**COMPLETE, technically accepted at the frozen-state A/RECON ceiling.** The sole selected
invocation completed with every planned graph, cell and fixed-input measurement. No retry,
node switch, added sample, optimizer step, baseline update or successor was executed.
Scientific interpretation and next-object selection remain with the DM.

Contract: [frozen card](RCLE_TBCFV_A02_FROZEN_SCORE_ALLOCATION_SCIENCE_CARD_20260906.md)
§§2–6. Implementation and exact command:
[CM record](RCLE_TBCFV_A02_CM_RECORD_20260906.md). Full measured values:
[raw summary](a02_frozen_score_allocation_20260906/summary.json),
[all primary tables](a02_frozen_score_allocation_20260906/PRIMARY_TABLES.md).

## Terminal and execution facts

- Launch SHA `abcc3766c2b2d9908c9391b0827d9f2a39f8d641`, Root-integrated and pushed.
- Node `wsl_4070`, detached cwd `/home/wu/hmasd-worktrees/rcle-a02-abcc376`;
  handle `rcle-a02-20260906`, supervisor PID 2439912, start epoch `1788752496`.
- Supervisor start `2026-09-07T03:41:36Z`, terminal `2026-09-07T03:41:43Z`,
  equivalent owner-local September 6 20:41:36–20:41:43 PDT. Its
  [terminal log](a02_frozen_score_allocation_20260906/task.stdout) and retained exit witness
  report **exit 0**. Runner status is **COMPLETE**. No operation remained in flight.
- [Same-node admission](a02_frozen_score_allocation_20260906/memory.json) at
  `2026-09-07T03:41:36.420464Z` passed physical and effective availability:
  **15,257,608,192 bytes = 14.2097549438 GiB**, both above 4 GiB. Preflight and runner
  were joined by `&&` inside the accepted supervisor command.
- [GNU whole-process time](a02_frozen_score_allocation_20260906/complete.time):
  **7.02 s wall**, 5.75 s user + 0.28 s system = **6.03 CPU-s** at the tool's descendant
  accounting scope; **588,848 KiB = 602,980,352 bytes peak RSS**. Whole-process wall includes
  interpreter startup, required imports/native loading or build, all measurement and final output
  writing. The summary's 5.927895314 s is explicitly narrower, excluding final summary writing.
- Supporting focused-check debit **12.7002317 s** plus whole result process 7.02 s is
  **19.7202317 s charged**, below the 300 s object cap and frozen 287 s process bound.
  Sequential result critical path and result invocation wall are identical; supporting checks
  are charged once. Cold-build cost was not isolated and is not invented as zero.

Before acceptance, a non-login-shell Git fetch and partial-clone blob fetch stalled. Only those
CM-owned preparation processes were terminated. Preparation then succeeded through configured
`zsh -lic`; the exact SHA was checked out without source changes. This was Git/network preparation,
not an experiment attempt. Git/SSH preparation and artifact collection are outside result-machine
wall as specified; no result-bearing command existed before the one accepted handle.

The configured independent monitor received the accepted handle directly via the app with
Luna/low. CM observed the terminal fact before the forwarded adoption ACK; Root then forwarded
adoption and CM released routine polling. CM performed only terminal collection/acceptance after ACK.

## Complete exposure and identity

| Quantity | Planned | Observed |
| --- | ---: | ---: |
| Single-constructed models | at most 4 | 4 |
| Configurations x probe blocks | 4 x 2 | all 8 |
| Episodes | 512 | 512 |
| Environment ticks | 32,768 | 32,768 |
| Derivative attempts / completed evaluations | at most 32 | 32 / 32 |
| Optimizer / baseline updates | 0 / 0 | 0 / 0 |
| Raw fixed-input points | 256 | 256 unique |
| Six-way probability vectors | 768 | 768 |

Technical fixtures remain separate: 16 non-card episodes, 17 derivative attempts / 16 completed
evaluations with one deliberately interrupted synthetic call; they are not part of result
denominators. Artifact readback and table generation added no model forward, derivative or episode.

Final-state hashes match the frozen card:
C1P1 `3c277fee5ec01adbdd259bc809126bd6eaaa85affbe7b716425d2da14895d13e`;
FLEX `66d23ae708edbf6ab02003400bdd961451b81dc6f68b6c0e55118b1478e490f0`.
Both contain all 30 named tensors. The reconstructed seed18 theta0 norm is
**21.205717682888878**, compared with retained **21.205717682888885**; the declared local
identity check passed. Initialization was reconstructed, not loaded or retrained.

Both final baselines were reconstructed from their own retained 200 ordered full-precision
per-cell curves. No fallback was used. Original `math.fsum/len` curve means versus learner
`torch.mean` create the disclosed FP64 reduction-order limit; this is not bit-equivalent recovery
of the missing buffer. All eight baseline values, Y means/population SDs and advantage
mean/RMS/population SDs are retained for each graph in the primary tables and raw summary.

## Primary observations and literal card readings

All eight `g - g_M - g_A` residuals passed the card's local tolerance. Largest observed norm
residual: **7.624346369010137e-17**. Each projection includes all 30 named tensors in five
disjoint groups, preserving no-graph versus numerical-zero states. Readback recomputation of the
published tensor norms found maximum squared-norm coverage discrepancy **2.220446049250313e-16**.

| Final configuration | Block | r_A original | r_P original | Original / zero total norm | cos(original, zero) |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1P1-final | 19001 | 0.00758724535 | 0.00760733249 | 0.0988989568 | 0.811611093 |
| C1P1-final | 19002 | 0.00671868818 | 0.00673617113 | 0.0453089754 | -0.189325433 |
| FLEX-final | 19001 | 0.00760950255 | 0.00761280071 | 0.0989116764 | 0.811568586 |
| FLEX-final | 19002 | 0.00641083238 | 0.00641687601 | 0.0463483646 | -0.244324980 |

**Literal descriptive rule:** every one of the four logical configurations, including both
initial configurations, satisfies r_A<=0.01 and r_P<=0.01 in both blocks. Thus the card permits
“very low sampled actor-score contribution and pointer allocation in these two samples.”
All eight graphs also satisfy the weaker manager-dominant r_A<0.5 reading. This does not establish
that the actor has no role or received no gradient during training.

The same-graph zero-baseline comparison changes direction as well as magnitude. In the second
block its direction cosine with the original-baseline joint gradient is negative for both finals;
the first block is about 0.812. These are frozen finite-sample derivatives, not a zero-baseline
training result or permission to launch a baseline variant. Shared encoder and FLEX-head
projections, cancellation and all zero-baseline r_A/r_P values accompany the full primary tables.

| Direct parameter difference | Full norm | Encoder norm | Manager norm | Pointer norm | Common head norm | Agent head norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1P1-final minus init | 0.472889394 | 0.236357695 | 0.409282064 | 0.0157356670 | 0 | 0 |
| FLEX-final minus init | 0.472943899 | 0.236177737 | 0.409450372 | 0.0156912522 | 0.000279550939 | 0.000327731230 |
| FLEX-final minus C1P1-final | 0.00234143919 | 0.000889832705 | 0.00212181439 | 0.0000536881510 | 0.000279550939 | 0.000327731230 |

The final-to-final difference above is measured directly from tensors; it is not the difference
of the two displacement norms and does not decompose the history of 200 training updates.

| Probe block | C1P1-final / init mean TV | Maximum TV | FLEX-final / init mean TV | Maximum TV | FLEX-final / C1P1-final mean TV | Maximum TV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 19001 | 0.00535123840 | 0.0103800609 | 0.00534134180 | 0.0103474469 | 0.0000172250146 | 0.0000348291830 |
| 19002 | 0.00544612839 | 0.0106404335 | 0.00543670243 | 0.0106135669 | 0.0000164804789 | 0.0000363948778 |

Both final-versus-init block means meet the prechosen TV<=0.01 descriptive scale; maxima exceed
0.01, so the result is small average conditional change, not every probability vector unchanged.
All 16 cell/block rows and two whole-block rows, including three snapshot entropies and every
TV mean/maximum, are retained. The library fixes z and external input: no full-policy latent,
visitation-distribution or causal service claim follows.

## Artifact acceptance and remaining limits

[Artifact readback](a02_frozen_score_allocation_20260906/artifact_readback.json) records the raw
library origin and collected copy. The 586,817-byte `fixed_inputs.pt` SHA256 is
**`13e480994acc47e5183aa174a1a3ace81e166ae4e46a72a50a3227408864fb61`**, matching remote and local.
Remote origin is under this A02 result root; collected local copy is
`C:/Projects/HMASD/temp/directions/roster_consistent_latent_exploration/exp/tbcfv_a02_collected_20260906/fixed_inputs.pt`.

Readback found 256 unique point identities: two scenarios (0,1), four ticks (0,24,28,60), first
and last active members, 16 points in every cell/block. Three arrays have shape `[256,6]`, CPU
FP64 finite nonnegative values, maximum probability-sum error **3.3306690738754696e-16**.
Recomputing entropy and TV from stored vectors using Python `math.fsum` gave maximum difference
from the published summary **4.440892098500626e-16**. This adds no model execution.

The raw summary retains all original data needed by the reading rule, including per-tensor norms.
The pointer file is kept at the remote and collected local locations rather than duplicated as
a Git binary. No measurement dependency is quarantined. Remaining limits are exactly the card's
single training seed/two probe blocks, baseline reduction-order precision, conditional fixed-input
ceiling and lack of a new algorithm effect. No unique cause, future learner efficacy or general
policy invariance is established. DM owns prediction scoring, Chinese brief, intake and any later
object choice; this selected spend ends here.

scope: none
