# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Two systems share one directory:

1. **An MARL research codebase** — a PyTorch implementation of HMASD (Hierarchical Multi-Agent
   Skill Discovery, Yang et al. 2023) applied to multi-UAV base-station scenarios, plus several
   later algorithm lineages and 21 current research directions (53 implementation dirs under
   `experiments/candidates/`, since one direction can have several attempts).
2. **A research workflow / evidence layer** — `AGENTS.md`, `.agents/skills/`, `.codex/agents/*.toml`,
   `scripts/hmasd_*.py`, and `docs/research/`. This layer governs how scientific objects are frozen,
   run, and recorded. It is not in the application import graph.

Most day-to-day work follows the second system's conventions even when the edit lands in the first.

## Environment

The project runs on a conda env that is **not** the `python` on PATH (that is a bare system
Python 3.11 without torch). Use the explicit interpreter:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe        # main env: Python 3.10, torch 2.7.0+cpu, pytest 9
C:/Users/fires/.conda/envs/hmasd-science-tools/python.exe  # isolated analysis env (Python 3.11, no torch)
```

The second env is declared in `configs/scientific-capabilities-v1.toml`; query it with
`python scripts/hmasd_science_capabilities.py list|show|doctor [--id <capability>]`. Only
`scientific-python` (symbolic/numerical/tabular/statistical/plotting) and `networkx` are `active`;
`paper-lookup`, `stable-baselines3-reference`, `torch-geometric-probe`, `pufferlib-marl-probe`, and
`wolfram` are declared `unavailable`. Never install into either env to satisfy an analysis need —
report the capability as unavailable and let the owner decide.

## Commands

### Tests

There is no `pytest.ini`, `pyproject.toml`, `setup.cfg`, or `tox.ini`, so pytest is invoked with
explicit paths. (Two `conftest.py` files exist under
`tests/experiments/candidates/finite_resource_relational_inductive_efficiency/` and its `b01/`
subdir; they define fixtures only — no `addopts`, markers, or collection hooks.)

```powershell
# a directional candidate's whole suite
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/experiments/candidates/ucope/

# one file, one test
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/hmasd_run_test.py::test_name

# repo-level product tests
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/ha_ctse_process_stage_c_test.py
```

For anything whose output will be cited as evidence, isolate the temp dir so concurrent runs cannot
collide (some older packets also pass `-p no:cacheprovider`):

```powershell
... -m pytest -q --basetemp C:/Projects/HMASD/temp/pytest_<slug>
```

This is a real practice — hundreds of such directories exist — but it is not a written rule, and the
literal commands quoted in 2026-08-28→09-01 evidence documents are usually the plain
`... -m pytest <paths> -q` form. The dominant `--basetemp` naming today is flat
(`temp/pytest-<slug>` / `temp/pytest_<slug>`) rather than the nested
`temp/directions/<direction-id>/test/<run-tag>` the layout standard prescribes.

**Test file naming is dictated by `.gitignore`, not by pytest.** `test*.py` is globally ignored;
`tests/experiments/**/*.py` is explicitly un-ignored. So:

- `tests/` top level → `*_test.py` (e.g. `hmasd_run_test.py`)
- `tests/experiments/candidates/<impl>/` → `test_*.py`

Using the wrong one silently produces an untracked file.

### Training / running

```powershell
# original HMASD/UAV route
python main.py --mode train --scenario 1 --n_uavs 5 --n_users 50
python main.py --mode eval  --scenario 2 --model_path models/hmasd_model.pt --render

# standalone process-core route (separate config and training loop)
python -m ha_ctse_process.train
python -m ha_ctse_process.smoke
python -m ha_ctse_process.train --preset S7-S1 --scenario energy --n_agents 6 --num_envs 2 `
  --collector_backend subproc --total_timesteps 16 --rollout_length 8 --skill_interval 4
```

Per-direction experiment entry points live in `scripts/run_<direction>_<object>.py` (83 of them).

### What does not exist

No lint, format, or typecheck tooling is configured anywhere (no ruff/flake8/mypy/pylint/pre-commit
config) — that is a deliberate absence, not something to hunt for. There is no dashboard command
either; `scripts/hmasd_dashboard.py` was removed and `scripts/dashboard/` is an empty leftover. And
there is no C++ build step: `envs/native/cpp_extension_cache.py` compiles and caches extensions
through PyTorch's JIT loader on first use, keyed by a source SHA-256 — so the first test or run that
touches a native backend pays a slow implicit compile.

### Mandatory resource preflight

Immediately before **every** result-bearing experiment, resume, retry, or slice:

```powershell
python scripts/hmasd_resource_preflight.py admit-memory --out <receipt.json>
```

`--out` is required. Both physical and effective available memory must be ≥ 4 GiB
(`MINIMUM_AVAILABLE_MEMORY_BYTES = 4 * GIB`); a missing or failed measurement refuses the launch.
Re-check per invocation, before creating RNG masters, models, optimizers, checkpoints, or results.
A passing resource check never overrides a scientific blocker. The script also offers `capture`
(observational only, makes no admission decision) and `assess-run --direction ...` (applies the
frozen reserve/peak formula to a fresh capture).

`scripts/hmasd_run.py prepare|execute|reconcile|cancel|promote` wraps one observed run and its
manifest (plus a hidden `_exec-gate` used internally). `prepare` requires `--direction --run-id
--assignment --code-sha --parameters --estimate --output-root`; `execute`/`reconcile`/`cancel` take
`--manifest`; `promote` takes `--manifest --result-json --result-markdown`.

## Architecture

### Executable lineages (kept deliberately separate)

| Route | Entry | Notes |
| --- | --- | --- |
| Original HMASD/UAV | `main.py` → `config.py` (a shim for `config_1.Config`) → `hmasd/agent.py` | Compatibility surface. |
| Legacy multiprocess | `train_multiproc_config_1.py` | Large single-file legacy/baseline route. |
| Process-core | `python -m ha_ctse_process.train` | Standalone platform, owns its own config. **Must not import `hmasd.agent`, HMASD discriminators, or the HMASD training loop.** Importing generic layer helpers from `hmasd/r_mappo_utils.py` is allowed and done (`standalone_models.py`, `variable_roster_event_models.py`). |
| Research candidates | `experiments/candidates/<impl>/` | Mostly isolated — but see the native boundary below. |
| Alt algorithm lineages | `gnn_hmasd/`, `manifold_hmasd/` | Dormant since 2026-08-20; reachable only via `scripts/rollout_and_collect.py` and `scripts/train_vae.py`, not from any route entry point. |

Shared beneath all of them: `envs/` — subpackages `pettingzoo/` (which itself nests `relay/` and a
C++ source dir), `continuous_roster/`, `native/`, plus a loose `envs/probe_environments.py`.

### Native boundary — plural, and it crosses the isolation line

`envs/native/cpp_extension_cache.py` owns source-keyed C++ extension loading, and two adapters use it
(`envs/continuous_roster/cpp_backend.py`, `envs/pettingzoo/uav_cpp_backend.py`). That is *not* the
whole story, and both `PROJECT_MAP.md` and an earlier draft of this file got it wrong:

- `envs/native/production_backend.py` is a fail-closed capability registry and the de-facto native
  dispatcher. It **lazily imports native loaders out of `experiments/candidates/*`** from inside
  function bodies — roughly ten of them (`semantic_graphon_shared_policy_rscf_r01`,
  `variable_n_fleet_churn_bpcr_r09`, `scdmp_variable_k/*`, `opportunity_normalized_lease_gated_rebinding/*`,
  `renewal_indexed_score_plasticity`, `roster_consistent_latent_exploration_tbcfv`, `vqfp_vnpa_r03`,
  `ucope`). It is exercised by `tests/production_backend_policy_test.py`.
- So `PROJECT_MAP.md`'s "Production routes do not import isolated candidates" is **false** as written.
  Shared `envs/` infrastructure does import candidates. Treat that line as aspirational.
- Most candidates that go native ship their **own** `native_backend.py` / `native_loader.py` with
  bespoke ctypes/subprocess build-and-load code, bypassing `cpp_extension_cache.py` entirely (only
  `semantic_graphon_shared_policy_rscf_gate_a` reuses the shared cache). There is no single native
  choke point.

Dependency direction otherwise: entries wire runners → runners depend on agents, collectors,
environments, and output owners → adapters may call native kernels. Research documents describe
meaning; they never control execution.

### Process-core internals

This is a **~110-file package**, not the tidy dozen-module platform `PROJECT_MAP.md` implies. The
skeleton: `ha_ctse_process/train.py` parses and wires train/eval into `standalone_train_runner.py` /
`standalone_eval_runner.py` (variable-roster work goes to `standalone_variable_roster_runner.py` and
`event_process_runner.py`). Env creation and collection flow through `standalone_cli.py` →
`env_factory.py` → `collectors.py`. Hyperparameters live in `ha_ctse_process/config.py`, which
inherits environment presets from `config_1.Config` but owns the algorithm settings locally. The
agent is composed from `standalone_agent.py` (327 KB, which itself pulls in ~17 further first-party
modules — `intrinsic_rewards.py`, `team_intent.py`, `situation_*.py`, `process_posterior.py`,
`g_info_objective.py`, …), `standalone_models.py`, `standalone_ar_selection.py`,
`standalone_lifecycle.py`, `standalone_low_inference.py`, `standalone_low_update.py`,
`standalone_segments.py`, with `standalone_metrics.py`, `standalone_manifest.py`,
`standalone_contracts.py`, `standalone_event_support.py`, `infrastructure_profiling.py`, and
`plotting.py` around the edges.

**Checkpointing is not single-owner.** `checkpoint_io.py` owns the standard path;
`variable_roster_event_checkpoint.py` independently implements the event/variable-roster payloads and
restores, and is what `event_process_runner.py` and `standalone_variable_roster_runner.py` actually
call. `PROJECT_MAP.md` claims `checkpoint_io.py` owns it solely — it does not.

Note also that `ha_ctse_process/` has accumulated a lot of research-flavored code directly inside it
(`continuous_roster_native_six_g31_*_g4x/g5x.py`, `uav_source_identifiability_g0.py` at 152 KB,
`uav_charge_rotation_g2.py`, `r24_qd_dataset.py`, `r30_fixed_clock.py`, …), which blurs the
"process-core vs. isolated candidate" line the rest of this file draws.

The `subproc` collector runs only env `reset/step` in workers — inference, rollout storage, segment
closure, and PPO/process updates stay in the main process, which is what keeps the algorithm
on-policy. Do not move update work into workers.

### Research-direction layout (the joining key)

There are **21 current candidate directions** (19 ACTIVE, 2 PARKED as of 2026-09-01), inventoried in
`docs/research/RESEARCH_MAP.md` and mirrored row-for-row in `docs/research/portfolio/PORTFOLIO.md`.
A further **14 structurally closed or absorbed** labels are indexed separately under
`docs/research/legacy/directions/`. 21 + 14 = 35 labels have ever existed, which is where
`PROJECT_MAP.md`'s "35 direction keys / 35-row inventory" phrasing comes from — that phrasing is
stale, since RESEARCH_MAP.md's table now holds only the 21.

The directory name under `docs/research/candidates/` is the stable **direction id** and joins four
surfaces:

| Surface | Path | Versioned? |
| --- | --- | --- |
| Science definitions, contracts, result evidence | `docs/research/candidates/<direction-id>/` | yes |
| Implementation | `experiments/candidates/<impl>/` | yes |
| Tests | `tests/experiments/candidates/<impl>/` | yes |
| Run/checkpoint/profile output | `temp/directions/<direction-id>/exp/` | no (ignored) |
| Pytest bases, fixtures, compiler probes | `temp/directions/<direction-id>/test/` | no (ignored) |

`<impl>` frequently differs from the direction id — `variable_n_fleet_churn` →
`variable_n_fleet_churn_bpcr_r09`, `commitment_residual_triggered_options` →
`commitment_residual_triggered_options_common_history_gate_r01`,
`degraded_incumbent_shadow_handover` → `..._rbhr_r06`, `roster_consistent_latent_exploration` →
`..._tbcfv`. Some directions nest one level deeper and break the flat mapping entirely:
`semigroup_consistent_duration_model_policy` → `experiments/candidates/scdmp_variable_k/<sub>/`
(seven sibling sub-implementations) and `ucope` → `experiments/candidates/ucope/<sub>/` (three).
`docs/research/RESEARCH_MAP.md` is the single inventory of that mapping — read it before guessing a
path, and update it (not `PROJECT_MAP.md`) when a direction's primary implementation or test path
changes. It can lag the working tree: in-flight CBSC work under
`experiments/candidates/capability_bound_semantic_currentness/omrc_b01/` is not in RESEARCH_MAP.md
yet, and its tests are flattened to
`tests/experiments/candidates/capability_bound_semantic_currentness_omrc_b01/` rather than mirroring
the nesting. Check both spellings before creating a test directory.

Inside a direction directory, `DIRECTION.md` (the scientific position) is the one universal file.
The dominant recurring type is `*_SCIENCE_CARD*.md` — one frozen definition per attempted scientific
object. Result evidence arrives as dated `*_RESULT_INTAKE_<date>.md` and `*_TECHNICAL_ACCEPTANCE.md`
files, and external-review rounds as an intake family (`*_INNOVATOR_INTAKE_<date>.md`,
`*_CONVERGENCE_DECISION_INTAKE_<date>.md`, `*_REVISION_REQUIRED_INTAKE.md`, `*_CLOSED_INTAKE.md`).
About 9 of the 21 directions also carry a `CODE_SCIENCE_INDEX.md` (claim → stable symbols → focused
evidence table) and roughly a third an `IMPLEMENTATION_THRESHOLD.md`. A newer
`*_PROSPECTIVE_CONTRACT_<date>.md` / `*_RESULT_EVIDENCE_<date>.md` pair appeared 2026-08-31/09-01
alongside `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`; it is the emerging standard, not yet
repo-wide.

### Navigation

| Question | File |
| --- | --- |
| Stable code architecture, dependency direction | `docs/project/PROJECT_MAP.md` |
| The 21 directions, position, code/test paths | `docs/research/RESEARCH_MAP.md` |
| Lifecycle, priority, owner, capacity | `docs/research/portfolio/PORTFOLIO.md` |
| Exact scientific meaning of a direction | that direction's `DIRECTION.md` and cited evidence |
| Collaboration/authority model, Git and push policy | `AGENTS.md` |
| Evidence class / rigor tier a claim needs | `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` |
| Parked defects and open questions that block interpretation | `docs/project/PROBLEM_CACHE.md` |
| Measured throughput numbers and their conditions | `docs/project/EFFICIENCY_PRACTICES.md` |
| Rules those numbers support | `docs/project/ENGINEERING_ADDITIONS.md` |
| Closed/absorbed directions | `docs/research/legacy/directions/` |

## Working rules specific to this repo

**Scientific integrity.** Do not silently change scientific meaning, numerical precision, RNG
behavior, checkpoint format, bit identity, a declared comparison, or external side effects. State
material assumptions; distinguish observation from inference.

**Incomplete attempt ≠ consumed object.** A launch or artifact that omits required prospective
instrumentation, resource observation, or any other part of the frozen assignment is an incomplete
implementation. Quarantine it — do not interpret, resume, or salvage it. Only a valid *completed*
assignment consumes a scientific object; technical failures create no retry budget and no result
polarity. An outcome-informed redesign is a different scientific object.

**Workflow-layer edits are handled directly, not delegated.** `AGENTS.md` §"Workflow-task routing"
restricts `$hmasd-workflow-outsource` to cases where the user explicitly names it or explicitly asks
for outsourcing/delegation; otherwise the current agent makes ordinary workflow/control-plane changes
and audits itself. Do not reach for it on your own initiative.

**`.gitignore` is a denylist — check before creating files.** Two tiers:
`*.md`, `*.txt`, `test*.py`, and `temp/**` are ignored with a long hand-maintained allowlist of `!`
re-includes; `*.csv`, `*.png`, `*.pdf`, `*.pt`, `models/`, `results/`, `logs/`, and `runtime/` have
no re-includes at all, so nothing under those ever enters Git. A new document under an un-allowlisted
path is invisible. Run `git check-ignore -v <path>` when adding anything new. (This file is one such
case — root `CLAUDE.md` matches `.gitignore:47`, the `*.md` rule.)

**Line endings.** `.gitattributes` pins `text eol=lf` on byte-addressed authorities: everything under
`docs/research/portfolio/`, each `DIRECTION.md`, `docs/research/candidates/**/workflow/**/*.json`,
`docs/external-review/directions/**`, `docs/migration/*.md`, `/.codex/**`, `/.agents/**`,
`/AGENTS.md`, `/CONTEXT.md`, `scripts/hmasd_*.py`, `scripts/schemas/hmasd_*.schema.json`,
`tests/hmasd_*.py`, the `tests/fixtures/hmasd_{external_review,phase0,science}` fixture sets, and the
two VNFC science cards a native loader byte-addresses. Do not normalize those endings by hand.

**Performance defaults are measured, not assumed — and CPU is not universally valid.** At the
measured model size (~15k params, batch 16, ~480 sequential kernel calls per epoch) CPU single-thread
beats CUDA by ~2.7–2.9x and beats 14 CPU threads by 1.5x, so `torch.set_num_threads(1)` is the right
default for small tensors; one CUDA card saturates near 2.0x across concurrent processes; prefer
batching replicas as a dimension inside one verified process over one-process-per-replica. Two
caveats before acting on that: the numbers were taken **2026-07-21 on `torch 2.7.0+cu118` / RTX 4070
(WDDM)** and have not been refreshed since, and neither declared conda env has CUDA available today,
so the comparison cannot be re-verified in-repo. More importantly, CPU is sometimes *scientifically*
invalid rather than merely slower — `docs/project/PROBLEM_CACHE.md` P1b documents a frozen contract
where CPU fork reconstruction is not bitwise-exact (float32 reduction order, 4.768e-07 against a
1e-6 tolerance) and CUDA is the registered backend. Check the contract before switching device.

**Git.** Commits made for an authorized task are pushed immediately to the configured upstream; see
`AGENTS.md` for the full policy, including the Windows-specific rule that Git pushes must run outside
the default Codex sandbox (the sandboxed HTTPS helper crashes without a diagnostic).

**Scratch files** belong under `temp/directions/<direction-id>/{exp,test}` (ignored). That is the
intended target, not a description of reality: as of 2026-09-01 the repo root also carries ~30 stale
`.tmp_pytest_*` / `.pytest_tmp_*` directories plus a `.tmp/` tree of ad hoc per-task subdirectories,
and `temp/` itself has loose entries outside `temp/directions/`. Do not add to the sprawl — pass
`--basetemp` explicitly rather than trusting defaults.

## Known staleness

`CONCEPT_MAP.md` and `LEARNING_LOG.md` are the user's personal learning documents, not project
authorities. `CONCEPT_MAP.md`'s concepts 1–6 describe an entire task-database / lease-registry /
return-witness control plane that **no longer exists**: `scripts/hmasd_state.py`,
`hmasd_work_packet.py`, `hmasd_worktree.py`, `hmasd_external_review.py`, `hmasd_codex_tasks.py`,
`hmasd_protocol_contracts.py`, `docs/project/WORKFLOW_PROTOCOL.md`,
`docs/project/git-path-policy-v1.json`, and the `hmasd-slice-interface` / `hmasd-git-integration`
skills are all gone, along with `registry.json`, per-direction `state.json`, and the `work_id` /
"return witness" vocabulary. `AGENTS.md` was rewritten to a much simpler model with no
repository-internal task database, lease registry, or approval gates — trust it over any older
description of the workflow layer. Concepts 7–8 (training determinism, cost model) still describe
live code.

`CONTEXT.md` is referenced as a tracked, `eol=lf`-pinned file by both `.gitignore` and
`.gitattributes`, but does not exist at repo root — a leftover of the retired handoff-document
convention.
