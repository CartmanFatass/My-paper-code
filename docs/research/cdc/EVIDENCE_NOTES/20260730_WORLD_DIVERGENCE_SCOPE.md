# The scope of the world divergence, and why local cannot be the baseline

Date: 2026-07-30
Instrument: `scripts/d7_s_world_digest_probe.py` (construction only, seconds per
episode), validated against an independent local computation -- it reproduces
`fe21b9e3...` for 20260734/calibration/0 and `d700a69e...` for 20260736/calibration/0
exactly.

## Measured

32 episode keys: the frozen R4 population, both blocks, episodes 0 and 1.
Fingerprints compared three ways.

```text
local  == H        (run 30403322062)      0 of 32
local  == re-run   (run 30479940700)      0 of 32
H      == re-run                         21 of 32
```

The 11 disagreeing cloud-vs-cloud keys are all of 20260736 and 20260740, plus three
of four on 20260739 -- the same three topologies the pooled artifacts disagreed on.

## Two different findings, and they must not be merged

**1. Cloud vs cloud is the CLEAN signal, and it is 3 of 8 topologies.** Same OS,
same `requirements_d7s_audit.txt`, same `numpy==1.26.3` / `scipy==1.15.2`, same
python 3.10, same workflow, same invocation. Something unpinned varies between two
`ubuntu-latest` runners. This is the divergence the ruling calls a claim-blocking
population-provenance failure, and it is the one worth localizing.

**2. Local vs cloud is 32 of 32, and it is CONFOUNDED.** The local interpreter is
Windows on AMD Zen (`Family 25 Model 117`, `AuthenticAMD`) with an MSVC-built
`openblas64 0.3.23.dev`; the runners are Linux on Intel or AMD EPYC with a
different wheel build. OS, compiler, CPU vendor and BLAS build all differ at once.

**A 100% disagreement across that boundary is expected and diagnoses nothing.** It
does not isolate CPU kernel dispatch, it does not confirm the pre-registered
prediction, and it must not be quoted as evidence for any specific cause. Recording
it because the number is striking is exactly how a confounded comparison becomes a
cited result.

## What this changes about step 1

**The plan was wrong.** I intended to localize the first differing world array by
comparing a local probe against a cloud run. That cannot work: local differs from
both cloud runs on every key, so the comparison would report a divergence on all 32
and name a first-differing array for the *platform* difference, not for the
cloud-vs-cloud difference the ruling is about.

Localizing the clean signal needs **two cloud samples carrying
`component_digests`**, from runs that landed on different runners. Neither existing
artifact has the field, and the `workers` job runs both its arms on one runner --
that job proves cross-process determinism, which is a different property.

Revised step 1: obtain two independent cloud samples with component digests and
diff those. `d7s-workers-2` (run `30516912923`) is the first. A second run is
needed, and whether two runs land on different runner hardware is not controllable
from here -- so a clean localization may take several attempts, and each attempt's
runner identity has to be recorded to know whether the comparison tested anything.

`d7_s_world_digest_probe.py` records `platform`, `machine`, `processor`, the
`openblas configuration` string and the CPU dispatch feature list for exactly this
reason. Without the runner identity, two agreeing samples are indistinguishable
from two samples that ran on the same hardware.

## What is not yet established

- Which world array diverges first. Unchanged: not localized.
- That CPU kernel dispatch is the cause. The pre-registered prediction
  (`20260730_WORLD_DIVERGENCE_PREREGISTERED_PREDICTION.md`) is untested -- the only
  comparison run so far is the confounded one, which cannot test it.
- Pro's Challenge 6 still binds: do not freeze "machine-dependent construction
  state" as the causal conclusion until a comparison names the first differing
  surface.

## What it does strengthen

The ruling's classification. `seed_controls_generation = True` was reported for
128/128 episodes in both runs, and for every one of these 32 keys the registered
tuple -- contract namespace, topology hash, block, episode index, `user_world_seed`
-- fails to determine the world across a machine boundary. That is a
population-identity failure rather than final-digit numerical drift, which is what
the ruling said and what the manifest-replay repair addresses regardless of cause.
