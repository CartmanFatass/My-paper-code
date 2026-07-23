# EHC minimal sequence-mediation prototype G1 implementation plan

> **For Project Manager and code workers:** REQUIRED PROJECT SKILL: Use
> `$hmasd-agile-research-development`. Generic Superpowers execution is
> disabled; use the project Skill's proof-sized implementation and verification
> procedure.

```text
active_implementation=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1
implementation_status=PM_ACCEPTED_COMPLETE_NONFORMAL
next_boundary=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION
design=docs/research/designs/EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1.md
backend=cpu
torch_threads=1
formal=false
formal_path_exercise=forbidden
select_result_branch=forbidden
G0_mutation=forbidden
```

**Goal:** Build the smallest independent G1 diagnostic that tests whether the
corrected sequence-mediation measurements separate three counterexample
families without training or consuming a conclusion-bearing iteration.

**Architecture:** A new temporal-duty taskbed owns source dynamics, lifecycle,
reward identity, snapshots and RNG. A separate prototype module owns synthetic
controllers, exact-snapshot interventions and metrics. A thin runner validates
the complete nonformal schema and writes artifacts. No G0 runner, analyzer,
branch selector, audit row or formal artifact is reused.

**Tech stack:** Python 3.11, standard library, NumPy if already available, the
registered CPU interpreter, pytest/unittest-compatible focused tests.

## Global constraints

- Preserve the accepted G1 design exactly; no tuning after result inspection.
- Do not modify G0 environment, event-link module, runner, analyzer or tests.
- Use new seed namespaces beginning at 731001.
- Actor fields are exactly the six frozen fields; tests fail closed on leakage.
- Snapshot branches clone all state/RNG and never copy future outcomes.
- Artifacts are nonformal and cannot enter any formal analyzer.
- No compatibility adapter, legacy reader, migration or fallback.

### Task 1: Independent temporal-duty taskbed

**Files:**

- Create: `ha_ctse_process/temporal_duty_g1.py`
- Create: `tests/ha_ctse_process_temporal_duty_g1_test.py`

**Produces:**

```python
@dataclass(frozen=True)
class G1EpisodeSpec: ...

@dataclass(frozen=True)
class G1Observation:
    actor: tuple[float, float, float, float, float, float]

class TemporalDutyG1Env:
    def observe(self) -> dict[int, G1Observation]: ...
    def step(self, actions: dict[int, int]) -> dict[str, object]: ...
    def snapshot_state(self) -> dict[str, object]: ...
    @classmethod
    def from_snapshot_state(cls, state: dict[str, object]) -> "TemporalDutyG1Env": ...
    def outcome(self) -> dict[str, float]: ...

def make_episode_spec(split: str, roster_size: int, duration: int,
                      sign_start: int, rotation: int) -> G1EpisodeSpec: ...
```

- [x] Write failing tests for the two-step cue, hidden actor fields, JOIN reset,
  LEAVE freeze, REJOIN restore, terminal censoring, duration split, shifted and
  permuted held-out membership, exact logical-to-physical schedule mapping,
  every-active-transition opportunity law, `/4` count normalization, horizon
  censoring, utility range and reward-sum identity.
- [x] Run
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/ha_ctse_process_temporal_duty_g1_test.py -q`;
  observe import/behavior failures.
- [x] Implement only the interfaces above with action domain `{-1,0,+1}` and
  exact snapshot round-trip.
- [x] Re-run the focused test; require all pass.

### Task 2: Controllers and natural trajectories

**Files:**

- Create: `ha_ctse_process/ehc_sequence_mediation_g1.py`
- Create: `tests/ha_ctse_process_ehc_sequence_mediation_g1_test.py`

**Consumes:** `TemporalDutyG1Env`, `G1EpisodeSpec`, and exact snapshots.

**Produces:**

```python
CONTROLLERS = (
    "MECHANISM_CONTROL", "RANDOM_USE", "EXOGENOUS_LIFETIME",
    "LOGIT_WITHOUT_BEHAVIOR", "RECURRENT_CONTROL", "DUM_CONTROL",
)

def primitive_logits(base_logits: tuple[float, float, float],
                     treatment: int, mark: int) -> tuple[float, float, float]: ...
def collect_natural_episode(spec: G1EpisodeSpec, controller: str,
                            seeds: dict[str, int]) -> dict[str, object]: ...
```

- [x] Write failing tests for `base_logits + W_z(m*z)`, DUM `m=0`, recurrent
  no-mark behavior, nondegenerate random use, exogenous renewal, logit-only
  one-step influence, greedy tie-breaking, zero action-RNG draws, natural-row
  provenance and RNG namespace separation.
- [x] Run the focused module and observe expected failures.
- [x] Implement deterministic action selection and controller-owned state/RNG.
- [x] Re-run and require all pass.

### Task 3: Exact-snapshot branches and measurements

**Files:**

- Modify: `ha_ctse_process/ehc_sequence_mediation_g1.py`
- Modify: `tests/ha_ctse_process_ehc_sequence_mediation_g1_test.py`

**Produces:**

```python
def run_event_intervention(snapshot: dict[str, object], controller: str,
                           window: int = 6) -> dict[str, object]: ...
def run_mark_intervention(snapshot: dict[str, object], controller: str,
                          window: int = 6) -> dict[str, object]: ...
def analyze_prototype(records: list[dict[str, object]]) -> dict[str, object]: ...
```

- [x] Add failing tests for outcome-blind `age=3` selection, exact branch-origin
  equality, CRN equality, no future-reference copy, separate event/mark
  contrasts, downstream-window exclusion of the intervention action, finite
  metrics and measurement-tuple-only output.
- [x] Run focused tests and observe expected failures.
- [x] Implement paired continuations and the six named measurement families.
- [x] Re-run and require all pass.

### Task 4: Nonformal runner and fail-closed artifacts

**Files:**

- Create: `scripts/run_ehc_sequence_mediation_prototype_g1.py`
- Create: `tests/run_ehc_sequence_mediation_prototype_g1_test.py`

**Produces:**

```text
python scripts/run_ehc_sequence_mediation_prototype_g1.py --output-dir <path>
  -> prototype_manifest.json
  -> prototype_analysis.json
```

- [x] Write failing tests that recompute the 192-episode inventory, `formal=false`, exact
  design/seeds/source identity, bounded branch count, no G0 identifiers,
  fail-closed malformed records and formal-analyzer rejection.
- [x] Run focused tests and observe expected failures.
- [x] Implement the thin runner and schema validator without training.
- [x] Re-run and require all pass.

### Task 5: Bounded CPU acceptance

**Files:** no tracked-source write during execution.

- [x] Run all three focused test files with the registered interpreter and
  `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`.
- [x] Run one prototype into a new `logs/nonformal_ehc_sequence_mediation_g1_*`
  directory.
- [x] Verify manifest/analysis hashes, `formal=false`, complete cells, finite
  metrics, reward identity, snapshot/CRN validity, `status=COMPLETE`, controller
  provenance and the validated measurement tuple.
- [x] Inspect the path for hidden actor fields, G0 coupling, serial per-row
  tensor transfer, RNG drift and excess persistence.
- [x] Record the smallest CDC delta and let Project Manager select the next
  automatic boundary. This task consumes zero conclusion-bearing iterations.
