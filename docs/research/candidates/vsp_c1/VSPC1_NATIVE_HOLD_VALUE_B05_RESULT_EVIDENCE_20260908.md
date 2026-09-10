# VSPC1 NATIVE HOLD VALUE B05 — E0 result evidence

The one allocated P70 invocation completed with exit 0, native status COMPLETE,
complete publication readback and no limit/cap breach. Technical acceptance is
PASS. No second submission, replay, extra seed or successor was executed.

[Collected evidence](results/native_hold_value_b05_8301_20260908/evidence.json)
retains the native summary, all 96 evaluation episode rows and 32 matched values
for each contrast, artifact checks/source, hashes, admission and complete terminal
receipts. [Staging](VSPC1_NATIVE_HOLD_VALUE_B05_P70_STAGING_EVIDENCE_20260908.json)
and [execution record](VSPC1_NATIVE_HOLD_VALUE_B05_P70_TECHNICAL_20260908.md)
bind the actual inputs. Scientific interpretation and any next allocation belong
to the DM's intake; this record applies the frozen arithmetic rule only.

## Binding and execution facts

Scientific SHA: `bda90e1db76a00123ba889ed6c4b05225473f4cb`; master 8301,
extra initialization 830100012. Wrapper commit:
`9c7971da3ec545b7c9a8847fc143455e31ad0d40`. Handle:
`vspc1_hold_value_b05_8301_bda90e1db76a`, PID 3019318 on `hmasd-wsl-node`.
CPU FP32, one process/numerical thread. Detached cwd:
`/home/wu/hmasd-worktrees/vspc1-native-hold-value-b05-8301-bda90e1db76a`.
Output:
`/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b05_8301_bda90e1db76a`.
Started 2026-09-09 04:31:42 UTC; terminal 04:36:57 UTC, exit 0, tmux inactive.
Local raw collection remains at
`temp/directions/vsp_c1/collection/native_hold_value_b05_8301_bda90e1db76a/`.

## Primary and frozen reading

| Arm | Mean native J |
| --- | ---: |
| GATED-V | 0.194786498888121 |
| MLP-V (wide133) | 0.17819458751184225 |
| H | 0.16509972954531915 |

| Matched contrast | Mean | Conditional SE |
| --- | ---: | ---: |
| GATED minus wider MLP | 0.01659191137627875 | 0.008099210958544987 |
| GATED minus H | 0.029686769342801844 | 0.011221422877033574 |
| Wider MLP minus H | 0.013094857966523096 | 0.01249800862351387 |

Card §5's rule is **Delta>.01 with trustworthy primary**. Its verbatim reading:
“UP: a local gated-package advantage over this specified similarly sized ordinary
critic; retain H and all outcomes, then assess whether one later independent pair
is worthwhile. No automatic follow-up allocation.” The observed Delta places this
instance in UP. The excess above .01 is smaller than the conditional SE; keep that
noise qualification. Both learned mean returns exceed H, with all adverse
individual identities retained. One matched training pair remains n=1; the 32
conditional evaluation differences are not 32 independent training seeds. No
stable superiority, specialized hold-credit mechanism or capacity causal effect
is established. Tuned same-information headroom remains absent; H is untuned.

## Technical acceptance and exposure

Artifact-only collection check PASS, exit 0, 2.3724121000850573s process wall.
No model construction, forward call, native evaluation or training replay occurred.
Remote/local SHA256 values match summary, episodes, rollouts, both final
checkpoints and admission. All 1,120 episode rows, 512 rollouts and 2,048 epoch
records reconcile: 286,720 native steps (262,144 training /24,576 evaluation),
2,048 Adam calls, 1,024 training episodes /96 final evaluations, two constructor
resets and zero partial steps. Reward/J decomposition, held-decision counts,
master/reset identities and all three primary contrasts/conditional SEs agree.

Checkpoint source/object/configuration/RNG identities and FP32 finiteness pass.
Critic counts are 34,817 GATED and 34,827 wider MLP. Actual wider checkpoint
second weight/bias shapes are (133,128)/(133,), output weight (1,133).
Final parameter norms agree with summary exposure. Total relative displacement
is 0.2566371782435865 GATED /0.2498335423431346 wider MLP. Gate absolute
movement is 0.6429120302200317; duration absolute movements are
0.08419010788202286 /0.1235380545258522. Their initial norms are zero, so relative
movement is undefined; the collected check supplies null for that reading while
preserving the raw native summary's historical reporting field.

Each arm has 131,072 target rows and 256 moment merges, increasing by 512 rows
per rollout. Normalized-squared losses and final moments agree across summary,
checkpoint and before/after evaluation; wider-MLP moments also remain frozen
through H. Final (mean, M2, scale): GATED (21.053756713867188,35270048,
16.4039363861084); wider MLP (19.920923233032227,33007296,15.869016647338867).
Nonzero held rows: GATED 1,506 train /96 eval; wider MLP 1,500 train /96 eval.
Raw full return-to-go arrays were not separately archived or replayed; accepted
source tests and actual recorded state/publication cover that boundary.

## Complete-path resources and deviations

Actual-node admission passed both floors with 15,637,360,640 available bytes.
Enclosing complete wall is 315.20s (supervisor duration 315s); internal pair wall
306.7498197230161s, wider-MLP start boundary 159.50694155402016s. Charging the
unpartitioned 8.450180276983872s residual conservatively to each arm yields
167.95712183100403s GATED and 155.69305844597983s wider MLP, both below 1800s;
complete pair including H/publication/readback/exit is below 3600s. Serial study
critical path and summed invocation wall are both 315.20s. Peak RSS 559,544 KiB
(546.4296875 MiB). Aggregate CPU and width/normalization-specific overhead remain
unmeasured; no performance-equivalence inference follows.

No scientific or execution-binding deviation was observed. Accepted P69 source
checks were reused with their original first-enclosing-wall measurement limit;
no repeat smoke was run. P70 is spent, terminal and technically accepted. DM is
next owner for all-outcome scientific intake and Root return.
