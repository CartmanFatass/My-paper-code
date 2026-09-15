# FOLR entity current increment B01 — E0 result

Object: FOLR_ENTITY_CURRENT_INCREMENT_B01_781801, B / EXPLORE.
The [frozen card](FOLR_ENTITY_CURRENT_INCREMENT_B01_SCIENCE_CARD_20260914.md) at
8ad304d61af6885c0ca5ba236bbf6c2c160e61f4 selects one fresh Generic G and one fresh
current-only augmented Z. Exact execution uses that source for both original
invocations; DM technical acceptance/independent code review is at8d17e4aa3.
Authoring checkout: C:/Projects/HMASD-worktrees/codex-vap-folr, codex/vap-folr.

## Primary and complete endpoints

**Z−G = −4.44375; GENERIC_ABOVE_MEI.** The rule applied without alteration is:
"Strict d>1 selects CURRENT_ONLY_ABOVE_MEI; inclusive −1<=d<=1 selects WITHIN_MEI
with sign preserved; strict d<−1 selects GENERIC_ABOVE_MEI."
The absolute MEI1 is an effect-importance boundary, not a significance, competence
or equivalence certificate. This is a comparison of one fitted program per arm.

| Quantity | G: GENERIC_RETAIN | Z: AUGMENTED_CURRENT_ONLY |
| --- | ---: | ---: |
| Final mean native return | 4.307734375 | −0.136015625 |
| Conditional episode SD | 9.166581225405613 | 7.467901953715321 |
| Conditional episode SE | 0.8102189680977001 | 0.6600755140885463 |
| Final return range | [−21.56,29.03] | [−23.78,15.20] |
| Negative final episodes | 40/128 | 69/128 |
| Training episodes / ticks | 5000 / 100000 | 5000 / 100000 |
| RMSprop updates | 4969 | 4969 |
| Final greedy episodes / ticks | 128 / 2560 | 128 / 2560 |
| Registered actor parameters | 103173 | 192741 |
| Actor parameter change L2 | 34.046542076775566 | 39.67975006716655 |
| External native wall seconds | 2112.27 | 2080.16 |
| Process user + system CPU seconds | 2112.83 | 2079.15 |
| Peak RSS KiB | 770268 | 858384 |

Both use training seed781801/evaluation seed1781801, reset before construction and
final evaluation, CPU FP32, Torch2.7.0+cu118 / NumPy1.26.3 / Torch threads1/1.
Each owns fresh weights, replay, optimizer and targets. Compatible Generic/mixer
construction is aligned, not the complete unequal networks. Common seed labels
do not establish independent arm draws or paired episode worlds. There is no
paired-difference SE or training-population CI. RUN_SCORES.csv contains two rows,
one per fitted program; scientific-tools RUN_SUMMARY.json reports n1 per arm,
SDnull and no paired differences. Neither episodes nor historical objects inflate n.

## Technical evidence and provenance

The evidence root is [entity_current_increment_b01_781801](entity_current_increment_b01_781801/).
Per-arm COLLECTION records verify the clean exact source, arm/object/seeds, all
native counts, finite train/final arrays and complete checkpoint. LOCAL_VERIFICATION
checks every archived member after transfer. PAIR_READBACK.json recomputes both
panels and the selected publisher's primary from the exact original summary bytes;
it equals Z's pair_primary. Z consumed the original collected G digest only after
its learning and evaluation; no G output enters its optimizer or endpoint selection.

| Binding | G | Z |
| --- | --- | --- |
| Accepted handle | folr-current-increment-b01-781801-generic | folr-current-increment-b01-781801-current-only |
| Supervisor status PID | 3702285 | 3703852 |
| Accepted UTC | 2026-09-15T02:18:02.432323Z | 2026-09-15T02:59:58.244731Z |
| Raw supervisor terminal UTC | 2026-09-15T02:53:14Z | 2026-09-15T03:34:38Z |
| Supervisor / external invocation exit | 0 / 0 | 0 / 0 |
| Memory available at adjacent admission, bytes | 14991753216 | 15626321920 |
| Checkpoint tensor count | 176 | 230 |
| Actor / target state elements | 103199 / 103199 | 192768 / 192768 |
| Optimizer slots | 41 | 54 |

Both physical/effective memory floors passed >=4294967296 bytes. Original checkpoint
loads without map_location show all finite CPU tensors and floating dtype FP32.
State-element counts include registered buffers, distinct from actor parameter counts.
Native supervisor logs use +08:00 terminal timestamps; the table converts those
instants to UTC. Monitor confirmation and collection times remain separately recorded.

Summary SHA256:

- G: `49b98f1ce155c4c90798692c3a8de844293e5133b669ed4d926b0f3fd2a99e93`.
- Z: `5ae6d9cdb813e78c3e73773d1199b85c8e447993207271e21b911bdb438e24e1`.

Final checkpoint SHA256:

- G: `d32cd0a4ed27e108d51b7c934d924cd30e3a022ec0876d61f7507a9b66ffc290`.
- Z: `99b94e3bf9d5cec1db3c096a8dcf079b7a20dd7d03c26e82bc5806b1a94967a7`.

Original raw archive SHA256 (10 members each, all verified locally):

- GENERIC_RAW.tar.gz, 4288032 bytes:
  `9e7ae325d7432caa9d301b8abaa0360ecbfbd7e4e9d9ec545640e5f380141cc1`.
- CURRENT_ONLY_RAW.tar.gz, 5290873 bytes:
  `7772f813c0677c49addfb51d8a72ec9596fbcd3dc4e16bd6f1cc8cab7394cb33`.

## Costs, failures and evidence ceiling

Two original fits completed: 200000 training ticks, 9938 RMSprop steps, two final
checkpoints, 256 greedy episodes / 5120 evaluation ticks, 205120 ticks overall.
Summed external native wall4192.43s and CPU4191.98s are measured. The ordinary G
plan1800s was exceeded by312.27s; total ordinary plan7200s was not a watchdog or
owner hard cap. The heterogeneous4109.30s pre-run reference was not a forecast or
speed claim. Full engineering/support/provider/lifetime cost remains UNKNOWN.
No new resource telemetry is inferred from timing similarity between these arms.

All19 focused synthetic cases passed after a missing-parent setup repair; its
logs and a post-success within-scratch symlink cleanup assertion are preserved.
No native smoke or result-bearing retry occurred. The source/shell325 lines and
bounded collection/analysis140 lines stay within this card's600 non-test lines;
runner209 lines. No section5 budget breach or result-invalidating defect was found.
The independent code review is complete; independent scientific result review
remains the next required closeout work, not implicitly accepted by code review.

The native Monitor used the honestly declared terminal-only final fallback because
send_message was unavailable. G's initial state-path claim was corrected to the
actual local generic/MONITOR_STATE.json; its copied runner_pid is not independently
measured learner-PID evidence. Z uses the correct explicit local state path and
supervisor_pid label. No intermediate MONITOR_ADOPTED was fabricated. Raw exit
witnesses and independent collection establish both terminals; no science process
was stopped. These technical issues change no scientific polarity or budget.

This supports favoring Generic over this Z package in the selected finite
realization. It does not identify a unique cause, prove augmentation/history
ineffective, establish a stable ordering, or close the direction/family. Old A−G
positive, A−Z adverse persistence contrast and replacement BANK negatives remain
distinct adaptive objects. The intake applies current §11.11 without retrograding
their original rules. No competence, transfer, scaling, efficiency or C/UAV claim
follows. See the [scientific intake](FOLR_ENTITY_CURRENT_INCREMENT_B01_INTAKE_20260914.md).
