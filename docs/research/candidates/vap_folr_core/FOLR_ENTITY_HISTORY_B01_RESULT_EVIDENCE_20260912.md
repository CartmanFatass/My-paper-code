# FOLR entity-history B01 — E0 result

Status: BANK own-arm endpoint accepted; intended pair primary unavailable.
Card: [FOLR_ENTITY_HISTORY_B01_SCIENCE_CARD_20260912.md](FOLR_ENTITY_HISTORY_B01_SCIENCE_CARD_20260912.md).
The [machine summary](entity_history_b01_781201/RESULT_SUMMARY.json) and
[final intake](FOLR_ENTITY_HISTORY_B01_INTAKE_20260912.md) retain the distinction.

## Rule, exposure and observation

Apply the card verbatim: **strict >+1 BANK_ABOVE_MEI; inclusive [-1,+1]
WITHIN_MEI preserving sign; strict <-1 GENERIC_ABOVE_MEI.** The quantity is final
BANK mean native return minus Generic mean. Generic has no final panel, so the
quantity and rule are both null. No MEI branch, sign or equality is imputed. The
MEI is a contrast threshold, not a threshold for BANK's raw return.

| Observed quantity | Generic RETAIN | BANK |
| --- | ---: | ---: |
| Terminal | incomplete, exit124 | complete, exit0 |
| Complete training episodes / native ticks | 4253 / 85060 | 5000 / 100000 |
| Complete optimizer steps | 4221 | 4969 |
| Final evaluation episodes / native ticks | 0 / 0 | 128 / 2560 |
| Final native mean return | unavailable | -4.32609375 |
| Final episode SD | unavailable | 2.85473421805 |
| Conditional episode SE | unavailable | 0.252325240509 |
| Final episode minimum / maximum | unavailable | -12.53 / 1.51 |
| Enclosed invocation wall, seconds | 1795.06 | 1762.22 |
| Whole-process peak RSS, KiB | 761828 | 754692 |

The two allocated invocations produced9253 completed training episodes,
185060 training ticks,9190 completed updates and128 final episodes/2560 final
ticks. The grant remained5000/128 and4969 updates per arm; Generic's timeout
prefix was not a selected shorter experiment. Its4253 changing-policy training
returns cannot substitute for a final greedy panel. No Generic retry occurred.

BANK is one completed training instance, seed781201, with final evaluation seed
1781201. All5000 training and128 final returns are finite and preserved. Standard
library arithmetic over the final array reproduces the published panel at an
ordinary1e-9 return tolerance. The
[run-level input](entity_history_b01_781201/RUN_LEVEL.csv) contains exactly this
one fitted-policy endpoint; the existing scientific-tool
[summary](entity_history_b01_781201/RUN_LEVEL_SUMMARY.json) reports n=1 and null
training-run SD, with no paired differences. Evaluation episodes are not128
training seeds. No new rollout, learner, model, diagnostic or statistical search
was run during collection.

## Source, RNG, checkpoint and publication acceptance

Generic ran source `922a461fde867a8efe23a1563a969e6d2d08e258`; BANK ran
`5b3ae6b9847beba5fe72b0960ec7b66cb7d1c4b4`. The intervening correction only
allowed a collected incomplete Generic input and truthful own-arm publication;
model, learner, environment, reward, information, exposure and RNG paths were
unchanged. Independent actual-diff review and the focused publication regression
were accepted before BANK launch. Original numerical-path checks are reused.

Both arms reset the declared fresh Python/global NumPy/Torch streams, with
arm-specific constructors isolated from the common constructor stream; final
evaluation uses its declared fresh reset. The inherited native environment and
replay share NumPy; greedy/terminal action selection retains its native draws.
These are the inspected source and recorded execution settings, not a claim of
reconstructed random-state traces or episode coupling. BANK records NumPy1.26.3,
Torch2.7.0+cu118 on CPU FP32, Torch1/1. No checkpoint/episode/model selection ran.

The final BANK checkpoint identifies BANK and4969 updates. Actor, mixer and
both target state dictionaries are finite FP32; final online/target states
agree after the episode5000 target copy. All43 optimizer state entries are
finite and record4969 steps, with RMSprop lr.0005/alpha.99/eps.00001. The GRU
weights have shapes48x128 and48x16. Actor parameters total89573; its26 fixed
buffer values are the5x5 label table and attention scale. The runner reports
initial actor L2=20.8844668859 and displacement L2=30.4876254884, supporting
learner movement without proving a useful mechanism.

There were three read-only weights-only checkpoint loads: an initial collector
assertion incorrectly counted state buffers as parameters; one targeted read
and the declared buffer registrations identified the26-value difference; the
corrected final read completed verification. No checkpoint/source defect or
scientific retry followed. The [collection receipt](entity_history_b01_781201/BANK_COLLECTION.json)
records this correction, counts, state checks and exact archived member digests.
The published summary has complete own-arm status, intact native_panel,
`pair_primary: null` and an explicit incomplete-Generic explanation. Strict
complete-pair validation remains unchanged.

## Terminal receipts, resource limits and preservation

Root routed BANK's exact Monitor terminal: finished exit0, PID3413041, inactive
tmux, source5b3ae6b98, witness at `2026-09-13T08:56:10+08:00`, duration1762s.
DM read the same terminal supervisor bytes directly. Live primary experiment
tracking also records the Monitor goal completed. Thus the earlier pending
observation receipt is closed; technical/scientific acceptance is still this
DM's responsibility. BANK's own adjacent4GiB admission had passed before model
construction. Both native and supervisor originals are retained.

BANK's2994s TERM plus5s kill grace and1s margin enclosed admission, startup,
learning, checkpoint, final evaluation, publication/readback and child exit
under its3000s ceiling. Actual time1762.22s includes runner1761.6770697s;
its own final time-record write tail is outside that enclosed timing. The
supervisor's coarse full duration1762s is consistent. Generic's1800s cap
terminated its partial attempt; no outside-cap continuation occurred.

Enclosed native wall sums to3557.28s, below4800s; aggregate native CPU is
3556.57s. This is actual spend for both assigned arms, including the incomplete
Generic. It is not a same-endpoint runtime superiority claim. Known support
through archival/analysis is104.5563982s plus a separately observed97s lower
bound for the earlier failed Git retrieval, so support is at least201.5563982s
and native plus observed support at least3758.8363982s. These are lower bounds,
not complete costs. Unitemized support, final publication/integration/cleanup,
and timing tails remain unknown; provider/agent all-in costs are also unknown.
The hard support1200s and complete6000s ceilings remain binding. No breach is
observed, but full support/complete conformance is unverified
(`resources_unmeasured` for those uncovered components). See
[SUPPORT.json](entity_history_b01_781201/SUPPORT.json). No section4 additions or
new section5 source/test-budget breach occurred; no profiler or replay was added.

The [BANK raw archive](entity_history_b01_781201/BANK_RAW.tar.gz) is4149375 bytes,
SHA256 `f4d2726f98ae2b05157fd3b06b5cfc2f9c3c8c4fa0cc891bb41874f0c2b1595b`;
it preserves summary, final checkpoint, admission and invocation time. The
[supervisor archive](entity_history_b01_781201/BANK_SUPERVISOR.tar.gz) is1766
bytes, SHA256 `888c165c9c05ab8caa0c50a87a8f8bf104270b69c6a64e1280d33295e84da3e1`.
The remote creator compared every archived member with original bytes; DM then
verified both local archives and all member hashes. Generic's already preserved
raw/supervisor archives and incomplete intake remain unchanged. The collection
receipt lists the one terminal detached checkout, both output roots, support
root and two terminal supervisor roots for reclamation after Root accepts
integration/retention. No deletion has occurred at this boundary.
