Claim: one bounded replay of A03 T0 tape construction on system CPython 3.12.3 with task-isolated NumPy 1.26.3 can establish whether that alternative stack completes this input path, at A/RECON ceiling.
Binding structure: `systems / information flow`.

# FRRIE A04 alternative-stack path — prospective card

This substrate question does not arise from multi-agent partial observability or non-stationarity;
it concerns the addressed input path used by the paired MARL learner.

Status: **PROSPECTIVE / PREPARATION_SELECTED / EXECUTION_UNALLOCATED**.
Object: `FRRIE-R09-A04-ALTERNATIVE-STACK-20260907`.
Authority: P11-FRRIE-A04-PREP-01; A03 intake §4 and standing object-tier delegation.
No installation, A04 invocation or R09 invocation is authorized by this preparation.
Owner item: `docs/research/portfolio/owner/inbox/2026-09-07/20260907-frrie-001.json`
(accept = retain the prepared card; execution remains unallocated).

## 1. Question, evidence and interpretation ceiling

Does the unchanged no-torch/no-tracer T0 workload complete three repetitions on the alternative
stack? The comparator is the **recorded**, failed A03 T0 on uv CPython 3.10.21 plus its cp310
NumPy 1.26.3 wheel. That historical observation is not a concurrent control or independent sample.
No new uv-interpreter arm is selected. Interpreter version/build and NumPy binary ABI both change;
even completion cannot isolate interpreter, wheel or host as the original cause.

The [preparation intake](FRRIE_R09_A04_PREPARATION_INTAKE_20260907.md) records the actual inventory,
authority reconciliation and missing package. A03's `A03_CORRUPTION_WITHOUT_TORCH` reading remains.
**No R09 launch on the A03 substrate until its host/interpreter question is answered.** A04 does
not answer that question by itself or authorize R09 on either stack. R06–R08 mechanism evidence,
the frozen R09 learner/comparator/RNG/budget and historical quarantines remain as recorded.

This is a bounded alternative-path observation, not a hardware health test, unique causal
diagnosis, stability claim, source-defect exclusion, learner result or UAV entry.

## 2. Exact path and protected semantics

- Source: `d6844bb25f6f1030aa7123467935861dcc719450`; the FRRIE candidate tree and A03 runner
  match `50283c9cfffeaba913572fe43f5a8dbf311abe7e` by the preparation's empty Git diff.
- Entry: `scripts/run_frrie_r09_tape_isolation_a03.py`, calling
  `experiments/candidates/finite_resource_relational_inductive_efficiency/tape_isolation_a03.py`.
  Invoke `--arm T0 --repeat 3 --updates 2 --eval-episodes 256`; T0 constructs no evaluation tapes.
  Its raw `summary.json.object` retains the A03 implementation identifier. Record A04 identity
  through this card, its distinct supervisor handle/output root and intake; do not rewrite raw data.
- Host is part of the A04 execution question: `wsl_4070`, `LAPTOP-U9TDKC8A`, Ubuntu 24.04.3,
  WSL2 kernel `6.6.87.2-microsoft-standard-WSL2`, x86_64 CPU. No local/Windows fallback.
- Interpreter: `/usr/bin/python3.12`, observed CPython 3.12.3 / GCC 13.3.0, through dedicated
  `/home/wu/.venvs/hmasd-frrie-system312-a04-20260907/bin/python` (not created by P11).
  Only `numpy==1.26.3`, binary wheel for cp312, is proposed in that environment. Its artifact
  availability and importability are unverified. The shared project and CBSC environments are
  not installation targets. Using uv to create a venv does not select uv's CPython build.
- Preserve root `0000000000000000000000000000000000000000000000000000000000000003`, label
  `FRRIE-B09-CONTACT-BLOCK-003`, roster order `(9,15)*32`, origin schedules, updates 1 and 2,
  horizon 12, addressed RNG, FP32/int64 arrays, and the existing digest/publication code.
- One CPU compute thread, `-X faulthandler`, no torch, pdb, model, optimizer, native adapter,
  checkpoint, tuning, additional seed or fourth repetition. No workload smoke before this probe.

## 3. Primary observation and ordered result rules

Retain the complete setup/probe log, dependency installation outcome, actual interpreter/NumPy
facts, fresh admission, supervisor exit/wall and the existing summary where written. Read the
phase counts/digests, `exception`, `torch_present_at_work_start`, `torch_in_sys_modules`,
`trace_active` and peak RSS. Missing RSS alone is `resources_unmeasured`.

| First matching branch | Reading and resulting recommendation |
| --- | --- |
| `A04_PATH_NOT_OBSERVED` | Required source/host/interpreter, admission, T0-only semantics or single allocation was not met; or setup/import failed before tape work. Report independently trustworthy setup facts and return the exact dependency. No tape or mechanism polarity. |
| `A04_TAPE_FAILURE` | A direct original exception or fatal signal occurred in tape work. Record the first location and completed work; this alternative stack also failed at that exposure. Return the substrate/path question with both failures, without assigning a unique cause. |
| `A04_BOUNDED_INCOMPLETE` | The complete-chain cap or external interruption ended work without three full repetitions and without an observed tape failure. Report completed phases and actual stop; no completion or corruption claim. |
| `A04_CONTENT_DIFFERENCE` | All six 64-tape phases completed, but same-update digests differ across repetitions or from the recorded A03 phase. Report the difference; it may reflect changed numerical/serialization behavior or a defect. No silent-corruption attribution and no R09 portability inference. |
| `A04_T0_PATH_COMPLETED` | Exit 0, all six 64-tape phases completed, no exception, no torch/tracer, and retained same-update digests agree within this run and with the available A03 phases. This one alternative-stack T0 path completed; recommend an explicitly scoped next path decision. No automatic full R09 attempt. |

The A03 phase digests are read from its retained T0 `summary.json`, not regenerated. Here digest
agreement measures this exact addressed-input path; it is not a project-wide numerical gate.

MEI: categorical completion of the declared six phases (384 constructions), beyond A03 T0's
two completed phases, with preserved tape content. No return-scale MEI is applicable to this
path question. Headroom: no tuned same-information host baseline/upper pair is recorded; A04
does not measure it. Above this completion threshold the next recommendation is a bounded
path decision; incomplete work is unresolved; a direct failure supplies contrary path evidence.
The ordered branches above, not that descriptive narrative, control intake.

Prediction: low-confidence `A04_T0_PATH_COMPLETED`; the competing outcome is another tape
failure. Prior Windows completion weakly supports a usable alternative, while the shared
physical host and A03's unresolved cause oppose confidence. No probability of reliability is
inferred. Owner prediction: **not taken (unattended)**.

## 4. Exposure, cost, scope and stops

Tool-produced counts: [preparation counts](FRRIE_A04_PREPARATION_COUNTS_20260907.json).
Proposed work = 1 arm × 3 repetitions × 2 update labels × 2 rosters × 32 episodes = **384
tape constructions**, representing 128 distinct tape inputs repeated three times, not independent
training seeds. The dominant uplink array work is `3*2*32*12*(9^2+15^2) = 705024` addressed
entries, plus detection/base/action/event and origin-schedule work. No trajectory search.
**Exposure: 0 learner updates; 0 optimizer steps; 0 native transitions; 0 native evaluations;
0 model initializations.** The words `training_update` in probe phases label tape inputs only.

Historical phase-time scaling gives 17.73 s of T0 construction from A03's remote completed phases
or 41.33 s from the recorded Windows phase. Neither measures system312 throughput. Installation,
import and final publication costs are unknown and not zero. A single prospective **300 s complete
chain**, including venv creation, one NumPy acquisition/install, admission, import, all tape work
and publication, has a maximum 5 s kill grace: at most **305 s**. No separate setup budget,
automatic retry, extra arm or calibration run. P11 allocates **zero** of these invocations.

This bounded path question is chosen over the multi-arm attribution proposal: a full R09 learner
run still depends on this threatened input path and remains stopped; complete interpreter/wheel/
host separation is unnecessary for A04's claim. If setup exhausts the cap, reconsider the path
question and missing input rather than automatically expanding the cap or adding diagnostics.

Engineering-scope §4: **none needed or added**. Existing digest measurement and supervisor are
reused; no new guard, resume, registry, telemetry, incident machinery or runner. Source additions
and deletions: zero. A later invocation requires the normal fresh on-node memory admission
immediately before T0, with both physical/effective availability at least 4 GiB.

The [five-item handoff](FRRIE_R09_A04_PROSPECTIVE_HANDOFF_20260907.md) is preparation only. Root
returns this candidate to Portfolio for any later explicit execution assignment and collector.

scope: none
