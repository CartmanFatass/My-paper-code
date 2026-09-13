# MGTAP unequal-exposure B01 — master8231 E0

**Complete valid B/EXPLORE: COND_ADVERSE.** Mean-COND512 mean J is
0.16574499572521276; intact-DENSE768 is 0.19507936796417658. The complete
COND−DENSE difference is **−0.02933437223896382 J**, below the card's −.01 MEI.
DENSE remains default. This is one realized unequal-exposure procedure comparison.

## Rule, source and native result

The [card](MGTAP_UNEQUAL_EXPOSURE_B01_SCIENCE_CARD_20260913.md) rule applied verbatim:
**“Delta < −.01: adverse for this exact procedure choice.”** Both fits and all32
final worlds completed, so the incomplete/damaged branch does not apply.

The sole remote handle `mgtap-unequal-8231-ecf40e0ad` ran source
`ecf40e0ade4576fd75ffb0eab09425cb5c4ce059`, from the published command at
`1df130fca9a04ea0ede066f7e8f05620153db004`. The summary's `launch_sha` matches;
`source_sha=a9fbfddcfd8e0e714f6fe33b15c3d971fa95fd85` is recorded dependency
provenance. No alternate master, second invocation, model smoke or retry ran.

| Quantity | COND512 | DENSE768 | Pair |
| --- | ---: | ---: | ---: |
| Training episodes / native ticks |512 /131072|768 /196608|1280 /327680|
| Rollouts / Adam calls |256 /1024|384 /1536|640 /2560|
| Final episodes / ticks |32 /8192|32 /8192|64 /16384|
| Mean final J |0.16574499572521276|0.19507936796417658|−0.02933437223896382|
| Complete arm wall, seconds |193.6281692145858|238.67183078541422|432.30|

All32 differences are in [PAIRED_FINAL_SCORES.csv](unequal_exposure_b01_8231_20260913/PAIRED_FINAL_SCORES.csv).
Conditional SD0.05575806609540997, SE0.009856726660478026; 7 positive/25 adverse/0zero,
range−0.16262802975541926 to+0.10135544415656023. The evaluation worlds condition on
one trained pair; training-population uncertainty is not estimated.

## Technical checks and cost

[INTAKE_ANALYSIS.json](unequal_exposure_b01_8231_20260913/INTAKE_ANALYSIS.json) records
the byte-level collection and read-only analysis. All1344 episode rows equal the closed
summary and satisfy J=reward_sum/256; all640 rollout records contain the intended four
finite optimizer epochs. Master, private stream/reset addresses, complete ordered panels,
per-arm counts and complete primary agree. The accepted pure reducer, extracted without
scientific imports, exactly reproduces the published primary. Binding errors/limits are
empty. Both checkpoint ZIP CRCs pass without deserialization. All recorded actor, critic,
encoder, recurrence and branch groups have nonzero movement; projection displacement is
0.6599485278129578/0.6607306599617004. This proves learning exposure, not causality.

There are344064 native ticks,1720320 velocity decisions,8273920 actor collection/evaluation/
replay rows, no duration decisions/diagnostic frames/partial steps, one common pair factory
and six top-level model constructions. CPU FP32/thread1 and the actual learner remain intact.

Supervisor terminal is finished/exit0 at09:41:01 UTC, rounded duration433s, tmux inactive.
GNU time gives432.30s wall,425.74s user+4.96s system CPU and559924KiB peak RSS.
Fresh adjacent admission at09:33:49 UTC passed with15624224768 bytes effective availability.
COND includes startup/admission/shared construction; DENSE includes the entire16.380363709363166s
tail after the last Python clock through outer exit. Native600/900/1500s caps all pass.
Support900s and complete2400s remain in scope but **compliance is UNKNOWN** because author,
provider, coordination and integration tails are unmeasured; partial clocks are not a complete bill.
Separate ACPS selector repair and earlier Transport redesign are separate assignments.
No observed scientific-integrity or Engineering Scope§5 breach was found.

## Retained evidence and boundary

[NATIVE_EVIDENCE.zip](unequal_exposure_b01_8231_20260913/NATIVE_EVIDENCE.zip) preserves all
seven native files, six supervisor files and the read-only analysis script:1135296bytes,
SHA256 `2e9be88fd64c7825c5bfda5388be75f03444e68dc3add41b36ba9ce19c6253a1`.
All seven native hashes match the remote originals and all archive members pass hash readback;
the manifest is [COLLECTION.json](unequal_exposure_b01_8231_20260913/COLLECTION.json).
No unique evidence has been removed. [DM intake](MGTAP_UNEQUAL_EXPOSURE_B01_INTAKE_20260913.md)
states the bounded reading and next dependency. The empirical allocation ends with this pair;
MGTAP remains ACTIVE/MEDIUM and occupied. No automatic successor follows.
