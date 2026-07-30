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

## ESCALATION -- the clean localization needs a workflow file change

Recorded rather than worked around, because workflow-file pushes are user-gated on
this line.

`d7_s_world_digest_probe.py` produces exactly what step 1 needs, in seconds, and
records the runner identity that makes a comparison interpretable. **No existing
workflow job invokes it.** The jobs that do exist give:

| job | what it gives | why it is not enough |
|---|---|---|
| `audit` | R4 population, component digests | 114 min, 8 shards, and it is the formal run |
| `workers` | dev topology 20260725 only, component digests, ~1 h | wrong topologies -- the divergence is known on 3 of 8 R4 seeds, and 20260725 may simply be stable |
| `benchmark` | a step-rate number | no world digests at all |

So the accessible route is the `workers` job on the **development** topology, and
its answer is asymmetric:

- if two runs' digests DIFFER, the array is localized and that is decisive;
- if they AGREE, it means nothing -- either the generator is stable for that
  topology, or both runs landed on similar hardware, and the job prints `nproc`
  but no CPU model so the two cannot be distinguished.

**What would make step 1 cheap and conclusive:** one workflow job that runs
`python scripts/d7_s_world_digest_probe.py --episodes 2 --out probe.json` on
`ubuntu-latest` and uploads `probe.json`. Seconds of compute, the R4 topologies
where the divergence actually lives, and runner identity recorded in the artifact.
Run it twice and diff with `d7_s_world_component_digest_diff.py`.

Until then: `d7s-workers-2` (`30516912923`) and `d7s-workers-3` (`30518707693`)
were launched **concurrently**, since two simultaneous runs cannot share a runner.
Different runners do not guarantee different CPU models, so an agreement between
them remains uninformative -- which is the whole reason this escalation is written
down instead of being treated as a result.

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

## THIRD SAMPLE, 2026-07-30: a tiebreaker, and the fleet is homogeneous today

Two concurrent `benchmark` runs (`30530239912`, `30530245806`) at the corrected
identity, carrying the R4 digest block: 32 R4 episode keys each, component digests
and runtime identity.

```text
both runners        AMD EPYC 7763 64-Core Processor
detected features   identical, no difference in either direction
agreement           32 of 32 keys, all nine arrays

WORLD_CONFORMANCE_UNTESTED   (exit 1)
```

`UNTESTED` is the correct verdict and the gate is right to give it: **the two runs
landed on the same CPU model**, so their agreement says nothing about
cross-machine behaviour. What is new is that we can now SEE that, rather than
guessing -- `cpu_model` and numpy's runtime-detected feature set are recorded.

**The GitHub-hosted fleet looks homogeneous.** Two concurrent runs, guaranteed
different runners, both EPYC 7763 with identical feature detection. Repeated
tagging may therefore never produce two different CPU models, which means the
CPU-dispatch hypothesis may not be testable on this vehicle at all.

### The tiebreaker, which is the useful part

Today's fingerprints against both historical runs, same R4 keys:

```text
                          now == H     now == re-run     H == re-run
overall (32 keys)            29             24              21
20260736  (4 keys)          True          False           False
20260740  (4 keys)          True          False           False
20260739  (3 keys)         False           True           False
```

**Neither historical run is simply "the broken one."** On 20260736 and 20260740 the
re-run is the outlier; on 20260739 H is. A third independent sample agrees with
whichever run is not the outlier, in every case.

That rules out a story where one run was corrupted and the other was correct, and
it is not what a per-run random perturbation would look like either -- today's two
runs agree with each other on 32 of 32, so the generator is not simply unstable
from run to run.

### What it does NOT establish

The cause. Neither H nor the re-run recorded its hardware -- `runtime_identity` is
newer than both -- so it cannot be tested whether their outlier episodes correlate
with the CPU they ran on. That evidence is unrecoverable for those two artifacts.

The glibc-ifunc prediction remains **untested**, not refuted: today's pair could not
test it, because they shared a CPU model.

Pro's Challenge 6 continues to bind.

### What changed for the better

Every artifact this repository produces from now on carries the runtime that made
it. The next disagreement is interpretable at the moment it appears, rather than
requiring three samples and a tiebreaker to partially localize. That is the durable
outcome of this stretch, and it is worth more than the verdict.
