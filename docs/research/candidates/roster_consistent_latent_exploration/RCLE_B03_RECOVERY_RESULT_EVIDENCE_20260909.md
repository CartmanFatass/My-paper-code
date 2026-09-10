# B03 missing-only recovery E0 — technical acceptance PASS

The newly allocated W100→reference sequence completed with exit0. Historical W1 and
shared initialization remain frozen inputs. **Delta_U=+0.013224283854166657**, conditional
scenario SE0.0015969401899458364, approximate95% interval
[0.010094281081872818,0.016354286626460497]. This supplies the missing original-seed
comparison; it neither supplies a second independent seed nor proves the signal11 cured.

Source `4e89f24197a79d0b4fc724018f0223ca2c1e4289`, launch record `41a3577e5`.
[CM record](RCLE_B03_RECOVERY_CM_RECORD_20260909.md) documents the narrow change,
5.0949401s focused check and independent review. Root separately allocated this batch
against [recovery card](RCLE_B03_RECOVERY_SCIENCE_CARD_20260909.md) at7415f9a2d;
the old failed attempt remains incomplete. No additional invocation remains allocated.

## Native comparison and preserved losses

| AC path | Historical W1 U | New W100 U | W1−W100 | W100 G_U | Reference U |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8→12 | 0.6923502604 | 0.6789143880 | +0.0134358724 | +0.0135253906 | 0.2502522786 |
| 12→8 | 0.7163208008 | 0.7033081055 | +0.0130126953 | +0.0132324219 | 0.3218750000 |

Equal-weight G_U is0.01337890625 for W100 versus historical W1's0.000154622395833341.
Tau mean40/tau40 fraction1 remains on every learned cell. W100 primary-path40U is
27.1565755208/28.1323242188. The eight-cell secondary W100 U is0.6903513590494792;
reference U0.2884312947591146, tau39.625, tau40 fraction0.98583984375. Reference Y is
null because the unchanged scripted result has no Y; no upper/tuned headroom is claimed.
For8→12, scenario differences include84 negative,2 zero,170 positive; for12→8 they
include87 negative,9 zero,160 positive. Every assigned row and cell remains retained.

Original card §5 applicable descriptive row, verbatim: **“0<Delta_U<0.05 — Small local
positive signal; judge another named comparison using path outcomes, G_U and actual cost.”**
The positive difference and both G_U values remain below MEI0.05; recovery is saturated.
One historically completed control plus this completion fit provides one paired seed,
conditional on disclosed outcome-informed recovery. It is no stable-superiority,
training-population uncertainty or pure actor-credit-cause claim. DM owns full intake
and prediction scoring, with all overlapping original-card branches retained.

## Technical evidence

[Summary](RCLE_B03_RECOVERY_RESULT_SUMMARY_20260909.json) records both raw summary metadata,
the historical control, admissions, supervisor, hashes and independent row arithmetic.
[Raw rows](RCLE_B03_RECOVERY_RAW_ROWS_20260909.csv) contain8,192 observations across
historical init/W1 and new W100/reference. [Training curves](RCLE_B03_RECOVERY_TRAINING_CURVES_20260909.json)
contain all200 new blocks. No simulation or fitted model call was used for readback.

- New W100 has12,800 training episodes,200 backward/step calls,200 nonzero updates and
  zero zero-steps; each block has64 episodes/eight cells and4,096 ticks. New final and
  reference panels each have2,048 rows,256 distinct indices per each of8 cells.
  Increment:16,896 episodes/1,081,344 ticks/200 backward calls; six model allocations,
  one training instance plus five untrained helpers. No initialization panel repeated.
- All200 JSONL rows exactly equal final summary curves, sequential updates0–199. Step
  order/magnitudes, finite native values and raw norms pass retained-data checks.
  Final checkpoint has26,161 finite FP64 scalars. Initial norm21.230992499025053 and
  final displacement0.5938813516434148 are retained; no parameter-motion claim substitutes
  for native service. Initial checkpoint bytes exactly match the historical initial file.
- Scientific root/block digest, native source/artifact/build key and ABI/runtime ABI
  equal historical W1. W1 input remains1,367,051bytes with SHA256
  `a678a5d115a0c4c9d176423ab291f2daa4629bfb13e4f2286e7b68dacfe7acdf` after execution.
  Only its summary was staged; no old trained state was loaded. Independent arithmetic
  from raw paired indices reproduces both path deltas, equal mean and SE.
- Ten new output files and six supervisor files match remote hashes. No fatal event
  recurred in this invocation; that observation does not identify or cure the old cause.
  Known cumulative episodes/ticks/calls are33,792/2,162,688/400 **plus the original unknown
  W100 prefix**, not a zero-consumption rewrite. Cumulative model allocations18; three
  started training instances, two completed fits forming one pair.

## Complete execution, costs and Monitor transfer

Node wsl_4070, CPU FP64/one compute thread; detached cwd
`/home/wu/hmasd-worktrees/rcle-b03-recovery-20260909`; source above. Output beneath cwd:
`temp/directions/roster_consistent_latent_exploration/exp/b03-actor100-recovery-20260909`.
Staged input `/home/wu/hmasd-inputs/rcle-b03-recovery-20260909/W1-summary.json`.
Handle `rcle-b03-recovery-20260909`, PID3071849. Direct Monitor dispatch succeeded;
Root confirmed actual adoption21:53:07.3009905UTC. Monitor observed finished/exit0/tmuxfalse
at21:54:18.0312972UTC, reporting exit21:54:09UTC and event
`rcle-b03-recovery-20260909-exit0`. Root resumed original CM for collection.
CM did not maintain a parallel polling loop. Copied terminal supervisor files agree.

W100 complete wall **70.95s≤600s**, reference **2.59s≤30s**; logical sum73.54s.
Complete sequential remote chain including both admissions **73.62s**, charged once.
External timing includes startup and final publication; internal summary timing ends
before the final write and is not the complete bill. Both admissions passed: W100
physical/effective15,634,997,248bytes; reference15,635,030,016bytes, exceeding4GiB.
Peak RSS591,452KiB W100/whole-chain; reference429,500KiB. Aggregate CPU unmeasured.

Additional measured work: focused check5.0949401s; staging source/shell/input verification
0.5501623s; collection3.0204332s; remote-digest/readback shell0.8780937s; arithmetic/raw
publication0.3649094s; checkpoint/input verification2.7547207s. Conservatively include
network overhead in these collection windows. These sum with the chain to86.2832594s.
Charge **100s complete incremental work** including final serialization/document checks
and other short preparation tails, below750s. Git/agent/network staging elapsed remains
separate/unmeasured as a shared window. Remote critical path73.62s differs from summed
work and from first-check-to-E0 elapsed (unmeasured). Old160+.5983968s remains; named
old+new conservative charge260.5983968s is not a full-history wall or CPU total.

## Preservation and next owner

New raw outputs, supervisor and readback script are collected at the shared authoring
checkout's `temp/directions/roster_consistent_latent_exploration/exp/b03-actor100-recovery-20260909`.
Output inventory/digests live in the summary. Remote checkout is clean; execution, input
staging and supervisor are retained for Root's explicit integration/closeout trigger.
All old archives and local evidence remain preserved. DM receives the complete technical
result for scientific intake; Root owns integration and later closeout acceptance.

Automatic approval review rejected the new owned test-scratch removal as `blocked by
policy`; exact path is recorded in the CM record. It remains untouched after rejection,
alongside the older independently blocked scratch. No bypass/retry was attempted.
