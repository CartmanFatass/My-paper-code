# ACPS-B01 result evidence — E0

**Complete B/EXPLORE: ADVERSE on the sole master9101.** All32 final ACPS−SHARED differences average **−.03680814181453545 J**, conditional sample SD.06442303836564946 and SE.011388491823247962;7 positive/25 adverse worlds. No independent training-population uncertainty is available from one matched pair.

## Card, rule and exact executions

Frozen [science card](ACPS_B01_SCIENCE_CARD_20260912.md), selected Portfolio response`b793cf69b4935306708ad744b355acc4d5b33712`§3/10, source`2302072e2dcb7aa0c4ee2f71572ef8ca67cd9a46`, fixed commands`43e020856`. Both whole-arm runs used CPU FP32/thread1, common118 information and the declared physical heterogeneous-actuation law. No source or scientific configuration changed between arms.

Rule applied verbatim: **Strict mean>.01 is a local above-MEI package signal; inclusive[−.01,+.01] retains sign without equivalence; strict mean<−.01 is adverse. A damaged dependent primary has no comparative polarity.** The complete mean is below−.01, so ADVERSE; this is not a significance test.

| Quantity | SHARED | ACPS |
| --- | --- | --- |
| Accepted handle | acps-b01-shared-9101-20260912 | acps-b01-acps-9101-20260912 |
| Terminal | exit0 / COMPLETE | exit0 / COMPLETE |
| Train episodes / final episodes | 512 /32 | 512 /32 |
| Train ticks / final ticks | 131072 /8192 | 131072 /8192 |
| Two-episode rollouts / Adam calls | 256 /1024 | 256 /1024 |
| Final mean native J | .14885927425137008 | .11205113243683462 |
| Actor / critic parameter counts | 35702 /34177 | 37042 /34177 |
| Total parameter displacement / initial norm | 6.1293120 /15.5982218 | 6.2964859 /15.8069782 |
| Whole process wall, seconds | 165.05 | 195.99 |
| Partial internal wall, seconds | 164.5965068 | 195.6315034 |

Complete native sum **361.04s**, each whole arm below450 and sum below900. Final checkpoint evaluation performed zero optimizer updates; no model was created for evaluation. Four top-level scientific actor/critic objects were constructed across the two separate processes. The treatment's A moved from zero to norm.1845420 and B moved.8552084 from initial norm2.5604794; nonzero movement is not proof of competent convergence or benefit. Actor row uses remain6,635,520 pair total, not independent samples.

## Direct checks and receipts

[SHARED_COLLECTION.json](acps_b01_execution/SHARED_COLLECTION.json) and [ACPS_COLLECTION.json](acps_b01_execution/ACPS_COLLECTION.json) record actual ordered counts, finite rows, source/arm/master, explicit512/32 episode identities,4 epochs per rollout, checkpoint deserialization and parameter finiteness. Both raw JSONL streams match their published summary rows; all paired reset seeds and capability assignments match. [PAIR_RESULT.json](acps_b01_execution/PAIR_RESULT.json) preserves every absolute and signed contrast, including all25 adverse worlds. Training curves and weak checkpoints remain in the raw archive.

Fresh memory admission passed separately inside each timed payload:15,632,183,296 bytes SHARED and15,613,870,080 bytes ACPS physical/effective availability. Monitor actually adopted both handles with unfinished goals, and Root forwarded both terminal facts. SHARED's goal completed empty at its earlier boundary. At ACPS terminal, the shared Monitor goal remained active for unrelated MGTAP work; ACPS terminal delivery itself was accepted. No claim of globally empty Monitor state is made.

The protected density is the sampled pre-tanh proposal, while normalized sent commands stay in history and capabilities alter physical motion only. Independent reviewed source and focused checks support that boundary; this is technical conformance, not a causal ablation. Source review found no material defect, seven focused cases passed. No scientific retry, omitted adverse arm, checkpoint selection or extra panel occurred.

## Evidence preservation and cost limitations

[ACPS_B01_9101_RAW.tar.gz](acps_b01_execution/ACPS_B01_9101_RAW.tar.gz),1,034,735 bytes, SHA256`206b40250cc5cff6e57c4512b31a75783e1a81624c13f4b8adaade9c74b716e9`, contains all14 collected files: per arm admission, episodes, rollouts, final checkpoint, summary, process-wall receipt and supervisor log. [RETENTION.json](acps_b01_execution/RETENTION.json) and [remote readback](acps_b01_execution/REMOTE_SHA256.txt) verify every remote byte digest equals the local file and archive member. This retention check authorizes no new runtime predicate or evidence deletion.

[ACPS_B01_SUPERVISOR.tar.gz](acps_b01_execution/ACPS_B01_SUPERVISOR.tar.gz) separately preserves both complete terminal supervisor roots (12 files, including runner, exit code, status, start time, PID and the already retained logs). Its 1,718 bytes hash to `cf3edc14c2f9ebc8687bd66ce819a75e4bdb87f40bf04ffd4a18c114665db6d9`; [SUPERVISOR_RETENTION.json](acps_b01_execution/SUPERVISOR_RETENTION.json) records every remote/readback digest. Both retained statuses are `finished` with exit code 0.

Native wall includes enclosed admission/imports/construction/training/eval/checkpoint/publication/readback and actual exit. Support includes the3m11s observed failed partial-clone fetch/staging interval, repaired configured-login-shell staging, local checks/review, Git/collection/reduction/intake/preservation/cleanup. Some exact call walls are recorded in execution; original fetch completion and other support/agent/Root tails remain unknown. Shared Portfolio-discovery/application overhead is assigned once to ACPS as unknown, not charged again to T/CADC. Thus **full support/complete-work coverage is unmeasured**; native compliance does not certify support≤900 or total≤1800, and missing coverage does not demonstrate an unobserved breach. No allocation is increased or borrowed.

Test scratch removal was explicitly runtime-rejected; preserved scratch is a technical closeout limitation. All scientific raw files are retained and the four exact remote cleanup targets require Root integration/retention confirmation before reclamation. Shared authoring and any active sibling work remain intact.
