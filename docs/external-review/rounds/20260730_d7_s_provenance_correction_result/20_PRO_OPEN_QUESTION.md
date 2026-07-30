# D7.S — the provenance correction you ordered: steps 1–4 done, and step 1 may not be answerable on this vehicle

Your ruling scheduled five steps and said the next artifact should be an
episode-world provenance correction and root-cause localization, not another R4
result run. Steps 1–4 are implemented and measured. This is the result submission.

**The honest headline: step 1 localized the array across a PLATFORM boundary and
could not test the cloud-versus-cloud case, because the GitHub fleet appears
homogeneous.** That may not be fixable by running more samples, which is why it
comes to you rather than being retried indefinitely.

Every measured claim is offered to be falsified. Discarding this question's framing
is a legitimate answer, including the recommendation in §5.

## 0. Provenance and confidence

`[REPO]` verifiable at `stage_commit`. `[MEASURED]` I ran it; invocation given.
`[MY INFERENCE]` mine, attack first.

**Verified by reading source:** the writers of all nine world arrays; the IEEE-754
status of each operation they use; `fork_continuation`'s virtual REJOIN (your
Challenge 1, which I checked before accepting).

**Verified only by tests:** the manifest module's behaviour, and the conformance
gate's three outcomes. Neither is wired into the audit path.

## 1. Frozen inputs — not review surface

- Your 2026-07-30 ruling in full, including that H and the re-run keep
  `INVALID_R4_REALIZATION` and carry no confirmatory weight.
- `MATERIALITY_MARGIN = 5.0`, `DELTA = 10`, `H_STABLE = 139`, `H_FLEX = 550`,
  `T_E_MAX = 950`. No threshold moves.
- The frozen R4 population. Not re-selected, and no new population is proposed.
- Every historical artifact stays immutable.

## 2. `[MEASURED]` Step 1 — localized across a platform boundary, untested across the fleet

Instrument: per-array `component_digests`, added to `episode_world_fingerprint`
with the combined fingerprint proven byte-unchanged (golden digest + a real R4 env).

**Local (Windows/MSVC/AMD Zen) against cloud (Linux/glibc/EPYC), 6 shared keys:**

```text
first differing component   user_velocities            5 keys
                            user_cluster_assignments   1 key
user_positions              BIT-IDENTICAL on all 6
```

**Cloud against cloud, two concurrent runs, 32 R4 keys, corrected identity:**

```text
both runners        AMD EPYC 7763 64-Core Processor, identical detected features
agreement           32 of 32 keys, all nine arrays
verdict             WORLD_CONFORMANCE_UNTESTED
```

`UNTESTED` because the two runs shared a CPU model, so agreement establishes
nothing about cross-machine behaviour. Two concurrent runs are guaranteed
different runners but not different hardware.

**`[MY INFERENCE]`, and the load-bearing one: the fleet may be homogeneous, so this
may be untestable here.** Two concurrent runs landed on the same model. If that is
the norm, no amount of re-tagging produces the comparison step 1 wants.

### `[MEASURED]` A tiebreaker that changes the picture

Today's fingerprints against both historical runs, same R4 keys:

```text
                     now == H   now == re-run   H == re-run
overall (32 keys)       29           24             21
20260736 (4 keys)      True        False          False
20260740 (4 keys)      True        False          False
20260739 (3 keys)     False         True          False
```

**Neither historical run is simply the broken one.** On two topologies the re-run
is the outlier; on the third H is. A third independent sample agrees with whichever
run is not the outlier, every time. And today's two runs agree with each other on
32 of 32, so this is not per-run instability either.

`[REPO]` Neither H nor the re-run recorded its hardware — `runtime_identity` is
newer than both — so whether their outlier episodes correlate with CPU is
**unrecoverable for those two artifacts.**

## 3. `[MEASURED]` Step 2 — exactly one non-portable operation

Audited every writer of the nine arrays on the configured path
(`forced_relay_cluster`, `rpgm`):

| writer | random source | non-portable operation |
|---|---|---|
| `_generate_forced_relay_cluster_positions` | `uniform`, `multivariate_normal` | none (`**2`, SVD) |
| `_init_user_velocities` | `uniform` x2 | **`np.cos`, `np.sin`** |
| `_initialize_user_waypoints_rpgm` | `random`, `uniform` | `linalg.norm` -> `sqrt` |

**IEEE 754 requires `sqrt` to be correctly rounded. It does not require `sin` or
`cos`.** That is the only operation on this path whose result may legitimately
differ between conforming implementations, and it is precisely the array that
diverged. The RNG stream is provably shared — identical `user_positions` require
identical draws.

`[MY INFERENCE]` This kills my own pre-registered hypothesis, which said
`user_positions` would diverge via `multivariate_normal` -> SVD -> OpenBLAS
`DYNAMIC_ARCH` kernel dispatch. Positions are bit-identical; LAPACK is portable
here. I record it as dead rather than letting it disappear.

## 4. `[REPO]` Steps 3 and 4 — implemented, deliberately not wired

**Step 3, manifest replay (`scripts/d7_s_world_manifest.py`).** Capture, save,
load-and-verify, apply-with-read-back. The digest gate's paired negative perturbs by
**one ULP**, because a last-bit difference is the actual failure mode and a gate
tuned to gross corruption would pass it. `apply` verifies before AND after
assignment, since a property or dtype coercion could leave the env in a different
world while the manifest still verifies.

**Not wired into the audit path, and a test enforces that** until step 4's gate has
real inputs. A manifest mechanism never checked across two machines would relocate
the unverified assumption rather than remove it.

**Step 4, the conformance gate (`scripts/d7_s_world_conformance_gate.py`).** Three
outcomes, not two: `PASS` requires agreement AND runtimes some recorded field proves
distinct; `FAIL` on divergence, decisive whatever the hardware; `UNTESTED` otherwise,
exiting non-zero. A two-outcome gate would report PASS most confidently exactly when
it had tested nothing.

`[REPO]` Every artifact now records `runtime_identity` — CPU model from
`/proc/cpuinfo`, numpy's runtime-detected `__cpu_features__`, the BLAS
configuration string. The first version recorded only compile-time CPU lists and a
Linux `processor` field that is always `"x86_64"`, and would have produced a third
meaningless `UNTESTED`.

## 5. THE DECISIONS

**5a. Does step 1 have to succeed before the repair proceeds?** Your §6.1 ordered
localization first and Challenge 6 forbids freezing a cause before the digest
comparison names the surface. Step 1 named it across a platform boundary
(`user_velocities`, scalar trig) but could not test the cloud case, possibly for
structural reasons. Is the platform-boundary localization sufficient to proceed to
the repair, or must the cloud-versus-cloud comparison be obtained first — and if so,
on what vehicle, given this one may not offer two CPU models?

**5b. Route A or Route B, now that the mechanism is scalar trig?** Route A
(manifest replay) never re-executes the trig, so portability stops mattering. Route
B (deterministic generator) requires removing or pinning `sin`/`cos`, and **every
way of doing that changes the values drawn** — a portable direction draw, a pinned
libm, or rounding — which invalidates every world any existing artifact recorded.
That makes Route B a change to the registered draw rather than a refactor. I
recommend Route A and record that as my recommendation, not a decision.

**5c. Step 5 — may fresh confirmatory evidence be designed now?** Your §6.5 says any
new formal claim requires a fresh untouched population under the repaired contract,
and that no such population is selected by that ruling. Does the population
selection wait for a passing cross-machine gate, or may it be pre-registered now
against the repaired contract?

**5d. Is manifest replay acceptable to wire in, on the evidence above?** It is
implemented and tested but has never been exercised across two machines, because
the gate that would prove it cannot currently be satisfied.

## 6. What I have not done

- Not wired the manifest into the audit path.
- Not selected or pre-registered any population.
- Not changed a threshold, the contract, or any historical artifact.
- Not touched `sin`/`cos` — that would change the registered draw.
- Not re-run the R4 audit.

## 7. Required response sections

1. **5a** — is the platform-boundary localization sufficient, and if not, what
   vehicle.
2. **5b** — Route A or Route B, and anything wrong with the trig finding.
3. **5c** — whether step 5 may begin, and under what selection rule.
4. **5d** — wire it in, or hold.
5. Anything in §2 or §3 you judge false. The claim I most want attacked is that
   scalar trig is the ONLY non-portable operation on this path, because §3 and the
   Route A recommendation both rest on it.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260730_d7_s_r4_rerun_disposition/21_PRO_OPEN_RAW.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260730_STEP2_USER_VELOCITIES_WRITERS.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260730_WORLD_DIVERGENCE_SCOPE.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260730_WORLD_DIVERGENCE_PREREGISTERED_PREDICTION.md`
- `docs/research/designs/D7_S_WORLD_MANIFEST_REPLAY.md`
- `scripts/d7_s_world_manifest.py`
- `scripts/d7_s_world_conformance_gate.py`
- `scripts/audit_d7_s_event_aligned.py`
- `envs/pettingzoo/scenario_base.py`
