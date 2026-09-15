# FOLR_ENTITY_PERSISTENCE_B01_781701 — E0 result evidence

Evidence class B/EXPLORE. Fixed [card](FOLR_ENTITY_PERSISTENCE_B01_SCIENCE_CARD_20260914.md).
Both original invocations completed at source
42e337f36bd36c5dd24a7862eb71144f44fdef57, CPU FP32/Torch1/1 on hmasd-wsl-node.
One fresh unscreened fitted policy per arm; training seed781701 and evaluation
seed1781701. This object supplies no C consumption state.

## Rule applied verbatim

"Strict d>1 selects PERSISTENT_ABOVE_MEI; inclusive −1<=d<=1 selects WITHIN_MEI
with sign preserved; strict d<−1 selects CURRENT_ONLY_ABOVE_MEI."

Here d=mean(A)−mean(Z)=−3.069453125. The fixed reading is
**CURRENT_ONLY_ABOVE_MEI**. The contrast favors Z by more than the declared
absolute1-unit MEI in this selected complete learning/evaluation instance.
It is not a significance, equivalence, competence or stable-ranking decision.

| Selected final observable | Z: current-only entity state | A: persistent entity state |
|---|---:|---:|
| Mean native return | 1.59265625 | −1.476796875 |
| Episode sample SD | 7.1520175541 | 4.7745108887 |
| Conditional episode SE | 0.6321550140 | 0.4220111283 |
| Range | [−15.1,21.28] | [−17.54,11.99] |
| Negative returns | 57/128 | 84/128 |
| Training episodes / native ticks | 5000 / 100000 | 5000 / 100000 |
| RMSprop updates | 4969 | 4969 |
| Final evaluation episodes / ticks | 128 / 2560 | 128 / 2560 |
| Registered actor parameters | 192741 | 192741 |
| Actor parameter movement L2 | 45.8567639738 | 44.3868887812 |
| Full invocation wall, seconds | 2930.62 | 2829.32 |
| Aggregate user+system CPU, seconds | 2931.17 | 2828.21 |
| Peak RSS, KiB | 857528 | 865784 |

Machine-generated exposure: **2 fresh fits;200000 native training ticks;9938
RMSprop steps;2 final checkpoints;256 final greedy episodes/5120 evaluation
ticks; no screening/retry/checkpoint selection.** Total native ticks205120.
Native wall sum5759.94s and aggregate CPU5759.38s; peak RSS maximum865784KiB.
The10800s native plan was not a watchdog or endpoint. Full support/provider/
lifetime costs remain UNKNOWN; the old known native subtotal16513.92s is not
overwritten or treated as complete lifetime cost.

## Source, terminal, primary and preservation checks

DM checked object/arm/source/seeds, exact5000/4969/128 exposure, complete finite
training and evaluation arrays, nonzero optimizer/parameter movement,192741
parameters and CPU FP32/Torch1/1. Checkpoints contain separate online/target actor
and mixer states, finite optimizer state, correct arm/4969 updates and192768
actor state elements including27 buffers. Source checkout remained at the exact
accepted SHA with no tracked modifications. No source repair or new execution
occurred after result acquisition.

Both adjacent memory admissions passed physical and effective4GiB: Z
15285231616bytes at23:26:49Z; A15630495744bytes at00:17:51Z. Original supervisor
handles are folr-persistence-b01-781701-current-only (PID3695656) and
folr-persistence-b01-781701-persistent (PID3698859). Both exited0 with tmux false.
Raw exit logs report2026-09-15T00:15:40Z and01:05:00Z, respectively. Monitor
native final returned A terminal with a command-generated UTC status observation
at01:06:53.5531751Z; DM independently collected at01:07:23.914596Z. Earlier Z
Monitor observation timestamps are not trusted; [recovery](entity_persistence_b01_781701/MONITOR_RECOVERY.md)
preserves the discrepancies separately from the raw supervisor evidence.

All output/checkpoint and supervisor files were archived:10 members per arm.
Local transfer verifies archive digest, exact member set, byte counts and every
member SHA256. Original summaries are retained both directly and inside archives.
The A input digest matches the original Z summary. The DM recomputed both episode
panels from full arrays and applied the accepted publication function over the
selected bytes; its result exactly matches A's published pair_primary.

| Preserved artifact | SHA256 |
|---|---|
| Z summary | cfbeb5e9e7c8fd750a73c706a22e5719afce57d0f8a2b481e2f6fb2fe39ad61b |
| A summary | a491708b5a78c6032da7ad183205d0e959b6271eb02bf74a9d77da3caee379ec |
| Z final checkpoint | 000b9d4ef034b01f647009780a316991d6ec070e8a01e53bfd3be1029e654589 |
| A final checkpoint | 943275586d67df72e025cd596def597c92cc7cbf0641b07bf405fd84f17f363a |
| CURRENT_ONLY_RAW.tar.gz | 5b5ae7c891f467e82af1954714cad1d02a43cf12473dc14d6d4fa1e794448065 |
| PERSISTENT_RAW.tar.gz | c5eb3b5a863f9695c8e882ea11d921ca789e27dfb2c740a83c9fda75b4cab2ad |

See the per-arm COLLECTION/LOCAL_VERIFICATION/MONITOR_TERMINAL records and
[PAIR_READBACK.json](entity_persistence_b01_781701/PAIR_READBACK.json).
[RUN_SCORES.csv](entity_persistence_b01_781701/RUN_SCORES.csv) has one endpoint
row per fitted policy. Scientific-tools summarize_runs.py produced
[RUN_SUMMARY.json](entity_persistence_b01_781701/RUN_SUMMARY.json) without
--paired: n=1 per arm, no training-level SD or confidence interval. Equal seed
labels do not establish paired worlds or independent arm draws. The two128-episode
panels and their negative-count difference are not paired episode improvements.

## Deviations and bounded meaning

No scientific budget, arm, source, endpoint, RNG, information or device deviation
occurred. Original Z and A were both executed irrespective of Z's score. Focused
engineering22 checks plus5 changed-publication checks and independent Astra/high
review found one missing negative-count diagnostic, repaired before either launch;
all material findings were resolved at the accepted source.331 added source lines/
209-line runner remain inside declared section5 limits. No native smoke or retry.

Observation handover failures and one preparation fetch repair are technical
events, not scientific negatives. Local test scratch deletion was automatically
rejected before execution and remains a named cleanup limitation in ENGINEERING.md.
Remote preservation inventory and assigned cleanup follow collection; the authoring
checkout stays active. No historical result/quarantine is lifted.

The contrast concerns persistent entity-state input inside the same augmented
network. Z retains adaptive Generic recurrence, seen/age bookkeeping and common
public lifecycle cues; it is not a memoryless policy. Equal registered parameter counts do
not equalize temporal capacity or optimization: Z's entity recurrent weight sees
zero prior hidden inputs. Native history usefulness, stability, convergence,
competence, tuned headroom and transfer remain unestablished. This adverse A−Z
instance does not rewrite the old positive A−G block or the old adverse BANK blocks.
