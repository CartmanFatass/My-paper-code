# VNFC R02 result evidence — `B0-DEBUG` attempts 01 and 02 (2026-09-03)

Executed 2026-09-03 by Claude Code (Fable 5.1) under the owner-approved section 11 recast recorded
in `VNFC_SECTION11_RECAST_INTAKE_20260903.md`.

**Question.** On the exact two-zone, one-unannounced-executor-loss simulator, does a
presentation-safe shared `MAPR-4` policy learn post-loss recovery from unshaped external return at
training rosters `N = {3, 5}` under 64 updates, and show preliminary failed-zone recovery direction
on untouched `N = 7` worlds, separately against the strictly containing same-information
`DIRECT-SET-AR` learner and the competent fixed `BCRH-PERSIST` controller?

**Claim ceiling: `B/EXPLORE`.**

**Outcome: no B result. The object `VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02` is not consumed.**
Two `B0-DEBUG` attempts were launched and both were mechanically quarantined as `INCOMPLETE` before
any held-out `N = 7` endpoint was opened. No return, recovery, comparator or polarity observation
exists and none is claimed. The three 64-update `PRIMARY` seeds were **not** launched: the runner's
`PRIMARY` path requires an archived, sealed `DEBUG` three-artifact bundle, and no such bundle
exists. Everything below is a direct observation, including the two quarantines.

| Fact | Value |
| --- | --- |
| Study family | `VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02` (`B/EXPLORE`) |
| Presentation law executed | `VNFC-R02-ORC-CANONICAL-OPAQUE-RANK-SORT-V1` — canonical opaque-rank sort before the first tensor operation, null last |
| Recast intake | `VNFC_SECTION11_RECAST_INTAKE_20260903.md` (owner decisions 4, 6, 7) |
| Attempt 01 launch sha | `a8305f645` — "Install the resolved load-only native binding in the VNFC R02 runner" |
| Attempt 02 launch sha | `a2efdc6a4` — "Bind the held-out freeze token to serializable gate material in the R02 runner" |
| Working-tree cleanliness at each launch | `git status --porcelain` over `docs/research/candidates/variable_n_fleet_churn`, `experiments/candidates/variable_n_fleet_churn_bpcr_r09`, `experiments/candidates/variable_n_fleet_churn_b_explore`, `tests/experiments/candidates/variable_n_fleet_churn*`, `scripts/run_vnfc_*` returned **nothing**. `experiments/candidates/variable_n_fleet_churn_r02/` (the A0 implementation) remains untracked by design; other directions were dirty from concurrent sessions and were not touched |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10, torch 2.7.0+cpu, device CPU, `torch.set_num_threads(1)` |
| Machine | Windows 10.0.26200, 16 logical CPUs |
| Seeds | `B0-DEBUG` `2026090301`; `B1-B3-PRIMARY` `2026090311` / `2026090321` / `2026090331`, fixed outcome-blind in the recast intake §3 before any launch. The `PRIMARY` seeds were never used |
| Result root (gitignored) | `temp/directions/variable_n_fleet_churn/exp/R02_20260903/` |
| Disposition | **`QUARANTINED_INCOMPLETE_ATTEMPT`** ×2; object not consumed; no polarity |

---

## 1. The recast in force, and what it changed about these launches

Per owner decisions 4 and 7 of `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`
A.4 and `docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`:

- `DIRECTION.md:181-182` ("No R02 result-bearing DEBUG is permitted until the one-law A0 object is
  complete and passing under its finite claim ceiling.") did **not** hold these launches. A0 remains
  unimplemented (`implementation_started=false`) and holds nothing;
- the 304-row A0 panel was **not** produced and was not required. Its replacement §4 integrity item,
  the 52-row `VNFC-R02-PRESENTATION-CONFORMANCE-52`, ran and passed (§6);
- the `bpcr_backend.dll` build key and the A0 byte manifests were **recorded**, not required (§7);
- missing resource telemetry would have been recorded as `resources_unmeasured: true`. It did not
  arise: telemetry was fully measured in both attempts (§11), so the D7 downgrade path was not
  exercised by a real failure (it is covered by tests instead);
- the fresh 4 GiB physical/effective admission **remained** a launch condition and passed each time.

What stopped both attempts was **not** a demoted gate. Attempt 01 stopped on a serialization defect
in the R01 runner's own control flow; attempt 02 stopped on a §4 integrity condition the recast
explicitly kept — the per-decision fresh-relabel mismatch count.

---

## 2. Resource admission (a launch condition, unchanged)

`python scripts/hmasd_resource_preflight.py admit-memory --out <run_dir>/preflight.json`, run
immediately before each invocation and re-validated inside the runner (`_implementation_hard_fence`,
freshness window 300 s, floor `4,294,967,296` B on both physical and effective).

| Receipt | `assessed_at` | available physical = effective | `passed` |
| --- | --- | ---: | --- |
| `R02_20260903/DEBUG/preflight.json` (attempt 01) | 2026-09-03T10:13:21.807803Z | 13,067,223,040 B (12.17 GiB) | `true` |
| `R02_20260903/DEBUG_ATTEMPT_02/preflight.json` (attempt 02) | 2026-09-03T10:21:13.720159Z | 12,690,440,192 B (11.82 GiB) | `true` |
| `R02_20260903/diagnostic/preflight.json` (the non-result probe of §9) | 2026-09-03T10:27:28.111867Z | 13,523,480,576 B (12.59 GiB) | `true` |

An earlier receipt taken at 2026-09-03T10:09:45.089675Z (12,355,276,800 B, `passed: true`) belongs
to a launch that aborted before the telemetry sink existed; see deviation D1.

---

## 3. Commands actually run

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/hmasd_resource_preflight.py admit-memory --out '<root>/DEBUG_ATTEMPT_02/preflight.json'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_vnfc_bpcr_r02.py debug `
    --stage B0-DEBUG --seed 2026090301 --updates 8 `
    --preflight-receipt '<root>/DEBUG_ATTEMPT_02/preflight.json' `
    --scratch-root '<root>/DEBUG_ATTEMPT_02/scratch' `
    --durable-root '<root>/DEBUG_ATTEMPT_02/scientific/VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B0-DEBUG/2026090301' `
    --publication-root '<root>/DEBUG_ATTEMPT_02/publication' `
    --record-root '<root>/records'
```

with `<root>` = `temp/directions/variable_n_fleet_churn/exp/R02_20260903`. Attempt 01 is the same
command with `DEBUG` in place of `DEBUG_ATTEMPT_02`. One process at a time; the runner sets
`torch.set_num_threads(1)`, inside the instructed ceiling of four threads.

---

## 4. Attempt 01 — quarantined on a freeze-token serialization defect

Wall 154.9 s (shell), 2026-09-03 ~10:13–10:15 PDT. Verbatim terminal line:

```json
{"error_type":"TypeError","message":"Object of type PSB0ActualComparison is not JSON serializable","record":"...\\records\\r02-record-B0-DEBUG-2026090301.json","schema":"VNFC_BPCR_R02_CLI_ERROR_V1"}
```

Where it stopped: `_freeze_before_n7` puts `dict(gate)` into a canonical-JSON digest, and
`assess_posttraining_debug_gate` carries the live PS-B0 comparison rows in that gate under
`ps_b0_comparisons` so the artifact serialiser can consume them. On the DEBUG path with a real
adapter those rows are `PSB0ActualComparison` dataclasses. **This is upstream of the held-out `N = 7`
freeze**, so no endpoint of any kind was computed.

The runner quarantined it correctly. `INCOMPLETE.json` records
`quarantine_only: true`, `resume_allowed: false`, `scientific_result: false`,
`evaluation_allowed: false`, `publication_allowed: false`, and preserved
`QUARANTINE_CHECKPOINTS.bin` (3,822,222 B) and `QUARANTINE_CHECKPOINTS_MANIFEST.json`. The
publication root received `INCOMPLETE_CLAIM.json` and `TELEMETRY_TERMINAL.json` only. Nothing from
this attempt is resumed, salvaged or interpreted here.

This is the same class of failure that mechanically quarantined the R01 formal DEBUG: a code path
that had never executed.

---

## 5. Attempt 02 — quarantined on the per-decision fresh-relabel mismatch

Wall 162.0 s measured by the runner (165.4 s shell), 2026-09-03 ~10:21–10:24 PDT. Verbatim terminal
line:

```json
{"error_type":"BExploreContractError","message":"INCOMPLETE: learned-arm actual-path relabel mismatch","record":"...\\records\\r02-record-B0-DEBUG-2026090301.json","schema":"VNFC_BPCR_R02_CLI_ERROR_V1"}
```

raised at `scripts/run_vnfc_bpcr_b_explore.py:1911`, i.e.

```python
mismatch = {arm: sum(int(row["relabel_mismatch_count"]) for row in learned if row["arm"] == arm) for arm in ARMS}
if mismatch != {"MAPR": 0, "DIRECT": 0}:
    raise BExploreContractError("INCOMPLETE: learned-arm actual-path relabel mismatch")
```

The same quarantine flags were written (`quarantine_only: true`, `resume_allowed: false`,
`scientific_result: false`, `evaluation_allowed: false`, `publication_allowed: false`), with
`QUARANTINE_CHECKPOINTS.bin`, `QUARANTINE_CHECKPOINTS_MANIFEST.json`, `STARTED.json` in the
scientific root and `INCOMPLETE_CLAIM.json` + `TELEMETRY_TERMINAL.json` in the publication root. The
per-arm and per-cell mismatch counts were not written before the raise, so the run itself reports
only that the aggregate is nonzero; §9 measures the same quantity directly.

**What did complete before the raise, as direct observations:**

- 8 updates × 2 arms of real training on the real native host: 16 balanced episodes, 96 joint
  decisions, 12 action forwards, 384 optimizer forwards, 16 backwards and 16 AdamW steps per arm per
  update, all reconciled by the runner (a mismatch raises);
- both initial and final checkpoints created and validated as distinct;
- the **288-comparison PS-B0 panel passed** at the DEBUG checkpoint under the R02 canonical sort:
  `validate_ps_b0` requires the exact 288 addresses and
  `mismatch_by_arm == {"MAPR": 0, "DIRECT": 0}`, and raises otherwise; execution reached
  `_freeze_before_n7`, which is downstream of that check;
- the eight-corner high-demand BCRH precheck passed (`validate_bcrh_precheck`, and the gate refuses
  unless `common_host_valid`);
- the `N = 3` and `N = 5` evaluation cells and the `N = 7` cells all ran to completion; the raise is
  on their aggregate relabel counter, after evaluation.

---

## 6. The 52-row presentation-conformance check (the replacement §4 integrity item)

`VNFC-R02-PRESENTATION-CONFORMANCE-52`, row list frozen in the recast intake §4 before the check was
implemented.

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  --basetemp C:/Projects/HMASD/temp/pytest_vnfc_recast \
  tests/experiments/candidates/variable_n_fleet_churn_b_explore/test_r02_presentation_conformance.py
54 passed in 19.36s
```

54 = the 52 frozen rows + `test_row_inventory_is_exactly_the_frozen_52` +
`test_c_direct_contains_mapr_at_zero_residual`. **All 52 rows pass.**

Whole-direction suite at the commit-C sha:

```
... -m pytest -q --basetemp C:/Projects/HMASD/temp/pytest_vnfc_recast \
  tests/experiments/candidates/variable_n_fleet_churn \
  tests/experiments/candidates/variable_n_fleet_churn_b_explore \
  tests/experiments/candidates/variable_n_fleet_churn_bpcr_r09 \
  tests/experiments/candidates/variable_n_fleet_churn_r02 \
  tests/vnfc_bpcr_b_explore_test.py
8 failed, 348 passed, 1 warning in 237.11s (0:03:57)
```

The 8 failures reproduce in isolation at this checkout and are the pre-existing canonical-EOL
`SourceManifestError: empirical source manifest bytes are not canonical` failures that
`VNFC_BPCR_BEXP_R01_ENGINEERING_MILESTONE_20260901.md` already records ("Its full historical suite
still has pre-existing canonical-EOL manifest failures in this checkout"). Nothing in this work
touches that frozen surface.

---

## 7. Recorded fields that used to be gates

### Native identity (recast row 6) — recorded, `gating: false`

| Field | Frozen A0 literal | Observed 2026-09-03 | Equal |
| --- | --- | --- | --- |
| `bpcr_backend.dll` build key | `7222d990642a7e4cb010b6526f17acdb3f3aa85f11d1b8d34be0eedbe11e9c99` | `7222d990642a7e4cb010b6526f17acdb3f3aa85f11d1b8d34be0eedbe11e9c99` | **yes** |
| `bpcr_backend.dll` size | 213,504 B | 213,504 B | **yes** |
| `bpcr_backend.dll` sha256 | `dadac9589cf1a885b1acd3891f7411152fa2748cbc34ddbf3537d0b2708f5f68` | `adc39faacc60dc13c1572f0098ead13a986c851f2ee121855fb12120e5bc3580` | **no** |

Reading: the build key is derived from the source, contract, science-card, public-law, compiler and
flag bytes plus the ABI version, so a rebuild from unchanged source reproduces it exactly — and did.
The artifact **digest** differs because MSVC embeds non-deterministic bytes in the image. Under the
recast this is recorded and holds nothing; under the pre-recast A0 binding it would have refused the
launch. Also recorded: shadow `vnfc_b_tick_telemetry.dll` build key
`1327df63c240b91ca37a9dc71ac3083d9ae9afd87e94fa044abbb3ef3dac9d3f`, sha256
`1656cabbe68ce6af86303173dbfffa246801121f52d21fbce320738031d871a1`, 161,792 B; compiler
`...\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe`, sha256
`88c8344236a27a6e727e0a8edc49aaa2690bdc7a9464b9d18cc7abe70a9f1c0d`.

Both DLLs were **compiled from unchanged source into the default `%LOCALAPPDATA%\Temp` cache root**
on this host (the owner cleared every `hmasd_*_native` root on 2026-09-02). `TMP`/`TEMP`/`TMPDIR`
were not redirected.

### A0 byte manifests (recast rows 3 and 5) — recorded, never required

Both files are present and were recorded, not verified against any expected content:
`VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_KERNEL_BYTE_MANIFEST_20260901.md` and
`..._REFERENCE_PYTHON_SOURCE_MANIFEST_20260901.tsv`. The 942 loaded Python dependency sources, the
31 opened distribution resources, the 81→82 compiled-module transition and the post-load canonical
root `ce22039a…` were **not** produced and were not required. `git check-ignore -v` reports the
`.tsv` as matching no rule (tracked; committed at `55a46c206`), and the `.md` as re-included by
`.gitignore:73 !docs/research/candidates/**/*.md`.

---

## 8. The exposure line (a launch condition the recast keeps)

`||θ − θ0|| / ||θ0||` per arm per update, against each arm's own initialisation, recorded beside the
run because the create-once result schema is frozen. Attempt 02, all 16 rows:

| Arm | Update | `||θ0||` | `||θ − θ0||` | `||θ − θ0|| / ||θ0||` | mean pre-clip grad norm | AdamW steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MAPR | 0 | 33.316665 | 0.861256 | 0.025851 | 0.100780 | 16 |
| MAPR | 1 | 33.316665 | 1.363979 | 0.040940 | 0.096752 | 16 |
| MAPR | 2 | 33.316665 | 1.844154 | 0.055352 | 0.186304 | 16 |
| MAPR | 3 | 33.316665 | 2.710384 | 0.081352 | 0.392809 | 16 |
| MAPR | 4 | 33.316665 | 3.038883 | 0.091212 | 0.387127 | 16 |
| MAPR | 5 | 33.316665 | 3.511573 | 0.105400 | 0.669485 | 16 |
| MAPR | 6 | 33.316665 | 3.793762 | 0.113870 | 0.544242 | 16 |
| MAPR | 7 | 33.316665 | 4.111832 | **0.123417** | 1.124412 | 16 |
| DIRECT | 0 | 38.652299 | 0.925487 | 0.023944 | 0.070453 | 16 |
| DIRECT | 1 | 38.652299 | 1.440405 | 0.037266 | 0.085467 | 16 |
| DIRECT | 2 | 38.652299 | 2.145115 | 0.055498 | 0.113758 | 16 |
| DIRECT | 3 | 38.652299 | 2.743505 | 0.070979 | 0.231452 | 16 |
| DIRECT | 4 | 38.652299 | 3.410898 | 0.088246 | 0.401650 | 16 |
| DIRECT | 5 | 38.652299 | 3.764734 | 0.097400 | 0.432091 | 16 |
| DIRECT | 6 | 38.652299 | 4.140393 | 0.107119 | 0.539326 | 16 |
| DIRECT | 7 | 38.652299 | 4.523300 | **0.117025** | 0.629947 | 16 |

Both learners move monotonically inside an 8-update budget, reaching about 12% relative parameter
displacement. This satisfies §11.4's exposure clause. It says nothing about return or recovery.

Attempt 01 produced a bit-identical exposure line where the two attempts overlap (MAPR update 0
`0.02585059206655834`, update 1 `0.0409398324711615`; DIRECT update 6 `0.10711893599150846`, update 7
`0.11702537303517462`), which is the direct evidence that the attempt-01 repair did not touch
training and that the attempt-02 launch was outcome-blind.

---

## 9. What the two attempts do establish: the relabel probe measures presentation ∘ batching

The condition that stopped attempt 02 is `_evaluate_learned_batch`'s per-decision fresh-relabel
check. It compares

- `output["command"][index]`, taken from a forward over a **batch of 8** worlds, against
- `model(*_permuted_inputs(inputs[index], permutation))["command"][0]`, a forward over a **batch of
  1**, mapped back through the permutation.

So it varies two things at once: the presentation **and** the batch width. A non-result-bearing
`A/RECON` probe (`<root>/diagnostic/probe.py`, receipt
`<root>/diagnostic/relabel-probe.json`, wall 18.6 s, admission at 13,523,480,576 B) separates them
on freshly initialised, untrained checkpoints of the same seed family, over all 12
`(N, failed-zone)` cells × 8 worlds × 2 arms = 192 world-decisions per law:

| Law | `batch8_vs_batch1` (batching only) | `presentation_1_vs_1` (presentation only) | `runner_probe_8_vs_1` (what the runner compares) |
| --- | ---: | ---: | ---: |
| R01, no canonical sort | 12 / 192 | **15 / 192** | 8 / 192 |
| R02, canonical opaque-rank sort | 12 / 192 | **0 / 192** | 12 / 192 |

Per cell, the presentation column is `0/8` in **every** cell and for **both** arms under the R02 law,
and is nonzero under the R01 law only at `N = 5` zone 2 (DIRECT, 1/8) and at `N = 7` (MAPR 6/8 and
DIRECT 2/8 in zone 1; MAPR 3/8 and DIRECT 3/8 in zone 2). The batching column is identical under
both laws (12/192), concentrated at `N = 7` (3/8 per arm per zone) with 1/8 at `N = 5` zone 1.

Three direct readings, none of them an algorithm effect:

1. **The R02 canonical opaque-rank sort does what it was selected to do.** Presentation dependence
   of the inverse-mapped physical command falls from 15/192 to exactly 0/192 on this panel. The
   288-comparison PS-B0 panel passing inside attempt 02 is the same fact measured a second way.
2. **Batch-position dependence is not a presentation effect and no presentation law removes it.**
   It is identical (12/192) under both laws. It is the residual finite-precision channel the A0
   freeze already forbids *relying on* ("batch-neighbor identity", A0 freeze:909-910); it is not
   something the freeze claims to eliminate.
3. **The R01 relabel probe is not a presentation test and is less sensitive than one.** Because it
   varies both quantities, its count under the R01 law (8/192) is *lower* than the true presentation
   count (15/192): the two error sources partially cancel. Under the R02 law, where presentation
   dependence is zero, the probe reports the batching residual (12/192) and refuses the launch.

Boundary on this probe: single instance, untrained checkpoints, one seed family; under evidence
spec §5.1 it may not be cited as an algorithm effect, and it establishes nothing about return,
recovery or comparator behaviour.

---

## 10. The reading rule, applied

The reading rule of the recast intake §5 (transferred verbatim from
`VNFC_BPCR_BEXP_PRESENTATION_SAFE_RETURN_R01_INNOVATOR_INTAKE_20260901.md`:99-114) **was not
reached**. Its own last clause governs this outcome:

> Relabel, telemetry, resource, native-host, hard-validity, or comparator-competence failure means
> `INCOMPLETE` or comparator-specific `NONIDENTIFIED`, never a scientific null. A valid Class B null
> does not close the direction.

Both attempts are `INCOMPLETE`. There is no deciding number, no polarity, no preliminary support and
no falsification. `MAPR` final-minus-initial, paired `N = 7` `R_fail_60` against `DIRECT` and against
`BCRH`, `U_total`, `U_intact`, the recovery latencies and the DIRECT residual-activity flag were
never computed for any checkpoint.

---

## 11. Verbatim summary lines

```json
{"error_type":"TypeError","message":"Object of type PSB0ActualComparison is not JSON serializable","record":"C:\\Projects\\HMASD\\temp\\directions\\variable_n_fleet_churn\\exp\\R02_20260903\\records\\r02-record-B0-DEBUG-2026090301.json","schema":"VNFC_BPCR_R02_CLI_ERROR_V1"}
```

```json
{"error_type":"BExploreContractError","message":"INCOMPLETE: learned-arm actual-path relabel mismatch","record":"C:\\Projects\\HMASD\\temp\\directions\\variable_n_fleet_churn\\exp\\R02_20260903\\records\\r02-record-B0-DEBUG-2026090301.json","schema":"VNFC_BPCR_R02_CLI_ERROR_V1"}
```

Attempt 02 `INCOMPLETE.json`, verbatim fields:

```json
{"quarantine_only": true, "resume_allowed": false, "scientific_result": false, "evaluation_allowed": false, "publication_allowed": false, "exception": {"message": "INCOMPLETE: learned-arm actual-path relabel mismatch", "type": "BExploreContractError"}}
```

Relabel-probe totals, verbatim from `<root>/diagnostic/relabel-probe.json`:

```json
{"R01_plain": {"batch8_vs_batch1": 12, "presentation_1_vs_1": 15, "runner_probe_8_vs_1": 8}, "R02_canonical_opaque_rank_sort": {"batch8_vs_batch1": 12, "presentation_1_vs_1": 0, "runner_probe_8_vs_1": 12}}
```

---

## 12. Resource telemetry (measured; `resources_unmeasured: false`)

Attempt 02, from `TELEMETRY_TERMINAL.json`:

| Field | Value |
| --- | ---: |
| `attempt_disposition` | `INCOMPLETE` |
| `end_to_end_wall_seconds` | 161.268 |
| `end_to_end_cpu_seconds` | 183.125 |
| `process_tree_peak_rss_bytes` | 428,601,344 (409 MiB) |
| `scratch_peak_bytes` | 0 |
| `durable_peak_bytes` | 3,857,390 |
| `io_read_bytes` / `io_write_bytes` | 642,051,895 / 3,857,390 |
| `available_physical_bytes` = `effective_available_bytes` | 12,690,440,192 |
| `worker_count` / `threads_per_worker` / `peak_process_count` / `peak_thread_count` | 1 / 1 / 1 / 22 |
| `host_cpu_occupancy` / `cpu_core_equivalents` | 0.0710 / 1.136 (of 16 logical CPUs) |
| `measurement_source` | `Windows Toolhelp/Process/PSAPI process-tree sampling`, 2,123 samples at 0.05 s |

`native_integrated_ticks`, `scientific_work_transitions`, `primary_host_calls` and
`shadow_host_calls` all read `1`: those are the runner's `_incomplete_counter_floor` substitutes for
a quarantined attempt, not measured work. `resources_unmeasured` is `false` in both attempts and the
decision-7 downgrade path was never triggered by a real failure; it is covered by 21 test cases in
`tests/experiments/candidates/variable_n_fleet_churn_b_explore/test_r02_recast_records.py`.

Another session held two 4-thread runs on the same host during these launches, as expected; this
process ran single-threaded at about 1.14 core-equivalents.

---

## 13. Deviations, each named

- **D1 — a launch that never started.** The first invocation at sha `04b032eb9` returned
  `REPAIR_REQUIRED: prebuilt load-only binding is not installed` in 2.8 s:
  `prepare_native_backends()` resolved the two content-keyed artifacts but did not install the
  binding. No root, RNG master, model, checkpoint or artifact existed. Fixed at `a8305f645`. The
  preflight receipt taken for it (10:09:45Z) was superseded.
- **D2 — attempt 01 repaired, then a fresh attempt.** After attempt 01's quarantine the
  freeze-token digest defect was repaired **from the R02 runner** (`a2efdc6a4`), not by editing
  `scripts/run_vnfc_bpcr_b_explore.py`, since R01 source is reused read-only
  (`DIRECTION.md:164-165`). Attempt 01 stays permanently quarantined and was not resumed or
  salvaged; attempt 02 is a fresh, differently-rooted attempt of the unchanged object, per §6.2
  ("After repair, an outcome-blind fresh attempt MAY implement the unchanged object"). The repair
  was outcome-blind by construction: attempt 01 stopped before the held-out freeze, so no endpoint
  existed, and §8 shows the two attempts' training was bit-identical.
- **D3 — attempt 02 was NOT repaired and no third attempt was launched.** The relabel condition is a
  §4 integrity item that the recast explicitly keeps. Changing what it compares after seeing it fail
  would be changing a declared comparison in response to an outcome. The instruction for this
  session ("if DEBUG shows an instrumentation failure, quarantine, do not rerun with changes,
  report") is followed here. The three 64-update `PRIMARY` seeds were therefore not launched.
- **D4 — the 52-row check row `G01` is a surrogate.** The registered R01 `N=5/reverse` witness
  parameterisation lives in the untracked A0 package
  `experiments/candidates/variable_n_fleet_churn_r02/fixtures.py`
  (`source_bound_witness_parameter_fixture`), which this recast neither commits nor imports. `G01`
  constructs its own one-ULP near-tie exhibiting the same mechanism. Recorded in the recast intake §4.
- **D5 — rows `A05` and `G02` are exercised at the decoder.** Byte-identical agent rows do not
  guarantee byte-identical candidate logits, because the row-wise GEMM is row-position dependent, so
  feeding duplicate rows through the model tests the GEMM rather than the tie rule. Recorded in the
  recast intake §4 implementation note. No row was added, removed or renamed.
- **D6 — `hmasd_run.py` was not used.** The direction's own runner owns its manifest and the
  create-once three-artifact publication; this matches how the R01 object and the SCDMP and CBSC
  recasts were executed.
- **D7 — `experiments/candidates/variable_n_fleet_churn_r02/` was left uncommitted.** It is the A0
  implementation (13 modules) and is outside the experiment path this session was scoped to. Its
  test directory `tests/experiments/candidates/variable_n_fleet_churn_r02/` **is** inside the scope
  and was committed at `55a46c206`, so that test directory is tracked while the package it imports
  is not.

---

## 14. Could not verify

- **The per-arm and per-cell relabel mismatch counts of attempt 02 itself.** The runner raises on
  the aggregate before writing the counter, and no instrumentation was added after the failure. §9
  measures the same quantity on untrained checkpoints of the same seed family instead; the two are
  not the same measurement.
- **Whether the 12/192 batch-position residual would persist at trained checkpoints**, or grow or
  shrink with training. The probe used freshly initialised parameters only.
- **Whether the relabel condition would also stop a `PRIMARY` seed.** `PRIMARY` was never launched.
- **The A0 byte-manifest quantities** (942 sources, 31 resources, 81→82 modules, post-load root
  `ce22039a…`). The A0 runner is unfinished (`implementation_started=false`); these were recorded as
  not-produced, which the recast permits.
- **Whether the `bpcr_backend.dll` sha256 mismatch is entirely due to MSVC image non-determinism.**
  The build key rederives exactly and the size matches to the byte, which is consistent with that
  reading, but no differential analysis of the two images was done and the frozen image no longer
  exists on this host.
- **The 8 pre-existing suite failures** were reproduced but not diagnosed; they are on a frozen
  surface this work does not touch.

---

## 15. Interpretation boundary

Nothing here is a return, recovery, learnability, comparator, superiority, stability, transfer,
arbitrary-`N`, repeated-churn, general-MARL, permutation-invariance, UAV, safety, flight, deployment
or lifecycle claim. `VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02` is **not consumed**; both attempts
are permanently quarantined and carry no polarity, and under evidence spec §6.1 the object may be
attempted again after the open question in §16 is settled. Revision-09 remains consumed and invalid
for value attribution, and the quarantined R01 DEBUG remains unavailable.

The one positive finding is a conformance observation, not an algorithm observation: on the panel of
§9 and on the 288-comparison PS-B0 panel inside attempt 02, the canonical opaque-rank sort makes the
inverse-mapped physical command a function of physical state under all four presentations, which the
R01 law did not. It supports only the presentation-safety premise of the R02 question. It supports
no claim about whether `MAPR-4` learns post-loss recovery.

## 16. What the owner must decide before R02 can produce a result

The per-decision fresh-relabel condition, as implemented, compares a batch-8 forward against a
batch-1 relabelled forward and therefore refuses any presentation law, including one with exactly
zero presentation dependence. Three options, none of them taken here:

1. **Repair the probe to the declared comparison** — batch-1 unpermuted versus batch-1 relabelled,
   which is what "one fresh relabel of that arm's own checkpoint with zero physical-command
   mismatches required" (R01 intake:66-68) says. §9 shows this still discriminates: 15/192 under the
   R01 law, 0/192 under R02. This is a change to a §4 integrity item's measurement and needs the
   owner's word.
2. **Keep the probe and require batch invariance too**, which would mean a law that fixes the batch
   dimension as well as the presentation dimension — a materially larger object than the canonical
   sort, and one the direction has not defined.
3. **Record the batch residual and demote the aggregate to a reported field**, with a stated
   tolerance. This weakens a §4 item and should not be done without the owner naming the tolerance.

The reviewer's recommendation is option 1, as the repair of a measurement to what the direction's
own text declares, with the §9 numbers published beside it.

---

# Part II — the repaired relabel probe, `B0-DEBUG` attempt 05, and the three 64-update `PRIMARY` seeds (2026-09-03, second launch window)

Executed 2026-09-03 by Claude Code (Fable 5.1) after owner decision **F.4 option (a)** of
`docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` (commit `ee84406cc`) — the
option §16 above put to the owner as "repair the probe to the declared comparison". Part I is left
exactly as written: it is the permanent record of attempts 01 and 02 and is not revised by anything
below.

**Outcome: a valid `B/EXPLORE` result. The object `VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02` is
consumed. Polarity: `INSTABILITY/HETEROGENEITY`.** Neither preliminary support nor falsification is
reached; the reading rule's third clause governs. The deciding numbers are in §22.

| Fact | Value |
| --- | --- |
| Launch sha, all four runs | `b90122e68` — "Install the R02 exposure budget at validate_runtime_terminal" |
| Relabel probe law | `VNFC-R02-RELABEL-LIKE-FOR-LIKE-V1` (presentation only, both sides at batch 1) |
| Presentation law | `VNFC-R02-ORC-CANONICAL-OPAQUE-RANK-SORT-V1` (unchanged from Part I) |
| Seeds | `B0-DEBUG` `2026090301` (8 updates); `B1-B3-PRIMARY` `2026090311`, `2026090321`, `2026090331` (64 updates each), fixed outcome-blind in the recast intake §3 before any launch |
| Attempts consumed | `B0-DEBUG` attempt 05 (sealed); three `PRIMARY` attempts, all sealed |
| Attempts quarantined in this window | `B0-DEBUG` attempts 03 and 04 (frozen accounting constant, §26 D8); `PRIMARY_2026090311_ABORTED_01` (shell timeout, §26 D9) |
| Disposition | **`VALID_B_EXPLORE_RESULT`**, polarity `INSTABILITY/HETEROGENEITY` |
| Result root (gitignored) | `temp/directions/variable_n_fleet_churn/exp/R02_20260903/` |

---

## 17. What changed: the relabel probe, before and after

The old probe, quoted from the read-only R01 substrate
(`scripts/run_vnfc_bpcr_b_explore.py`, `_evaluate_learned_batch`, lines 461-506):

```python
477:                output = model(*stacked); policy_forwards += 1
...
490:                    permuted_output = model(*_permuted_inputs(inputs[index], permutation)); diagnostic_forwards += 1
492:                    permuted = permuted_output["command"][0]
493:                mapped = tuple(len(permutation) if int(choice) == len(permutation) else permutation[int(choice)] for choice in permuted)
494:                mismatch += int(tuple(int(choice) for choice in output["command"][index]) != mapped)
```

`output` at line 477 is a **batch-8** forward; `permuted_output` at line 490 is a **batch-1** forward.
Line 494 therefore compares a batch-8 identity presentation against a batch-1 relabelled
presentation, so it varies presentation and batch position together and reports their composition.
Part I §9 measured that composition on untrained checkpoints: the old probe reports 8/96 under the
R01 law and 12/96 under the R02 law, i.e. it under-reports real presentation failure and refuses a
law whose presentation dependence is exactly zero.

The repaired probe, installed by `install_like_for_like_relabel_probe()` in
`scripts/run_vnfc_bpcr_r02.py` onto the imported R01 module — `scripts/run_vnfc_bpcr_b_explore.py`
is **not edited** (`DIRECTION.md:164-165` makes R01 source read-only substrate):

```python
identity_output = model(*inputs[index]); diagnostic_forwards += 1        # batch 1, identity
permuted_output = model(*r01._permuted_inputs(inputs[index], permutation)); diagnostic_forwards += 1  # batch 1, relabelled
reference = tuple(int(c) for c in identity_output["command"][0])
mapped = tuple(len(permutation) if int(c) == len(permutation) else permutation[int(c)] for c in permuted_output["command"][0])
mismatch += int(reference != mapped)                                     # GATING: presentation only
batched = tuple(int(c) for c in output["command"][index])                # the batch-8 forward
residual_sink.append({..., "batch_position_command_differs": batched != reference})   # descriptive
```

Both sides of the gating comparison are batch-1 forwards of the same decision state at the same
batch position; presentation is the only quantity that varies. That is the direction's own declared
condition, verbatim: "Every later evaluation decision state also receives one fresh relabel of that
arm's own checkpoint with zero physical-command mismatches required"
(`VNFC_BPCR_BEXP_PRESENTATION_SAFE_RETURN_R01_INNOVATOR_INTAKE_20260901.md`:66-68). It remains a
launch condition and still requires exactly zero.

The **batch-position residual** — the batch-8 policy forward against the batch-1 identity forward at
the same presentation — is computed from the same identity forward at no extra cost and published as
`VNFC_BPCR_R02_BATCH_POSITION_RESIDUAL_V1` with `gating: false`. It never gates.

---

## 18. Tests of the repair

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  --basetemp C:/Projects/HMASD/temp/directions/variable_n_fleet_churn/test/r02_probe_e3 \
  tests/experiments/candidates/variable_n_fleet_churn_b_explore/test_r02_relabel_probe.py
12 passed in 15.79s
```

The 12 cases, in
`tests/experiments/candidates/variable_n_fleet_churn_b_explore/test_r02_relabel_probe.py`:

| Test | What it pins |
| --- | --- |
| `test_diagnostic_totals_reproduce` | rebuilds Part I §9's panel on untrained checkpoints and reproduces all six totals exactly |
| `test_batch_residual_is_identical_under_both_laws` | 12/96 under R01 and under R02 — the residual is a property of the arithmetic, not of the presentation law |
| `test_repaired_probe_passes_the_r02_law_and_fails_the_r01_law` | the required discrimination |
| `test_old_conflated_probe_refuses_the_r02_law` | the defect Part I §16 reported |
| `test_repaired_probe_exposure_budget` | 96 (MAPR) / 108 (DIRECT) diagnostic forwards per learned evaluation row |
| `test_batch_residual_record_is_descriptive_only` / `test_empty_residual_record_is_valid` | `gating: false`, and the record is well-formed when empty |
| `test_recast_record_names_the_repaired_probe` | the probe law and the F.4 provenance appear in the run record |
| `test_installed_probe_replaces_the_r01_comparison` | installation swaps `_evaluate_learned_batch` and `validate_runtime_terminal` on the imported module |
| `test_installed_validator_checks_the_aggregate_exposure` | the second frozen 48/60 constant, at `run_vnfc_bpcr_b_explore.py:975` |
| `test_r01_runner_source_is_untouched` | `RELABEL_PROBE_LAW` and `batch_position_command_differs` do not appear in the R01 source |

The reproduced totals, over **96 world-decisions per law** (6 `(N, failed-zone)` cells x 8 worlds x
2 arms; Part I wrote "/192", which is the total across *both* laws — the correction is recorded in
the recast intake §7b):

| Law | batch-position residual | presentation (like-for-like) | old conflated probe |
| --- | ---: | ---: | ---: |
| R01, no canonical sort | 12 / 96 | **15 / 96** | 8 / 96 |
| R02, canonical opaque-rank sort | 12 / 96 | **0 / 96** | 12 / 96 |

---

## 19. Resource admission (a launch condition, unchanged)

`python scripts/hmasd_resource_preflight.py admit-memory --out <run_dir>/preflight.json`, immediately
before each invocation, re-validated inside the runner (freshness window 300 s, floor
`4,294,967,296` B on both physical and effective). Physical equals effective on this host.

| Receipt | `assessed_at` | available physical = effective | `passed` |
| --- | --- | ---: | --- |
| `DEBUG_ATTEMPT_03/preflight.json` | 2026-09-03T15:40:58.764950Z | 15,612,915,712 B | `true` |
| `DEBUG_ATTEMPT_04/preflight.json` | 2026-09-03T15:46:25.584083Z | 15,710,945,280 B | `true` |
| `DEBUG_ATTEMPT_05/preflight.json` (superseded, §26 D10) | 2026-09-03T16:04:53.102920Z | 14,206,586,880 B | `true` |
| `DEBUG_ATTEMPT_05/preflight.json` | 2026-09-03T16:06:24.508416Z | 14,270,267,392 B | `true` |
| `PRIMARY_2026090311_ABORTED_01/preflight.json` | 2026-09-03T16:10:43.191837Z | 13,621,387,264 B | `true` |
| `PRIMARY_2026090311_02/preflight.json` | 2026-09-03T16:22:24.193893Z | 14,109,392,896 B | `true` |
| `PRIMARY_2026090321_01/preflight.json` | 2026-09-03T16:33:57.040367Z | 12,531,900,416 B | `true` |
| `PRIMARY_2026090331_01/preflight.json` | 2026-09-03T16:46:04.860484Z | 13,068,845,056 B | `true` |

---

## 20. Commands actually run

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/hmasd_resource_preflight.py admit-memory --out '<A>/preflight.json'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_vnfc_bpcr_r02.py debug `
    --stage B0-DEBUG --seed 2026090301 --updates 8 `
    --preflight-receipt '<A>/preflight.json' `
    --scratch-root '<A>/scratch' `
    --durable-root '<A>/scientific/VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B0-DEBUG/2026090301' `
    --publication-root '<A>/publication' --record-root '<A>'

& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/hmasd_resource_preflight.py admit-memory --out '<P>/preflight.json'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_vnfc_bpcr_r02.py primary `
    --stage B1-B3-PRIMARY --seed <SEED> --updates 64 `
    --preflight-receipt '<P>/preflight.json' `
    --scratch-root '<P>/scratch' `
    --durable-root '<P>/scientific/VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B1-B3-PRIMARY/<SEED>' `
    --publication-root '<P>/publication' --record-root '<P>' `
    --archived-debug-valid-claim '<A>/publication/VALID_CLAIM.json' `
    --archived-debug-scientific-root '<A>/scientific/VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B0-DEBUG/2026090301'
```

with `<A>` = `<root>/DEBUG_ATTEMPT_05`, `<P>` in
`{PRIMARY_2026090311_02, PRIMARY_2026090321_01, PRIMARY_2026090331_01}`, `<SEED>` the matching seed,
and `<root>` = `temp/directions/variable_n_fleet_churn/exp/R02_20260903`. One process at a time;
`OMP_NUM_THREADS=MKL_NUM_THREADS=4` in the environment and `torch.set_num_threads(1)` inside the
runner, so at most one torch thread was used and the four-thread ceiling was never approached.

---

## 21. `B0-DEBUG` attempt 05 — completed and sealed

| Field | Value |
| --- | ---: |
| Started / finished | 2026-09-03T16:06:41.445972Z / 2026-09-03T16:08:40.970787Z |
| Wall (runner) / wall (telemetry) / CPU | 119.525 s / 118.580 s / 131.75 s |
| `status` | `COMPLETE`; `attempt_disposition` `VALID_CAPABLE` |
| Relabel mismatch, MAPR / DIRECT | **0 / 0** — the repaired probe passes at trained checkpoints |
| PS-B0 | passed, 288 comparisons, 0 mismatches per arm |
| Evaluation diagnostic forwards | MAPR 576 = 96 x 6 groups; DIRECT 648 = 108 x 6 — the R02 budget, exactly |
| Batch-position residual (descriptive) | 18 / 576, by cell `{N5z1: 3, N5z2: 2, N7z1: 5, N7z2: 8}` |
| `RESULT_BODY.json` | sha256 `d7c78b0bfcfbb061ae9288cfda7a7ccc822ec4e0c8efe6ba958fc2cc78832e87`, 43,458,334 B |
| storage seal | sha256 `a6cc89fc6e83a7f972657fbf067c3469ef3355404deac60d0ecebdd72a6ae328` |
| `TELEMETRY_TERMINAL.json` | sha256 `777038183267035fa21ef3fe319259f4be3291d2a1b113fba2928358ef6b87d2`, 5,682 B |
| `resources_unmeasured` | `false` |

Attempt 05's exposure line is **bit-identical** to attempt 02's where they overlap (MAPR update 0
`0.02585059206655834`, update 1 `0.0409398324711615`; DIRECT update 6 `0.10711893599150846`, update 7
`0.11702537303517462`). The probe repair therefore did not touch training, sampling or the optimizer:
it changed only what the diagnostic compares. This is the direct evidence that attempt 05 was
outcome-blind with respect to the learning question.

The sealed attempt-05 bundle is what gated the three `PRIMARY` seeds: the runner's `PRIMARY` path
rebuilds the DEBUG gate receipt from the archived `VALID_CLAIM.json` + `RESULT_BODY.json` +
`TELEMETRY_TERMINAL.json` and refuses to start without it.

---

## 22. The three 64-update `PRIMARY` seeds

All three completed, sealed and published the three-artifact bundle. Every §4 integrity item and
every launch condition the recast keeps held in every seed.

Each cell below is the **mean over the 16 worlds of that training size** (2 failed-zone strata x 8
worlds), with the count of positive worlds in parentheses. `R_fail_60` is the primary endpoint.

### 22.1 The primary endpoint, `R_fail_60`

| Seed | MAPR final-minus-initial N=3 | MAPR final-minus-initial N=5 | paired N=7 MAPR-DIRECT | paired N=7 MAPR-BCRH |
| --- | ---: | ---: | ---: | ---: |
| `2026090311` | **+0.060521** (10/16) | **-0.034375** (6/16) | **-0.032917** (1/16) | **-0.157292** (0/16) |
| `2026090321` | **-0.031250** (1/16) | **+0.080104** (9/16) | **+0.107292** (10/16) | **-0.093333** (0/16) |
| `2026090331` | **+0.143646** (14/16) | **+0.128229** (14/16) | **-0.022187** (5/16) | **-0.131354** (3/16) |

### 22.2 Secondary endpoints

`U_total`

| Seed | MAPR f-i N=3 | MAPR f-i N=5 | MAPR-DIRECT N=7 | MAPR-BCRH N=7 |
| --- | ---: | ---: | ---: | ---: |
| `2026090311` | +0.258228 (16/16) | +0.264927 (16/16) | -0.056129 (4/16) | -0.141193 (5/16) |
| `2026090321` | -0.033839 (2/16) | +0.072360 (10/16) | +0.054266 (13/16) | -0.152270 (1/16) |
| `2026090331` | +0.309568 (16/16) | +0.378045 (16/16) | -0.081096 (3/16) | -0.274326 (0/16) |

`U_intact`

| Seed | MAPR f-i N=3 | MAPR f-i N=5 | MAPR-DIRECT N=7 | MAPR-BCRH N=7 |
| --- | ---: | ---: | ---: | ---: |
| `2026090311` | +0.179715 (11/16) | +0.409908 (16/16) | -0.072309 (3/16) | -0.164836 (3/16) |
| `2026090321` | +0.000000 (0/16) | -0.028904 (3/16) | +0.072851 (10/16) | -0.169135 (2/16) |
| `2026090331` | +0.240034 (11/16) | +0.353083 (14/16) | -0.117014 (1/16) | -0.389861 (0/16) |

`J_ext = 0.5*R_fail_60 + 0.5*U_total`

| Seed | MAPR f-i N=3 | MAPR f-i N=5 | MAPR-DIRECT N=7 | MAPR-BCRH N=7 |
| --- | ---: | ---: | ---: | ---: |
| `2026090311` | +0.159374 (15/16) | +0.115276 (14/16) | -0.044523 (4/16) | -0.149242 (2/16) |
| `2026090321` | -0.032545 (2/16) | +0.076232 (10/16) | +0.080779 (13/16) | -0.122802 (0/16) |
| `2026090331` | +0.226607 (16/16) | +0.253137 (16/16) | -0.051642 (7/16) | -0.202840 (0/16) |

### 22.3 Zone strata (the rule's zone-reversal clause)

MAPR final-minus-initial `R_fail_60`:

| Seed | N3z1 | N3z2 | N5z1 | N5z2 | N7z1 | N7z2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `2026090311` | +0.088125 (5/8) | +0.032917 (5/8) | +0.000000 (4/8) | **-0.068750** (2/8) | +0.210417 (7/8) | **-0.119792** (0/8) |
| `2026090321` | **-0.058333** (0/8) | **-0.004167** (1/8) | **-0.004167** (1/8) | +0.164375 (8/8) | +0.000000 (1/8) | +0.068750 (4/8) |
| `2026090331` | +0.156042 (6/8) | +0.131250 (8/8) | +0.201042 (7/8) | +0.055417 (7/8) | +0.157500 (6/8) | +0.100417 (6/8) |

Paired N=7 `R_fail_60` by stratum:

| Seed | MAPR-DIRECT N7z1 | MAPR-DIRECT N7z2 | MAPR-BCRH N7z1 | MAPR-BCRH N7z2 |
| --- | ---: | ---: | ---: | ---: |
| `2026090311` | -0.060417 (0/8) | -0.005417 (1/8) | -0.159375 (0/8) | -0.155208 (0/8) |
| `2026090321` | +0.199167 (6/8) | +0.015417 (4/8) | -0.041667 (0/8) | -0.145000 (0/8) |
| `2026090331` | +0.017500 (1/8) | -0.061875 (4/8) | -0.087500 (3/8) | -0.175208 (0/8) |

Sign reverses **between zone strata within a seed** at N=5 and N=7 in seed `2026090311`, at N=3/N=5
in seed `2026090321`, and in the paired N=7 MAPR-DIRECT contrast in seed `2026090331`.

### 22.4 Validity, comparator competence and instrumentation

| Seed | relabel mismatch MAPR / DIRECT | PS-B0 | common host hard valid | BCRH | action-sensitive N=7 rows | DIRECT residual: nonzero total variation / physical-command changes | batch-position residual (descriptive) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `2026090311` | 0 / 0 | pass | `true` | `IDENTIFIED` | 64/64 | 288/576 nonzero, 0 command | 15/1152 `{N5z2:1, N7z1:6, N7z2:8}` |
| `2026090321` | 0 / 0 | pass | `true` | `IDENTIFIED` | 64/64 | 288/576 nonzero, 3 command | 30/1152 `{N5z1:4, N7z1:7, N7z2:19}` |
| `2026090331` | 0 / 0 | pass | `true` | `IDENTIFIED` | 64/64 | 286/576 nonzero, 1 command | 17/1152 `{N5z1:2, N7z1:8, N7z2:7}` |

Also `true` in all three: `n7_controls_frozen_before_open`, `shadow_boundary_exact`,
`shadow_source_stable`, `observations_complete`, `finite_values`,
`initial_final_checkpoints_retained`, `source_pre_digest == source_post_digest`;
`shadow_influenced_actions` is `false`.

### 22.5 Counts and exposure budget (identical across seeds)

| Quantity | Value |
| --- | ---: |
| training episodes / joint transitions / optimizer steps / evaluation rollouts | 2,048 / 12,288 / 2,048 / 208 |
| evaluation diagnostic forwards, MAPR / DIRECT | 1,152 = 96 x 12 groups / 1,296 = 108 x 12 groups |
| exposure-line rows | 128 (64 updates x 2 arms) |

### 22.6 The exposure line

| Seed | Arm | `||θ0||` | update 0 relative | update 63 relative | AdamW steps/update |
| --- | --- | ---: | ---: | ---: | ---: |
| `2026090311` | MAPR | 33.316665 | 0.024313 | **0.232585** | 16 |
| `2026090311` | DIRECT | 38.652299 | 0.026450 | **0.215438** | 16 |
| `2026090321` | MAPR | 33.316665 | 0.021612 | **0.239145** | 16 |
| `2026090321` | DIRECT | 38.652299 | 0.026860 | **0.210009** | 16 |
| `2026090331` | MAPR | 33.316665 | 0.021606 | **0.223496** | 16 |
| `2026090331` | DIRECT | 38.652299 | 0.026712 | **0.204767** | 16 |

Both learners move monotonically to 20-24% relative parameter displacement over 64 updates, with
matched optimizer exposure (2,048 steps each per seed). §11.4's exposure clause is satisfied.

---

## 23. The reading rule, applied

The rule, transferred verbatim from the recast intake §5, itself transferred verbatim from
`VNFC_BPCR_BEXP_PRESENTATION_SAFE_RETURN_R01_INNOVATOR_INTAKE_20260901.md`:99-114:

> Preliminary support requires at least two of the first three valid seeds to show positive MAPR
> final-minus-initial recovery at both training sizes and positive paired `N=7 R_fail_60` directions
> against each comparator, with active/competent comparators, no persistent zone reversal, and no
> repeated adverse `U_total` or `U_intact` direction. This remains hypothesis-generating.
>
> The exact 64-update proposition is falsified only when common validity, PS-B0, action sensitivity,
> and comparator competence hold and either:
>
> - MAPR has nonpositive final-minus-initial recovery at one or both training sizes in every seed; or
> - MAPR learns at both training sizes but has nonpositive paired `N=7` recovery versus both DIRECT
>   and BCRH in every seed.
>
> Mixed seed signs or zone reversal mean `INSTABILITY/HETEROGENEITY`. Relabel, telemetry, resource,
> native-host, hard-validity, or comparator-competence failure means `INCOMPLETE` or comparator-
> specific `NONIDENTIFIED`, never a scientific null. A valid Class B null does not close the
> direction.

**Precondition — all three seeds are valid.** Common validity (`common_host_hard_valid: true`),
PS-B0 (passed, 0 mismatches), action sensitivity (64/64 N=7 rows sensitive), and comparator
competence (`BCRH: IDENTIFIED`) hold in every seed (§22.4). No relabel, telemetry, resource,
native-host or hard-validity failure occurred: `resources_unmeasured: false` in all four runs and
the relabel mismatch is 0/0 everywhere. The last clause of the rule is therefore **not** triggered;
this is not `INCOMPLETE` and not `NONIDENTIFIED`.

**Clause 1 — preliminary support: NOT reached.** It requires at least two of the three seeds to show
positive MAPR final-minus-initial `R_fail_60` at **both** training sizes *and* positive paired N=7
directions against **each** comparator. Seed by seed:

| Seed | positive MAPR f-i at both N=3 and N=5? | positive paired N=7 vs DIRECT? | positive paired N=7 vs BCRH? | meets clause 1? |
| --- | --- | --- | --- | --- |
| `2026090311` | no (N=5 is -0.034375) | no (-0.032917) | no (-0.157292) | **no** |
| `2026090321` | no (N=3 is -0.031250) | yes (+0.107292) | no (-0.093333) | **no** |
| `2026090331` | **yes** (+0.143646, +0.128229) | no (-0.022187) | no (-0.131354) | **no** |

Zero of three seeds meet it, against a requirement of two. Independently, the clause's own
side-conditions fail as well: zone reversal is present (§22.3) and the paired N=7 `U_intact`
direction is adverse in all three seeds (-0.072309, -0.169135, -0.389861 against BCRH; negative
against DIRECT in two of three).

**Clause 2 — falsification: NOT reached.** Both bullets are conjunctions over *every* seed:

- First bullet — "MAPR has nonpositive final-minus-initial recovery at one or both training sizes in
  every seed": false. Seed `2026090331` is positive at **both** training sizes
  (+0.143646 at N=3, +0.128229 at N=5, 14/16 positive worlds each).
- Second bullet — "MAPR learns at both training sizes but has nonpositive paired N=7 recovery versus
  both DIRECT and BCRH in every seed": false. Its antecedent holds only in seed `2026090331`; seeds
  `2026090311` and `2026090321` do not learn at both training sizes, so the conjunction over every
  seed fails. (In the one seed where the antecedent does hold, the consequent also holds:
  -0.022187 versus DIRECT and -0.131354 versus BCRH.)

The exact 64-update proposition is therefore **not falsified**.

**Clause 3 — governs. `INSTABILITY/HETEROGENEITY`.** "Mixed seed signs or zone reversal mean
`INSTABILITY/HETEROGENEITY`." Both antecedents are satisfied:

- *Mixed seed signs.* MAPR final-minus-initial `R_fail_60` at N=3 is +0.060521, -0.031250, +0.143646
  across the three seeds; at N=5 it is -0.034375, +0.080104, +0.128229. The paired N=7 MAPR-DIRECT
  contrast is -0.032917, +0.107292, -0.022187. Every one of these three quantities changes sign
  across seeds.
- *Zone reversal.* §22.3: within seed `2026090311`, N7z1 is +0.210417 while N7z2 is -0.119792;
  within seed `2026090321`, N3z1/N3z2/N5z1 are negative while N5z2 is +0.164375; within seed
  `2026090331` the paired N=7 MAPR-DIRECT contrast is +0.017500 in z1 and -0.061875 in z2.

**The one direction that is stable across all three seeds** is the comparison against the fixed
controller: paired N=7 MAPR-BCRH `R_fail_60` is negative in every seed (-0.157292, -0.093333,
-0.131354; 0/16, 0/16 and 3/16 positive worlds), and the same holds on `U_total`, `U_intact` and
`J_ext`. The competent bounded receding-horizon controller matches or beats the learner on the
held-out `N = 7` worlds at this budget in every seed. This is the mechanism separation the object was
built to make: per the object's own statement, "if the fixed controller matches or beats the learner,
the host is solved by a rule and the learning question is not yet posed". It is a comparator
observation at a 64-update budget, not a claim that MAPR-4 cannot learn recovery.

**On the MAPR versus DIRECT limb.** DIRECT strictly contains MAPR, so no MAPR edge could have been
representational in any case. The residual-activity flag confirms DIRECT was not degenerate: 286-288
of 576 evaluation rows carry nonzero residual total variation (per-seed maxima 0.579264, 0.647854, 0.581158), with 0, 3 and 1
physical-command changes across the three seeds. So DIRECT distributes differently from MAPR while
almost always commanding the same physical action; the paired MAPR-DIRECT differences reported above
are small and sign-unstable, consistent with the `INSTABILITY/HETEROGENEITY` reading and with no
finite-budget inductive-bias effect being resolvable at 64 updates.

**Scope.** This is a `B/EXPLORE` result. It is preliminary, hypothesis-generating, and specific to
this simulator, these implementations, these three seeds and a 64-update budget. It is not a
stability, superiority, arbitrary-`N`, repeated-churn, general-MARL, permutation-invariance,
transfer, UAV, safety, flight or deployment claim. A valid Class B result of this polarity does not
close the direction.

---

## 24. The batch-position residual at trained checkpoints

Published as a separate descriptive field, `gating: false`, per owner decision F.4(a). Part I §14
listed "whether the 12/192 batch-position residual would persist at trained checkpoints" as a
could-not-verify item. It is now measured.

| Run | decisions | differing | rate | by cell |
| --- | ---: | ---: | ---: | --- |
| `B0-DEBUG` attempt 05 (8 updates) | 576 | 18 | 3.13% | `{N5z1:3, N5z2:2, N7z1:5, N7z2:8}` |
| `PRIMARY` `2026090311` (64 updates) | 1,152 | 15 | 1.30% | `{N5z2:1, N7z1:6, N7z2:8}` |
| `PRIMARY` `2026090321` (64 updates) | 1,152 | 30 | 2.60% | `{N5z1:4, N7z1:7, N7z2:19}` |
| `PRIMARY` `2026090331` (64 updates) | 1,152 | 17 | 1.48% | `{N5z1:2, N7z1:8, N7z2:7}` |

Observations, and only these: the residual **persists at trained checkpoints** and does not vanish
with training; it is concentrated in the larger rosters (`N7z1`/`N7z2` carry 14/15, 26/30 and 15/17
of the differing decisions, and no `N=3` cell ever differs); and its rate varies across seeds by a
factor of two. Split by checkpoint in seed `2026090311`, 10 of the 15 differing decisions are at the
`initial` checkpoint and 5 at `final`.

This is a property of float64 row-wise GEMM arithmetic at different batch positions, identical under
the R01 and R02 presentation laws (Part I §9; `test_batch_residual_is_identical_under_both_laws`).
It gates nothing, and no claim is made from it. It is not evidence about presentation safety, which
is measured separately and is exactly zero in every run.

---

## 25. Resource telemetry (measured; `resources_unmeasured: false` in all four runs)

| Field | `B0-DEBUG` 05 | `2026090311` | `2026090321` | `2026090331` |
| --- | ---: | ---: | ---: | ---: |
| `attempt_disposition` | `VALID_CAPABLE` | `VALID_CAPABLE` | `VALID_CAPABLE` | `VALID_CAPABLE` |
| `end_to_end_wall_seconds` | 118.580 | 624.511 | 689.369 | 583.283 |
| `end_to_end_cpu_seconds` | 131.75 | 705.906 | 782.563 | 655.469 |
| `process_tree_peak_rss_bytes` | 466,690,048 | 926,728,192 | 932,610,048 | 914,251,776 |
| `durable_peak_bytes` | 59,892,006 | 245,297,177 | 245,227,680 | 245,442,808 |
| `scratch_peak_bytes` | 0 | 0 | 0 | 0 |
| `cpu_core_equivalents` | 1.111 | 1.130 | 1.135 | 1.124 |
| `worker_count` / `threads_per_worker` / `peak_process_count` | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |
| `execution_topology` | `SERIAL_NO_CHILD_PROCESSES` | same | same | same |
| runner wall (record) | 119.525 | 626.079 | 691.121 | 584.934 |

Native identity, identical in all four runs and unchanged from Part I §7: `bpcr_backend.dll` build
key `7222d990642a7e4cb010b6526f17acdb3f3aa85f11d1b8d34be0eedbe11e9c99` (equals the frozen literal),
size 213,504 B (equals frozen), image sha256
`adc39faacc60dc13c1572f0098ead13a986c851f2ee121855fb12120e5bc3580` (differs from the frozen
`dadac958…`, recorded, `gating: false`); shadow `vnfc_b_tick_telemetry.dll` key `1327df63…`, sha256
`1656cabbe68ce6af86303173dbfffa246801121f52d21fbce320738031d871a1`, 161,792 B;
`source_native_admission: PREBUILT_FROZEN_LOAD_ONLY_NO_COMPILE`.

Publication seals:

| Run | `RESULT_BODY.json` sha256 / bytes | storage seal sha256 | telemetry sha256 |
| --- | --- | --- | --- |
| `2026090311` | `bd7ed53139d2d49949a6795783ccece2aaca1bb0243d48c5e6b1a6b6372a9ce9` / 241,445,961 | `f72033518f482895c3f5396262ab584b78fc272bc4f66303cf480095425db8b9` | `7aef1e3694072d0f47f869ee746213e4290aa811f18c3745715a01af955c6998` |
| `2026090321` | `2987ffb0143cc23c8e56aa60b9b5f5bb77f71a7bcb04a03da4d1c69ad912b17c` / 241,376,464 | `11eb087171379ae4aac0235df078d541a8ab3bb544be582e827b12be039e7d2a` | `e288514363242b83bae4e6264f36e2cb7ab23b0611ab4a05ec164fad04a5b31f` |
| `2026090331` | `def0cae757fcff8c234915d7bdf9403dbdaeab3590843d2742617c069c2522a5` / 241,591,592 | `76e4e4343ff9d08f85901874223ed94dcf5d928e389086e0d58c3e377407c62f` | `d80b60d3817472b29085e9be732d0274d6a71ca8917a73ff1d915dfeea02188d` |

---

## 26. Deviations in this window, each named

Part I's D1-D7 stand. New:

- **D8 — `B0-DEBUG` attempts 03 and 04 stopped on a frozen accounting constant and stay
  quarantined.** The repaired probe spends two batch-1 forwards per decision instead of one, moving
  `diagnostic_forward_calls` per learned evaluation row from the frozen 48 (MAPR) / 60 (DIRECT) to
  96 / 108. The R01 runner pins that constant in **two** places: per learned row at
  `scripts/run_vnfc_bpcr_b_explore.py:852` (inside `_validate_runtime_payload_cross_consistency`),
  and in the aggregate exposure terminal at `:975` (inside `validate_runtime_terminal` itself, which
  calls the cross-consistency check at `:934` and then continues). Attempt 03 (sha `1ab48e0bc`)
  covered only the per-row constant; attempt 04 (sha `4c7bcc369`) wrapped the cross-consistency
  function, which cannot reach `:975` because `:975` executes after that call returns. Both returned
  `BExploreContractError: exact training/evaluation exposure terminal differs` after 1 m 59.7 s and
  2 m 3.9 s, during terminal construction, **before any result body, endpoint or seal existed**. This
  is an accounting constant made unsatisfiable by an owner-authorised measurement repair, not a
  learner-side instrumentation failure and not a scientific outcome. Both attempts are permanently
  quarantined and were not resumed or salvaged; the fix (commit `b90122e68`) wraps
  `validate_runtime_terminal` — the one entry point all three call sites (`:1517`, `:1779`, `:1977`)
  reach as a module global — asserts the true R02 budget on the real terminal and satisfies the two
  frozen constants on a throwaway copy, so every other frozen check still runs against the real
  terminal. **The published terminal carries the true budget** (§22.5). Attempt 05 is a fresh,
  outcome-blind attempt of the unchanged object under §6.2, and §21 shows its training was
  bit-identical to attempt 02's.
- **D9 — one `PRIMARY` attempt was aborted by the launching shell and stays quarantined.** The first
  launch of seed `2026090311` (preflight 16:10:43.191837Z) was killed at the 10-minute tool timeout
  of the shell that started it. Only `STARTED.json` existed; no result body, no endpoint, no seal.
  This is an operator-side interruption, not a scientific or instrumentation failure. It is
  quarantined at
  `<root>/PRIMARY_2026090311_ABORTED_01/` with an `ABORTED_NOTE.txt`, and the seed was relaunched as
  a fresh attempt under a new root with a fresh preflight. All subsequent runs were launched
  detached so no shell timeout could interrupt them.
- **D10 — one superseded preflight receipt.** The first attempt-05 invocation (receipt
  16:04:53.102920Z) was refused in 2 s by `BExploreContractError: durable root must end with
  RUN_REVISION/stage/seed` — an argument error on my side, before the telemetry sink or any RNG
  master existed. The roots were recreated correctly and a fresh receipt taken at 16:06:24.508416Z.
- **D11 — the deciding numbers are reported as means over worlds, with positive-world counts beside
  them.** The reading rule says "positive MAPR final-minus-initial recovery at both training sizes"
  and "positive paired `N=7 R_fail_60` directions" without naming an aggregation across the 16 worlds
  of a training size. This document reports the arithmetic mean over worlds as the seed-level
  direction, and prints the positive-world count in every cell so the alternative reading is visible.
  The two readings agree on the clause-3 outcome: under a median/majority reading, MAPR f-i at N=5 in
  seed `2026090311` is 6/16 positive (nonpositive), at N=3 in seed `2026090321` is 1/16 (nonpositive),
  and seed `2026090331` is 14/16 at both (positive) — the same seed pattern, so preliminary support
  still fails 0-of-3 and falsification bullet 1 still fails on seed `2026090331`. No cell in §22.1
  changes its sign between the two readings.
- **D12 — `tests/vnfc_bpcr_b_explore_test.py` was omitted from the commit-E suite line.** Commit
  `b90122e68`'s body quotes a four-directory run (8 failed, 327 passed). The whole-direction line in
  §27 below adds that fifth path, matching Part I §6's command.

---

## 27. Suite at the launch sha

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
  --basetemp C:/Projects/HMASD/temp/directions/variable_n_fleet_churn/test/r02_all_f \
  tests/experiments/candidates/variable_n_fleet_churn \
  tests/experiments/candidates/variable_n_fleet_churn_b_explore \
  tests/experiments/candidates/variable_n_fleet_churn_bpcr_r09 \
  tests/experiments/candidates/variable_n_fleet_churn_r02 \
  tests/vnfc_bpcr_b_explore_test.py
8 failed, 360 passed, 1 warning in 179.31s (0:02:59)
```

The 8 failures are the pre-existing canonical-EOL
`SourceManifestError: empirical source manifest bytes are not canonical` failures recorded in
`VNFC_BPCR_BEXP_R01_ENGINEERING_MILESTONE_20260901.md` (2 in `test_fixed_fh_q0.py`, 6 in
`test_empirical_preactivity.py`). They reproduce in isolation at this checkout, are on a frozen
surface this work does not touch, and none is in an R02 file.

---

## 28. Could not verify

- **Whether the `INSTABILITY/HETEROGENEITY` polarity would persist beyond three seeds or beyond 64
  updates.** The budget was three seeds at 64 updates, fixed outcome-blind before launch. Nothing
  here estimates a seed distribution or an asymptote.
- **Why the paired N=7 MAPR-BCRH direction is negative in every seed.** Whether the bounded
  controller is genuinely sufficient for this host, or the learners are budget-starved at 64 updates,
  is not separated by this design. Both readings are consistent with the numbers.
- **Whether the batch-position residual would shrink under a batch-invariant kernel or a different
  BLAS.** Only the shipped float64 CPU path was measured, on one host.
- **The A0 byte-manifest quantities** (Part I §14) remain unproduced; the A0 runner is still
  unfinished. Unchanged by this window.
- **Whether the `bpcr_backend.dll` image-digest mismatch is entirely MSVC image non-determinism.**
  Unchanged from Part I §14.
- **The per-arm relabel mismatch counts of the two quarantined attempts 03 and 04.** They stopped
  before writing the counter. Attempt 05 and the three seeds measure the same quantity on the same
  law and report 0/0 in every case.
- **The 8 pre-existing suite failures** were reproduced but not diagnosed.

---

## 29. Interpretation boundary

The object is consumed with polarity `INSTABILITY/HETEROGENEITY` at `B/EXPLORE`. What may be said:
on this exact two-zone one-unannounced-executor-loss simulator, with the canonical opaque-rank sort
as the presentation law and a like-for-like presentation probe measuring exactly zero presentation
dependence, three seeds of a 64-update budget give sign-unstable MAPR recovery direction across
seeds and across failed-zone strata, no preliminary support and no falsification of the exact
64-update proposition, and a competent fixed bounded receding-horizon controller that is not beaten
on held-out `N = 7` worlds in any seed.

What may not be said: nothing here is a stability, superiority, arbitrary-`N`, repeated-churn,
general-MARL, permutation-invariance theorem, unique-mechanism, transfer, UAV, hardware, safety,
flight, deployment or lifecycle claim. Revision-09 remains consumed and invalid for value
attribution, and the quarantined R01 DEBUG remains unavailable. A valid Class B result of this
polarity does not close the direction.
