# CADC-B01 result — complete adverse paired observation

Evidence class B/EXPLORE; original DM `/root/dm_cadc_start`; master9302; exact native source `22e009c9387f2507aab6ebab4555d92e27f5070e`. The [frozen card](CADC_B01_CARD.md) was applied unchanged to both preselected arms and every final episode. No scientific rerun or additional evaluation was used for collection.

## Primary and co-reported outcomes

| Final episode average | LEARNED | RR | LEARNED−RR |
| --- | ---: | ---: | ---: |
| Net native service J_net | 0.174522977659 | 0.187877898960 | −0.013354921301 |
| Original physical service J | 0.176778714963 | 0.188877898960 | −0.012099183996 |
| Communication charge/H | 0.002255737305 | 0.001000000000 | +0.001255737305 |

The exact reading rule is: **“Mean >0.01 reads ABOVE_MEI; [-0.01,+0.01] reads INSIDE_MEI with its sign; mean <-0.01 reads ADVERSE.”** The complete primary is **ADVERSE**. These are the card's descriptive branches, not significance or equivalence tests.

All32 final paired net differences are retained in [ANALYSIS.json](evidence/cadc_b01_9302/ANALYSIS.json): 10 positive,22 adverse, conditional SD0.044207147585 and SE0.007814793458. They describe final-world variability conditional on this one learned training pair. The independent training unit is one matched master9302 pair, not32 independently trained replicates. [Run summary](evidence/cadc_b01_9302/RUN_SUMMARY.json) therefore reports n=1 and no training-run SD or confidence interval. Individual positive worlds remain contrary evidence to a uniform-loss claim.

| Final communication totals over32 episodes | LEARNED | RR |
| --- | ---: | ---: |
| Eligible attempts, including collisions | 18,479 | 8,192 |
| Collided attempts | 16,744 | 0 |
| Accepted packets | 1,735 | 8,192 |
| Delivered packets | 1,715 | 8,110 |
| Terminal pending packets | 20 | 82 |

These endogenous communication counts describe the tested complete packages. They do not identify collision, stale information, motion co-adaptation or credit assignment as the causal source of the return difference. Net harm includes both lower physical service and greater communication charge; removing the charge in the reported arithmetic does not produce a physical-service gain.

## Complete actual exposure and cost

Both arms:512 train episodes,32 sole-final episodes,256 two-episode rollouts,1,024 Adam calls,131,072 train and8,192 final team ticks,544 explicit resets and one environment constructor. Pair total:278,528 team ticks and2,048 Adam calls. Evaluation optimizer calls are zero. The LEARNED send head moved0.044393774122 in Euclidean norm from its zero initialization; total actor movement is2.222118616 versus RR2.659447908. Both critic and actor parameters moved and every retained checkpoint tensor is finite FP32. This establishes real exposure, not adequacy or convergence of send learning.

GNU time enclosing adjacent admission, imports, native training/final evaluation, publication and child exit measured LEARNED195.00s and RR180.34s; sum375.34s. Supervisor logs additionally span195s and180s at integer-second precision and show exit0/COMPLETE; Root reported both tmux sessions inactive. Each measured arm is below600s and the measured native sum below1,200s. Peak RSS is555,392KiB and554,288KiB. Final outer wrapper tails are not separately resolved; support and2,100s complete-grant compliance are not certified because support coverage is partial. See [support accounting](execution/SUPPORT.json); native savings do not transfer to the hard900s support allocation.

## Retained evidence

- [CADC_RESULTS.tar.gz](evidence/cadc_b01_9302/CADC_RESULTS.tar.gz), 1,117,622 bytes, SHA256 `f3804156ab239fa177b5773743e2508bd7f3c6453f7c52c005185ce1f529c41a`: both summaries, complete episode/update streams and final actor/critic checkpoints,8 files. Per-member lengths/digests are in ANALYSIS.json.
- [CADC_SUPERVISORS.tar.gz](evidence/cadc_b01_9302/CADC_SUPERVISORS.tar.gz), SHA256 `555ea01968abd87e514ad1fd73132a28f3e11cacdbe4864bd299a302b5cd3852`: both exact supervisor runners, terminal status/exit/PID/start facts and logs.
- [Terminal collection](evidence/cadc_b01_9302/TERMINAL_COLLECTION.json), wall/log sidecars, [launch](execution/LAUNCH_RECEIPT.json), [memory admissions](execution/LEARNED_MEMORY.json), [RR admission](execution/RR_MEMORY.json), [actual Monitor adoption](execution/MONITOR_ADOPTION.json) and staged-command/source evidence.
- [Complete scientific and technical intake](CADC_B01_INTAKE.md), [Chinese owner brief](../../portfolio/owner/briefs/contention_aware_decentralized_communication/2026-09-12_CADC_B01.md).

Claim ceiling: this finite learned-send-plus-motion package was adverse to this same-information learned-motion RR comparator on one matched native training history. This is neither stable inferiority of learned communication, a mechanism diagnosis, a general radio result, nor a direction/Portfolio disposition.
