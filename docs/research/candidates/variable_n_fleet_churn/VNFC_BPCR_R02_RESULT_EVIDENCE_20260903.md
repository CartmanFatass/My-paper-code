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
