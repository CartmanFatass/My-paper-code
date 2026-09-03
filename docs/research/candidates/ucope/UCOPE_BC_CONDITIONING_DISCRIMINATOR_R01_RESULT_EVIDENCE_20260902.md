# UCOPE BC invertible-conditioning discriminator R01 — attempt record (2026-09-02)

Executed 2026-09-02 by Claude Code (Fable 5.1) against the frozen contract
`UCOPE_B_EXPLORE_FT_XF_BC_INVERTIBLE_CONDITIONING_DISCRIMINATOR_R01_PROSPECTIVE_CONTRACT_20260901.md`
after the owner-approved section 11 recast recorded in `UCOPE_SECTION11_RECAST_INTAKE_20260902.md`,
under decisions 2 and 7 of `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` A.4.

**Question.** Does a target-blind, function-space-matched Cholesky whitening of the Bellman design
(`G = XᵀX/n = LLᵀ`, `z_w = L⁻¹z`, `β̃₀ = Lᵀβ₀`) produce even-support competence in the
`FT-XF-BC-WHITENED` arm where the `FT-XF-BC-RAW` arm remains noncompetent, with a clear paired
whitened advantage at both updates 160 and 320?

**Outcome: no scientific observation.** The attempt failed inside the object's own scientific core
during data preparation, before any optimizer step, and was quarantined under evidence spec §6.2.
Per §6.2 and the repository rule "technical failures create no retry budget and no result polarity",
this attempt has **no polarity**, the object
`UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01` is **not consumed**, and
nothing below may be read as evidence for or against whitening, conditioning, competence,
acquisition or COUNT/RAW. It was not rerun with changes.

| Fact | Value |
| --- | --- |
| Science object | `UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01` |
| Evidence class (intended) | `B/EXPLORE` |
| Attempt status | **`QUARANTINED_INCOMPLETE_ATTEMPT`** — `complete: false`, no polarity, object not consumed |
| Launch commit sha (HEAD at launch) | `ce361d40ac7db9cc8ba7714fee278bb62dbf8793` — "Turn the UCOPE refusals and oracle-competence gate into recorded fields" |
| Failure | `ConditioningTransformError: recorded Gram/Cholesky relation is invalid`, raised at `experiments/candidates/ucope/conditioning_discriminator_r01/conditioning.py:106` |
| Where in the chain | `training.prepare_fold_data` -> `conditioning.build_transform` -> `factor_gram_design` -> `TransformRecord.validate`; before any model, optimizer, target, checkpoint or evaluation existed |
| Interpreter / libraries | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, Python 3.10.20, torch 2.7.0+cpu, CPU |
| Machine | `Windows-10-10.0.26200-SP0`, 16 logical CPUs |
| Topology | `intraop_threads = 1`, `interop_threads = 1`, `deterministic_algorithms = true`, 1 process, 0 child processes |
| Quarantine root (gitignored) | `temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01/quarantine-e52eb2ae834b44089b809ce1d7bbb0db` |

---

## 1. The recast in force, and what it changed about this launch

Both refusals the compliance note's Part B section 5 named as `file:line` gates were exercised as
**recorded fields**, and both would have refused this launch before the recast. They are recorded in
the run manifest and would have been copied into `complete/recast-record.json` had the run
completed; the manifest itself survives in the control root.

| Recorded field | Observed value at this launch | Pre-recast behaviour |
| --- | --- | --- |
| Source cleanliness (`run_ucope_bc_conditioning_discriminator_r01.py:82`) | recorded; `clean` over the bound source inventory at `prepare-run` and at `run`, `git_head = ce361d40ac7db9cc8ba7714fee278bb62dbf8793`, `gating: false` | `raise RunnerRefusal("prepare-run requires clean committed source inventory")` |
| Performance assessment (`:127`) | recorded: `assessment-02.json` resolved, `assessment_id = ucope-bc-conditioning-r01-assessment-02`, schema `UCOPE_BC_CONDITIONING_R01_A_RECON_PERFORMANCE_V2`, **`disposition = PERFORMANCE_READY`** on disk, **`contract_declaration = INVALID_NOT_ADOPTED`** per contract line 561, `gating: false`. `assessment-03` does not exist | `raise RunnerRefusal("manifest assessment-03 binding mismatch")` — the launch was impossible, since the required create-once `assessment-03` does not exist and the existing `assessment-02` is declared ineligible |
| Resource projection caps | carried forward from `assessment-02` as recorded caps with `gating: false`: wall 155.036 s, cpu 622.804 s, RSS 322,667,520 B, scratch 68,157,440 B, durable 67,108,864 B, threads 32, processes 1, child processes 0 | `raise RunnerRefusal("result resource cap exceeded")` |
| Exact-oracle competence predicate | never reached — the attempt died before any policy existed | (recorded, not gating, under the recast) |

**The recast did what it was meant to do: it let this object attempt a launch for the first time.**
What it then met is a defect in the object's own frozen numerical core, which no §11 demotion
touches and which the recast neither caused nor could have prevented.

## 2. Resource admission (a launch condition, unchanged — it passed)

```text
passed                      true
captured_at                 2026-09-03T00:57:58.086806Z
assessed_at                 2026-09-03T00:57:58.142864Z
measurement_source          GlobalMemoryStatusEx
minimum_available_bytes     4294967296
available_physical_bytes    11712937984   (10.91 GiB)
effective_available_bytes   11712937984   (10.91 GiB)
physical_floor_pass         true
effective_floor_pass        true
failure_reasons             []
```

## 3. Commands actually run

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_bc_conditioning_discriminator_r01.py prepare-run
  --manifest    C:/Projects/HMASD/temp/directions/ucope/controls/ucope-bc-conditioning-r01/manifests/result-01.json
  --output-root C:/Projects/HMASD/temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01
```

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_resource_preflight.py admit-memory
  --out C:/Projects/HMASD/temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/result-01.json

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_ucope_bc_conditioning_discriminator_r01.py run
  --manifest          C:/Projects/HMASD/temp/directions/ucope/controls/ucope-bc-conditioning-r01/manifests/result-01.json
  --admission-receipt C:/Projects/HMASD/temp/directions/ucope/controls/ucope-bc-conditioning-r01/admissions/result-01.json
  --output-root       C:/Projects/HMASD/temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01
```

## 4. Verbatim summary lines

`prepare-run` (exit 0):

```text
{"path": "C:\\Projects\\HMASD\\temp\\directions\\ucope\\controls\\ucope-bc-conditioning-r01\\manifests\\result-01.json"}
```

`run` (exit 6):

```text
UCOPE conditioning runner refused: recorded Gram/Cholesky relation is invalid
```

`quarantine-e52eb2ae834b44089b809ce1d7bbb0db/failure.json`:

```json
{
  "object_id": "UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01",
  "complete": false,
  "error_type": "ConditioningTransformError",
  "error": "recorded Gram/Cholesky relation is invalid"
}
```

## 5. Competence observation for this run

**None.** No policy, checkpoint, oracle vector, regret, tail agreement, PROBE rate, dominance count,
branch or reducer output was produced. The attempt ended in `prepare_fold_data`, before the first
optimizer step. Recorded here as the required per-run competence observation: the object produced no
competence observation at all, and none may be imputed.

## 6. The reading rule

The contract's rule (restated unchanged in `UCOPE_SECTION11_RECAST_INTAKE_20260902.md` section 5)
is:

> A positive requires whitened even-support `B_COMPETENT`, raw noncompetence, and a clear paired
> whitened advantage at both updates 160 and 320. The exact falsifier is whitened noncompetence plus
> no clear paired advantage at both checkpoints.

**Not applicable.** The rule takes competence flags and paired-dominance counts as inputs; this
attempt produced neither. There are no deciding numbers because there is no decision. In particular
the falsifier is **not** satisfied: a falsifier requires an observed whitened noncompetence, and
nothing was observed. Recording this attempt as falsifier support would be exactly the "incomplete
attempt read as a consumed object" error the repository rule forbids.

## 7. What failed, measured (post-hoc technical diagnostic, outcome-free)

`TransformRecord.validate` requires the recorded FP32 Cholesky factor to reconstruct the recorded
FP32 Gram within `torch.allclose(L Lᵀ, G, rtol=16·eps_fp32, atol=16·eps_fp32)`, i.e. a tolerance of
`1.9073486328125e-06` (`conditioning.py:104-106`). The frozen comment beside it is explicit that
there is "intentionally no ridge, truncation, retry, or factor repair".

To establish whether this was a seed-specific accident or a property of the frozen object, a separate
throwaway process regenerated **only** the host population and the ordered design matrices and
measured the residual. It constructed no model, optimizer, target, oracle, policy, score, competence,
acquisition or evaluation, and read nothing from the quarantined artifact. It is a numerical
infrastructure measurement, not science, and it produces no polarity.

| seed | fold | stage | rows | dim | `max abs(L·Lᵀ − G)` | max allowed | allclose | cond(G) |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 00 | 0 | tail | 10,240 | 5 | 9.447336e-06 | 3.814697e-06 | false | 7.1538e+02 |
| 00 | 0 | root | 20,480 | 7 | 9.208918e-06 | 3.814697e-06 | false | 5.0231e+03 |
| 00 | 1 | tail | 10,240 | 5 | 9.477139e-06 | 3.814697e-06 | false | 7.2474e+02 |
| 00 | 1 | root | 20,480 | 7 | 9.208918e-06 | 3.814697e-06 | false | 5.0231e+03 |
| 01 | 0 | tail | 10,240 | 5 | 9.685755e-06 | 3.814697e-06 | false | 7.3028e+02 |
| 01 | 0 | root | 20,480 | 7 | 9.208918e-06 | 3.814697e-06 | false | 5.0231e+03 |
| 01 | 1 | tail | 10,240 | 5 | 9.357929e-06 | 3.814697e-06 | false | 7.2724e+02 |
| 01 | 1 | root | 20,480 | 7 | 9.208918e-06 | 3.814697e-06 | false | 5.0231e+03 |
| 02 | 0 | tail | 10,240 | 5 | 9.596348e-06 | 3.814697e-06 | false | 7.2443e+02 |
| 02 | 0 | root | 20,480 | 7 | 9.208918e-06 | 3.814697e-06 | false | 5.0231e+03 |
| 02 | 1 | tail | 10,240 | 5 | 9.119511e-06 | 3.814697e-06 | false | 7.2660e+02 |
| 02 | 1 | root | 20,480 | 7 | 9.208918e-06 | 3.814697e-06 | false | 5.0231e+03 |

Worst residual across all twelve designs: `9.685755e-06`, about **2.4 to 2.5 times** the frozen
tolerance. Every seed, every fold and both stages fail, by a similar margin, deterministically. All
Gram entries are bounded by 1.0, so the `rtol` term contributes at most another `1.9e-06`, giving the
`3.81e-06` ceiling in the table.

Two observations follow directly, and only these two:

1. **The failure is a property of the frozen object at science scale, not of a seed draw, not of the
   recast, and not of concurrency.** The first design attempted (seed 00, fold 0, tail) fails, which
   is why the attempt died 22 s in.
2. **It is consistent with the technical assessments having passed.** `assessment-01` and
   `assessment-02` exercised 40 episodes per context (80 tail rows, 160 root rows) against the same
   validator; the science configuration uses 5,120 episodes per context (10,240 tail rows, 20,480
   root rows) and Gram condition numbers of `7.2e2` (tail) and `5.0e3` (root). An FP32 Cholesky of a
   matrix at that conditioning cannot reconstruct its Gram to `1.9e-06` absolute.

`REVIEWER_INFERENCE`, offered as a hypothesis and not as an observation: the tolerance
`16·eps_fp32` appears to have been calibrated at technical scale and never checked against the
science-scale design, so `UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01` as
frozen is not executable on this platform. Deciding what to do about that — a `REPAIR_REQUIRED`
disposition, a fresh object with a scale-appropriate tolerance derived before any outcome is seen, or
a different conditioning intervention — is a scientific decision for the direction owner and is **not
taken here**. Changing the tolerance and rerunning would be an outcome-informed repair of a frozen
object mid-attempt, which §4.5, §5.2 and the intake's own "non-positive-definite `G` stops rather
than admitting ridge, truncation, or outcome-dependent repair" clause all forbid.

## 8. Resource telemetry (measured; not `resources_unmeasured`)

Captured by the runner's process-tree monitor up to the failure and written into the quarantine
receipt:

```text
wall_seconds                 22.018767499990645
cpu_seconds                  19.422
cpu_core_equivalents         0.8820657196188775
host_cpu_occupancy           0.05512910747617984
process_tree_peak_rss_bytes  266485760      (254.1 MiB)
process_count_peak           1
root_process_count           1
child_process_count_peak     0
thread_count_peak            20
scratch_high_water_bytes     0
durable_high_water_bytes     0
io_read_bytes                14253123
io_write_bytes               0
aggregate_io_bytes           14253123
samples                      51
logical_cpu_count            16
```

End-to-end wall clock for the `run` invocation including interpreter start and the preflight
subprocess: `2026-09-03T00:57:57Z` to `2026-09-03T00:58:21Z`, 24 s. Every telemetry field was
measured, so the decision-7 downgrade path was not exercised and `resources_unmeasured` would have
been `false`. All observed values sit far inside the recorded `assessment-02` caps; no cap
exceedance occurred, so the recast's `cap_exceedances` path was not exercised either.

## 9. Quarantine (§6.2), as performed

```text
temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01/
  quarantine-e52eb2ae834b44089b809ce1d7bbb0db/
    failure.json
    staging/          (empty — nothing had been staged)
    work/             (empty — nothing had been written)
```

No `complete/` namespace exists, no `result.json` was written, and no checkpoint was produced. The
create-once `manifests/result-01.json` and `admissions/result-01.json` remain in the control root as
the record of what was attempted. The attempt was **not** resumed, retried, salvaged or rerun with
changes.

## 10. Deviations

- **D1 — the two recorded fields that used to be refusals.** The clean-source check and the
  `PERFORMANCE_READY` `assessment-03` binding were recorded, not enforced. This is the recast itself
  (decision 2) and is what made the attempt possible at all.
- **D2 — the manifest binds `assessment-02`, which its own contract declares ineligible.** Recorded
  with both facts side by side (`disposition: PERFORMANCE_READY`, `contract_declaration:
  INVALID_NOT_ADOPTED`) and `gating: false`. No assessment was created for this attempt; the contract
  requires an `assessment-03` that does not exist.
- **D3 — a recast manifest format.** `prepare-run` writes
  `UCOPE_BC_CONDITIONING_R01_RESULT_MANIFEST_RECAST_V1` instead of the strict V1 format. It binds the
  same exact scientific configuration, science contract, RNG version, data-ancestry law, batch law,
  transform implementation and zero-effect firewall, and it still detects tampering through the
  binding digest; the strict V1 path is retained in the source unchanged and unused.
- **D4 — `prepare-run` lost its `--assessment` argument.** It resolves the recorded assessment
  itself, because the frozen path it used to require points at a file that does not exist.
- **D5 — output root naming.** The frozen contract fixes the create-once root
  `temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01`, which does not follow the
  `<object>_<date>` convention used for the exposure ladder. The contract's path was kept rather than
  changing a create-once identity.
- **D6 — post-hoc technical diagnostic.** Section 7's residual table was produced by a separate
  outcome-free process after the quarantine. It regenerated only the design matrices, constructed no
  learner and read no quarantined artifact.
- **D7 — concurrency.** The `flexible_skill_duration` E1 study was running two 4-thread processes on
  the same machine. This attempt used 1 intraop and 1 interop thread. The failure is deterministic
  and independent of load.
- **D8 — no native build cache involved, no TMP redirect.** This package touches no C++ extension, so
  the `%LOCALAPPDATA%\Temp\hmasd_*_native` roots the owner cleared were not exercised, and
  `TMPDIR`/`TEMP`/`TMP` were left at their defaults.

## 11. Could not verify

- Anything about whitening, conditioning, competence, arm separation, acquisition or COUNT/RAW. The
  attempt produced no scientific quantity.
- Whether the object would complete if the FP32 Cholesky tolerance were scale-appropriate. That is
  the obvious next question and it is a question for the owner, not something this attempt may test.
- Whether the same tolerance affects any other object. `TransformRecord` is local to
  `experiments/candidates/ucope/conditioning_discriminator_r01/`; no other direction was checked.
- Whether an FP64 Gram/Cholesky, a scale-relative tolerance, or a different whitening construction
  would preserve the contract's function-space-matched initialisation exactly. Not investigated.

## 12. Interpretation boundary

This document records an incomplete attempt and a technical defect. It carries **no** scientific
polarity in any direction. It does not support `PARK`; the independent review's warning that "a
both-arms-noncompetent outcome is not `PARK` support on its own" does not even apply here, because
there was no outcome. It does not consume
`UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01`, which remains registered and
unrun. It establishes nothing about the UCOPE host, the learner packages, paid acquisition, COUNT
versus RAW, variable `k`, variable `N`, MARL, UAV autonomy, transfer, safety or deployment. The only
finding is engineering: as frozen, this object cannot execute at science scale on this platform, and
what to do about that is an owner decision.
