# UCOPE reactive renewal B01 — 8901 result evidence

**VALID / COMPLETE; original primary R−F WITHIN.** The one selected R/F/G instance and all four final panels completed. This is one matched training instance, not64 independent learned effects. Source: `831b83c15ec40939fc908a6aaac99f2a3b1a597a`; [frozen card](UCOPE_REACTIVE_RENEWAL_B01_CARD_20260913.md). DM collection acceptance:2026-09-14T03:29:54.465788Z.

## Rule and results

The card's primary is the mean of64 paired-world R−F differences at the final2048-episode endpoint. Its rule is: above+0.01J supports a bounded R-over-F signal; inside±0.01 shows no demonstrated margin at this scale, not equivalence; below−0.01 is adverse R-over-F package evidence. No other contrast rescues or replaces this primary. J is summed original team reward over256 ticks divided by256.

| Contrast | Mean difference J | Conditional world SE | Favorable / adverse / tied | ±0.01 reading |
| --- | ---: | ---: | ---: | --- |
| **R−F, primary** | **−0.0032978552991116817** | 0.007273884687935381 | 27 / 37 / 0 | **WITHIN** |
| R−G | −0.01806329032976254 | 0.009141773796144283 | 26 / 38 / 0 | DOWN |
| R−H | +0.055448365668267365 | 0.009138495293396914 | 51 / 13 / 0 | UP |
| F−H | +0.05874622096737905 | 0.008811008434780394 | 51 / 13 / 0 | UP |
| G−H | +0.0735116559980299 | 0.009645788424337796 | 54 / 10 / 0 | UP |
| F−G, descriptive | −0.014765435030650859 | 0.008208376779783744 | 24 / 40 / 0 | DOWN |

Final means are R0.19718366523949393, F0.20048152053860563, G0.2152469555692565 and H0.14173529957122658. Every contrast retains all64 differences in [SUMMARY.json](reactive_renewal_b01_8901/SUMMARY.json). The SE is sample SD of the paired-world differences divided by8; it is conditional on these fitted policies and cannot estimate training-population uncertainty. These local signs do not establish a stable ranking, equivalence, isolated termination/feedback causality, transfer, optimum or C claim.

The prospective event R−F>0.01 did not occur. DM probability0.35 gives Brier score0.1225; owner prediction **not taken (unattended)**. This is one scored event, not a calibration estimate.

## Integrity and exposure

The source was implemented by the DM and independently reviewed by Astra/high. A late-failure publication defect was corrected before execution; seven focused tests passed and the Reviewer confirmed its finding resolved. The accepted source keeps per-owner forced/eligible transitions, actual-command copying on KEEP, gate-before-fresh-velocity ordering, branch/conditional-velocity likelihoods, KEEP credit and full current-return/final-tick credit. F/G reuse their accepted code unchanged. Review evidence and the DM's response are in the [scientific review intake](pro_packets/20260913_reactive_renewal_convergence/INTAKE.md).

Collection recomputed the rule from the recorded episode rows and checked all episode IDs, world seeds, finite native rewards, reward_sum/256 identities, all1024 rollout IDs per fit and all four finite update records per rollout. All6144 training episodes and256 evaluations completed, with **1572864 training +65536 evaluation =1638400 native team steps**,3072 rollouts and12288 Adam calls. No interim panel, extra fit, retry, diagnostic frame or selected checkpoint was added. There were three constructors/constructor resets and6400 explicit scored episode resets. The no-error limits list is empty.

R's trainable parameters are68553; F/G have66311 each. Read-only final-checkpoint inspection confirmed metadata, all finite FP32 tensors and total parameter counts68553/68553/66311 for R/F/G (F includes its frozen2242 parameters), without constructing a model or environment. Common actor and critic parameters moved in all three fits. R gate displacement is0.6534708738327026; its final layer moved0.10117259621620178. F's frozen gate displacement is exactly0. All recorded parameter groups had zero evaluation displacement, and every training action generator remained unchanged by evaluation. These checks establish actual learning exposure and isolation, not successful causal use of feedback.

R selected1744115 training gates:870500 KEEP and873615 END, with6827 eligible final-tick credits. Evaluation selected54921 gates:26790 KEEP and28131 END, with225 eligible final-tick credits. Aggregate KEEP fractions are0.49910699695834276 in training and0.48779155514284156 in evaluation. Near-half aggregate frequency does not show that the gate ignored observations, nor explain the return comparison. No post-result gate diagnostic was run.

The existing scientific-tools run summary was applied once to final R/F/G means, one row per fit/master, using `--paired --baseline F`. [RUN_LEVEL_SUMMARY.json](reactive_renewal_b01_8901/RUN_LEVEL_SUMMARY.json) correctly reports n=1 and no sample SD for each training-level group. H is retained in native panel evidence and was not mislabelled as another trained unit. No episode rows or historical checkpoints were fed to that run-level tool as independent fits.

## Actual cost and observation

| Measured scope | Actual |
| --- | ---: |
| Complete Python runner, external `/usr/bin/time` wall | 1813.83s (30min13.83s) |
| Whole detached preflight/runner supervisor chain | 1814s |
| Complete runner CPU, user+system | 1811.91s |
| Internal summary wall / CPU | 1778.5461654390674s / 1810.762745969s |
| Peak RSS | 561872KiB =0.5358428955078125GiB |
| R arm / F arm / G plus H panel wall | 579.4346265790518s /655.7529266430065s /542.161346554989s |

The complete runner timing includes work outside the internal timer; neither is silently substituted for the other. One valid result consumed1813.83 measured runner seconds and1811.91 runner CPU seconds. This is not the complete direction cost: implementation, scientific review, Git/network recovery, monitoring, transfer, collection, publication and closeout have unmeasured support components. The initial source-preparation Git wait was observed at201 seconds before recovery; it created no scientific invocation. Focused check and independent counterexample timings remain in the technical intake. The45-minute plan and6000-second ordinary watchdog were not scientific endpoints or old-budget balances.

Supervisor `ucope-reactive-renewal-b01-8901` on `wsl_4070` exited0 at2026-09-14T03:13:24Z. Actual-node adjacent memory admission passed with14.558216094970703GiB available. The native Monitor initially adopted but repeatedly ended turns early; its record became stale and its yielded observer did not deliver completion promptly. DM reconciled the same handle at03:21:38Z, then the same Monitor directly returned `ucope-reactive-renewal-b01-8901-terminal-01`, finished/exit0/tmux inactive and empty active_set, and interrupted only its own observer session. This delivery delay changed no source, scientific exposure or result. Supervisor uptime after completion is not charged as continuing scientific execution. No new experiment or duplicate observer was launched during collection.

## Preserved evidence

All eight copied native files matched their independently read remote SHA256. [COLLECTION_FACTS.json](reactive_renewal_b01_8901/COLLECTION_FACTS.json) records the checks, selected numbers, costs and every archive member digest. [RUN_ARTIFACTS.tar.gz](reactive_renewal_b01_8901/RUN_ARTIFACTS.tar.gz) preserves native summary, complete episode/update rows, three final checkpoints, memory/time receipts, supervisor command/log/status and terminal Monitor record. It is2127560 bytes, SHA256 `9d7463ebfe12cd99df478fcb2ecd500ab2d2031733830f9f8f202d93917a7dda`; every member was reopened and hash-verified after archive creation. Scientific artifacts are distinct from the creator-owned policy-blocked test scratch.

The remote checkout/output and supervisor evidence remain available through committed preservation and Clerk handoff. The [DM intake](UCOPE_REACTIVE_RENEWAL_B01_8901_INTAKE_20260913.md) owns interpretation and the lifecycle decision; [Chinese owner brief](../../portfolio/owner/briefs/ucope/2026-09-13_reactive-renewal-b01-8901.md) records the same outcome.
