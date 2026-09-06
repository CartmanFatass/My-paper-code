# FRRIE R09 third-root failure chain — read-only engineering map

Scout: Grok Build CM map on detached worktree `43eec21e9584c83e5e8d940402d7e4570b454e59`.
Compared against current `main` at `C:/Projects/HMASD` (`dda8eeaab4df9bfc244a5f94bec095d1d8f5363d`).
No source repairs. No runner, training, native build, or remote command.

---

## 1. `tapes.py` at 43eec21e: `canonical_bytes`, `block`, `uniform_float32`, `evaluation_tape`, and the `tuple_iterator` field object

Failing module: `experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/tapes.py` (253 lines).

### What the four functions do

`R02EvaluationAddress` is a frozen slotted dataclass of the evaluation-draw coordinate (seed label, roster, episode, kind, optional basin/event/slot/role/sender/receiver, draw). `validate()` checks membership and kind-specific field presence, then returns `self`.

```42:97:experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/tapes.py
@dataclass(frozen=True, slots=True)
class R02EvaluationAddress:
    seed_label: str
    roster: int
    episode: int
    kind: str
    basin: int | None = None
    event_ordinal: int | None = None
    slot: int | None = None
    public_role: int | None = None
    role_local_index: int | None = None
    sender: int | None = None
    receiver: int | None = None
    draw: int = 0
    ...
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes({
            "schema": "FRRIE_B01_EVALUATION_ADDRESS_V1", **asdict(self.validate()),
        })
```

- **`canonical_bytes`** (L94–97): validates `self`, serializes it with stdlib `dataclasses.asdict`, prefixes schema `FRRIE_B01_EVALUATION_ADDRESS_V1`, and canonical-JSON-encodes the dict (`canonical_json_bytes` in `b01/contract.py` L33–38 is `json.dumps(..., sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")`).
- **`block`** (L106–110): SHA-256 of `b"FRRIE-B01-EVALUATION-RNG-V1\0" + root + address.canonical_bytes() + retry.to_bytes(4, "big")`.
- **`uniform_float32`** (L112–113): first three bytes of `block(address)` interpreted as an integer, scaled by `1/2**24`.
- **`evaluation_tape`** (L184–221): builds one `R02EvaluationTape` for `(root, seed_label, roster, episode)`. Event slots are drawn with `rng.integer`; then for each `slot × sender` it fills base/action (and detection when `role < 2`) uniforms, then the `slot × sender × receiver` **uplink** uniforms. The A01 traceback is the uplink assignment at L216.

```184:218:experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/tapes.py
def evaluation_tape(
    root: bytes, *, seed_label: str, roster: int, episode: int,
) -> R02EvaluationTape:
    rng = R02EvaluationRNG(root)
    ...
            for receiver in range(roster):
                uplink[slot, sender, receiver] = rng.uniform_float32(
                    _address(**common, receiver=receiver, kind="uplink_uniform")
                )
```

`_address` (L178–181) constructs `R02EvaluationAddress(...).validate()` and returns that instance. That instance is what `block` → `canonical_bytes` later passes to `asdict`.

### Object passed to `dataclasses.asdict` at line 96

Line 96 is `**asdict(self.validate())`.

- Argument: `self.validate()`, which is `return self` (L92).
- Class: `R02EvaluationAddress`.
- Import of `asdict`: `from dataclasses import asdict, dataclass` (L6). The module does not import `fields`. A local import probe on these bytes showed `tapes.asdict is dataclasses.asdict` and no module name `fields`.

A01 postmortem agrees: `type(obj).__name__ == 'R02EvaluationAddress'`.

### Shadowing / monkeypatch / iterator-passed-as-instance

Static scan of this module and the names it imports:

| Check | Result |
| --- | --- |
| `dataclasses.fields = ...` anywhere under the worktree | no matches |
| `fields` attribute / property / ClassVar on `R02EvaluationAddress` | none; `@dataclass(frozen=True, slots=True)` generates `__slots__` and `__dataclass_fields__` only |
| `dir(addr)` names containing `field` | `__dataclass_fields__` only |
| `hasattr(R02EvaluationAddress, "fields")` | `False` |
| Iterator passed to `asdict` | no. Caller is `asdict(self.validate())` on a dataclass instance |
| Local `fields = ...` in this module | none (a tuple named `fields` exists in `collector.py` L41, a different function, not imported here) |

`__slots__` on the class is the tuple of the 12 field names. `iter(that_tuple)` is a `tuple_iterator`. Nothing in this module iterates `__slots__` into `asdict`.

CPython 3.10 `fields()` / `_asdict_inner` (local 3.10.20 `dataclasses.py`; A01 traceback line numbers match 3.10.21):

```1196:1202:C:/Users/fires/.conda/envs/hmasd-amd-cpu/lib/dataclasses.py
        fields = getattr(class_or_instance, _FIELDS)
    except AttributeError:
        raise TypeError('must be called with a dataclass type or instance') from None
    ...
    return tuple(f for f in fields.values() if f._field_type is _FIELD)
```

```1241:1246:C:/Users/fires/.conda/envs/hmasd-amd-cpu/lib/dataclasses.py
def _asdict_inner(obj, dict_factory):
    if _is_dataclass_instance(obj):
        result = []
        for f in fields(obj):
            value = _asdict_inner(getattr(obj, f.name), dict_factory)
```

A01: `_asdict_inner` L1245 `getattr(obj, f.name)` with `f` a `tuple_iterator`. Stdlib `fields()` only includes objects whose `_field_type is _FIELD`. A builtin `tuple_iterator` has no `_field_type`; iterating it inside `fields()` would `AttributeError` *inside `fields()`*, not at L1245. A01's class inventory (`type(obj).__dataclass_fields__`) was 12 proper `Field` entries, matching the class definition.

### Why `_asdict_inner` could see a `tuple_iterator` as `f`

The stdlib line that *would* bind `f` to a `tuple_iterator` is `_asdict_inner` L1244, `for f in fields(obj):`, **if and only if** `fields(obj)` yielded a `tuple_iterator` as an element, or the name `fields` in `dataclasses` was not the stdlib function.

No line in these launch bytes does that:

- L96 is the only `asdict` call. It passes a validated `R02EvaluationAddress`.
- Nothing patches `dataclasses.fields`.
- The class field dict is a normal 12-`Field` mapping; instance `__dataclass_fields__` is the class dict (`addr.__dataclass_fields__ is type(addr).__dataclass_fields__` on these bytes).
- `evaluation_tape` completes the event-time loop (L188–195, each `integer()` → `block` → `canonical_bytes` → `asdict`) *before* the uplink assignment at L216. For roster 9 that is at least six successful `asdict` calls on the same class, plus base/action (and detection when `role < 2`) for the current sender, before any uplink `asdict`. A static “this class’s `fields()` always yields a `tuple_iterator`” explanation is incompatible with reaching L216.

**No static explanation exists in these bytes** for a `tuple_iterator` field object. The single call site is L96; it does not pass an iterator. The observation is a runtime local in `_asdict_inner` that these sources do not construct.

Local Windows CPython 3.10.20 probe on these exact bytes: `dataclasses.asdict` on an R09 uplink `R02EvaluationAddress`, and `evaluation_tape(root=bytes.fromhex("00"*31+"03"), seed_label="FRRIE-B09-CONTACT-BLOCK-003", roster=9, episode=0)`, both succeeded (`uplink_uniform.shape == (12, 9, 9)`). That is this host/interpreter, not the A01 WSL 3.10.21 process.

Sibling `b01/tapes.py` L93–94 uses the same `asdict(self.validate())` pattern on `B01EvaluationAddress` (same 12 fields, same frozen slots).

---

## 2. Ordinary (non-pdb) path vs A01 AttributeError; native/ctypes/torch before `evaluation_tapes`

### Same construction path

Yes. Ordinary R09 and A01 share the same entry and `execute` prefix.

```1:9:scripts/run_frrie_b01_contact_r09.py
"""Module entry point for the frozen FRRIE R09 third-root object."""

import sys

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import main


if __name__ == "__main__":
    raise SystemExit(main([*sys.argv[1:], "--seed", "3"]))
```

A01 wraps that with `python -X faulthandler -m pdb -c continue -m scripts.run_frrie_b01_contact_r09 ...`. `-c continue` runs until the first exception; it does not skip `evaluation_tape`.

`main` always calls `execute` (L560). Seed 3 is applied inside `execute` before tapes:

```159:175:experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/experiment.py
    if seed == 2:
        root_hex, seed_label, adam_lr = f"{seed:064x}", "FRRIE-B07-CONTACT-BLOCK-002", 0.003
    if seed == 3:
        root_hex, seed_label, adam_lr = "0000000000000000000000000000000000000000000000000000000000000003", "FRRIE-B09-CONTACT-BLOCK-003", 0.003
    if role_column_cut:
        seed, root_hex, seed_label, adam_lr = 1, ROOT_HEX, SEED_LABEL, 0.003
    root = bytes.fromhex(root_hex)
    evaluation_tapes = {
        roster: tuple(
            evaluation_tape(
                root, seed_label=seed_label, roster=roster, episode=episode,
            )
            for episode in range(eval_episodes)
        )
        for roster in ROSTERS
    }
    output_root.mkdir(parents=True, exist_ok=True)
```

`ROSTERS = (9, 15)` and production `PRODUCTION_EVAL_EPISODES = 256` (`semantics.py` L24–27). Ordinary R09 is not `--test-only`, so it builds 256 tapes per roster. Output mkdir is **after** this dictcomp. A01’s missing output directory is exactly this order. The AttributeError **can** be the first Python exception on the ordinary path as well.

### `execute()` body before L166 — no native32 / ctypes.CDLL / torch op

Reached in order: absolute-path check (L150–151), `_load_admission` (JSON + `validate_resource_receipt`, pure Python, `b01/contract.py` L76–101), `time.perf_counter`, seed/root/label/LR locals, `bytes.fromhex`. No adapter, no model, no `import torch` at L199 yet.

Native build/load is **after** tapes and mkdir:

```175:178:experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/experiment.py
    output_root.mkdir(parents=True, exist_ok=True)
    launch_sha = _launch_sha()
    torch_threads = None
    adapter = _build_adapter()
```

```130:132:experiments/candidates/finite_resource_relational_inductive_efficiency/b01/r128_smoke.py
def _build_adapter() -> Any:
    build_package_native_artifact()
    return load_package_native_adapter(named_compute_profile())
```

`build_package_native_artifact` / `ctypes.CDLL` live in `native_adapter.py` L248 and L500. They are not called before L166. Original R09 left no output directory, so L175+ did not complete.

`import torch` / `torch.set_num_threads(1)` is `execute` L199–202, after adapter construction.

### Import-time loads reached before `execute` (hence before `evaluation_tapes`)

Runner L5 `from ...b01_contact_r02 import main` → `__init__.py` L3 → `experiment.py` module imports. Those **do** run before L166.

Every native32 / ctypes / torch-extension **site** on that import graph:

| Site | file:line | What actually runs at import | CDLL / build / torch op? |
| --- | --- | --- | --- |
| Torch C-extension load | `policy.py:20–21` (`import torch` / `from torch import nn`) | Yes. `experiment` imports `.semantics` (`FRRIEActorCritic`) and `r128_smoke` (`make_actor_critic`); both import `policy` | Library load only. No `torch.*` op |
| `import ctypes` | `native_adapter.py:10` | Yes. `experiment` → `r128_smoke` L16 `from ..native_adapter import build_package_native_artifact, load_package_native_adapter` | Import only |
| `import ctypes` + `ctypes.Structure` subclasses | `native/native_abi.py:11` and L75+ (`class _PackedPOD(ctypes.Structure)`); pulled in by `native_adapter` L23 and `native_batch` | Yes, type objects | No `CDLL` |
| `ctypes.CDLL(str(artifact_path))` | `native_adapter.py:500` | Only inside `load_package_native_adapter` | **Not reached** |
| `build_package_native_artifact` (c++/cl compile or retain) | `native_adapter.py:248` | Only inside `_build_adapter` | **Not reached** |
| `ctypes.windll.kernel32.GetShortPathNameW` | `native_adapter.py:143–145` | Only Windows build helper | **Not reached** (and A01/R09 were Linux WSL) |
| `import torch` in `execute` | `experiment.py:199` | After tapes | **Not reached** |
| `import torch` in `ContactActorCritic.project_beta` | `semantics.py:43` | Method body | **Not reached** |
| `hashlib.sha256` | `tapes.py:107` | During `evaluation_tape`, not before the dictcomp | C call **on** the failing path |
| numpy C API | `tapes.py` / `experiment.py` `import numpy as np` | Import-time numpy extension load | Not native32/ctypes/torch |

**Listed-category calls reached before `evaluation_tapes` in `execute`:** none of native32 load/build, none of `ctypes.CDLL`/ABI, none of a torch op. The only listed-category *load* before that point is `policy.py:20` `import torch`.

### Can AttributeError be first, or is SIGSEGV before it plausible?

- **AttributeError can be first in `execute`:** the ordinary body has no native32/ctypes.CDLL/torch-op before L166; A01 died at L166’s `evaluation_tape` uplink `asdict` with no output directory.
- **Plausible SIGSEGV *before* tapes:** import-time `policy.py:20` libtorch load (and numpy’s C extension). A01’s traceback shows that import completed (it reached `tapes.py:216`). Original R09 wall was 16 s; A01 was 19 s. Production tape construction is ~256×2 full `evaluation_tape`s (order 10^6 SHA-256/`asdict` calls). That duration matches dying *during* tapes more closely than dying at import.
- **Plausible SIGSEGV *on* the tape path, still before any native32 adapter:** `hashlib.sha256` (`tapes.py:107`) and numpy stores inside `evaluation_tape`. Those are C, not the package native32 artifact. They do not run *before* `evaluation_tapes`; they run *inside* it. They are not a site that would skip the AttributeError by crashing earlier than L166’s dictcomp — they are the same dictcomp.
- Native32 compile/`CDLL` cannot explain original exit 139 **as a pre-tape event**: those calls are after mkdir, and mkdir never happened.

---

## 3. `43eec21e` vs current `main` (`dda8eeaab`)

Command (from `C:/Projects/HMASD`): `git diff --numstat 43eec21e..main -- <paths>` and blob `git rev-parse <rev>:<path>`.

`43eec21e` is not an ancestor of `main` (merge-base `75b934658c4c01e13bd3206498fa49c6d183c3fd`). `git log 43eec21e..main -- <file>` therefore lists the parallel mainline R06–R09 commits that introduced the same paths. **Net file bytes are identical.**

| Path | added | deleted | blob 43eec21e / main |
| --- | --- | --- | --- |
| `b01_contact_r02/tapes.py` | 0 | 0 | `6be41b2ec6f4c4f28623590caa9af762487a86d8` both |
| `b01_contact_r02/experiment.py` | 0 | 0 | `00a494a594db06ab309a994f157d4384b9f656fa` both |
| `scripts/run_frrie_b01_contact_r09.py` | 0 | 0 | `1b5b9d16146420857fe81b7a1cce9a80f964727e` both |
| `native_adapter.py` (native build helper) | 0 | 0 | `20456c9e5fbd432914447fe5915c01c4778de398` both |

Also identical (0/0): `b01/tapes.py`, parent `tapes.py`, `b01/r128_smoke.py` (`_build_adapter`).

**Main does not contain a change that would alter L96 `asdict(self.validate())` or field handling.** There is no quote of a main-side fix: the failing line is the same bytes.

Unrelated FRRIE files *did* change on `main` (`b01/b4_induction_pilot.py`, `b01/checkpoint.py`, `b01/trainer.py`, `b01/training_runner.py`, `b01/training_shards.py` and their tests). Those are not on the R09 pre-mkdir `evaluation_tape`/`asdict` path.

---

## 4. Which pdb command produced `FIELD_TYPES`, and expressions that capture address + field-iteration state

A01 stdin is `FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt`, redirected in `FRRIE_R09_SEGFAULT_A01_COMMAND_20260905.txt` L8 (`... -m pdb -c continue -m scripts.run_frrie_b01_contact_r09 ... < .../FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt`).

```1:9:docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt
where
p ("FIELD_TYPES", type(obj).__name__, type(f).__name__, getattr(f, "name", None))
p ("FIELD_INVENTORY", [(k, type(v).__name__, getattr(v, "name", None)) for k, v in type(obj).__dataclass_fields__.items()])
up 2
p ("ADDRESS", self.seed_block, self.purpose, self.roster, self.update, self.episode, self.basin, self.event_ordinal, self.slot, self.public_role, self.role_local_index, self.sender, self.receiver, self.kind, self.draw)
up 6
p ("COUNTERS", number, update, paired_updates, adam, backward, training_slots)
where
q
```

**`FIELD_TYPES` is command 2** (`p ("FIELD_TYPES", type(obj).__name__, type(f).__name__, getattr(f, "name", None))`), run in the `_asdict_inner` postmortem frame. Terminal log L80: `('FIELD_TYPES', 'R02EvaluationAddress', 'tuple_iterator', None)`.

Command 3 is the class inventory (12 `Field`s). Command 4 `up 2` lands on `canonical_bytes` (`self` is the address). Command 5 then prints **B01 training-tape** names (`seed_block`, `purpose`, …) which `R02EvaluationAddress` does not have → `AttributeError: 'R02EvaluationAddress' object has no attribute 'seed_block'` (terminal L84). Command 6 `up 6` from there is `execute` L166, where `number` does not yet exist → `NameError` (terminal L87).

Intake’s proposed next capture (`FRRIE_R09_SEGFAULT_A01_INTAKE_20260905.md` L117–120): *“capture of the actual evaluation address and the local field-iteration state at this observed serialization failure”*. Existing commands assumed a different address shape.

### Expressions that work against these bytes

Crash frame is `_asdict_inner`; `obj` is the address; `f` is the loop local; `fields` is the stdlib function name in that module.

**Address (stay in `_asdict_inner`, or `up 2` onto `canonical_bytes` and use `self`):**

```text
p ("ADDRESS", obj.seed_label, obj.roster, obj.episode, obj.kind, obj.basin, obj.event_ordinal, obj.slot, obj.public_role, obj.role_local_index, obj.sender, obj.receiver, obj.draw)
p obj
```

Equivalent on `canonical_bytes` after `up 2`:

```text
p ("ADDRESS", self.seed_label, self.roster, self.episode, self.kind, self.basin, self.event_ordinal, self.slot, self.public_role, self.role_local_index, self.sender, self.receiver, self.draw)
p self
```

**Field-iteration local state (must be the `_asdict_inner` frame):**

```text
p ("F_LOCAL", f, type(f), type(f).__name__, id(f), getattr(f, "name", None), getattr(f, "_field_type", None))
p ("FIELDS_FN", fields, getattr(fields, "__module__", None), getattr(fields, "__name__", None), id(fields), fields is __import__("dataclasses").fields)
p ("FIELDS_RESULT", [(type(x).__name__, getattr(x, "name", None), id(x)) for x in fields(obj)])
p ("VALUES_NOFILTER", [(type(x).__name__, getattr(x, "name", None), id(x), getattr(x, "_field_type", None)) for x in obj.__dataclass_fields__.values()])
p ("INSTANCE_VS_CLASS", obj.__dataclass_fields__ is type(obj).__dataclass_fields__, id(obj.__dataclass_fields__), id(type(obj).__dataclass_fields__))
p ("SLOTS", type(obj).__slots__, type(type(obj).__slots__).__name__)
```

**Tape-loop indices** (`up 5` from `_asdict_inner` → `evaluation_tape` L216):

```text
p ("TAPE_LOOP", seed_label, roster, episode, slot, sender, receiver, role, local, common)
```

From `_asdict_inner` the ups are: asdict (1), `canonical_bytes` (2), `block` (3), `uniform_float32` (4), `evaluation_tape` (5). Do not use the historical `up 6` after already being on `canonical_bytes`; that overshoots to `execute` L166.

---

## 5. Line counts, import graph, tests that exercise `tapes.py`

### R09 attempt package line counts (43eec21e)

Intake counts match the launch bytes: experiment 566, semantics 321, tapes 253, module 9, test 156.

| Lines | Path |
| ---: | --- |
| 9 | `scripts/run_frrie_b01_contact_r09.py` |
| 21 | `.../b01_contact_r02/__init__.py` |
| 566 | `.../b01_contact_r02/experiment.py` |
| 321 | `.../b01_contact_r02/semantics.py` |
| 253 | `.../b01_contact_r02/tapes.py` (failing module) |
| 248 | `.../b01_contact_r02/collector.py` |
| 156 | `tests/.../b01_contact_r09/test_experiment.py` |

### Import graph (AST; first-party relative names as in source)

```
scripts/run_frrie_b01_contact_r09.py
  sys
  experiments...b01_contact_r02.main
    └── b01_contact_r02/__init__.py
          └── .experiment {OBJECT_ID, classify_r02, cost_config, execute,
                           exposure_record, initialize_contact_pair, main}

b01_contact_r02/experiment.py
  stdlib: argparse, hashlib, json, sys, time, pathlib.Path, typing
  numpy
  ..b01.constants.LEARNED_ARMS
  ..b01.contract {B01ContractError, canonical_json_bytes, validate_resource_receipt}
  ..b01.r128_smoke {_TimedTrainer, _build_adapter, _enforce_time_cap,
                    _evaluate_cell, _launch_sha}
      └── (import-time) ..native_adapter, ..policy, .native_batch, .tapes (B01), ...
  ..b01.trainer.PairedB01Trainer
  ..b01.three_seed._evaluate_cell
  ..state_codec {decode_optimizer_state, encode_optimizer_state}
  .collector.collect_r02_arm_update
  .semantics {HORIZON, OBJECT_ID, PRODUCTION_*, ROOT_HEX, ROSTERS, SEED*,
              TEST_*, classify_r02, cost_config, cut_contrasts,
              contact_integrity, exposure_record, _initialize_contact_pair,
              initialize_contact_pair}
  .tapes {evaluation_tape, production_training_inputs}
  deferred in execute: torch (L199); resource (L110, Linux RSS); psutil (L117, win32 RSS)

b01_contact_r02/semantics.py
  hashlib, math, typing, numpy
  ..arms.initialize_paired_arms
  ..b01.constants.LEARNED_ARMS
  ..policy.FRRIEActorCritic          → policy.py:20 import torch
  ..rng.AddressedRNG
  ..state_codec.encode_optimizer_state
  ..training.make_optimizer
  deferred in ContactActorCritic.project_beta: torch (L43)

b01_contact_r02/tapes.py
  hashlib, dataclasses.{asdict, dataclass}, typing, numpy
  ..b01.contract {B01ContractError, canonical_json_bytes}
  ..orchestration.OriginCoordinate
  ..rng.AddressedRNG
  ..tapes {EVENT_BASINS, EVENTS_PER_BASIN, EVENT_SLOT_COUNT, HORIZON,
           NATIVE_MAX_AGENTS, PUBLIC_ROLES, SURVEYOR_ROLE_COUNT,
           NativeEnvironmentTapePayload, generate_episode_tape,
           generate_training_origin_schedule}
  .semantics {SEED_LABEL, TEST_SEED_LABEL}

b01_contact_r02/collector.py
  typing, numpy
  ..b01.batch_collector {BatchCollectionAudit, CollectedUpdate, _audit_*,
                         _collect_*, _normalize_origins, _validate_tapes}
  ..b01.contract {B01ContractError, canonical_json_bytes}
  ..b01.trainer {B01ArmBatch, DirectExogenousEpisode, _EXOGENOUS_TOKEN}
  ..orchestration.OriginCoordinate
  ..policy {FRRIEActorCritic, LEGAL_ACTION_INDICES, require_torch}
  ..tapes.EpisodeTape
  ..training.RSCFEpisode
  deferred: torch (L127)
```

`tapes.py` → `.semantics` is one-way (labels only). `__init__` → `experiment` → `.tapes` / `.semantics` / `.collector`.

### Tests that exercise `tapes.py`

**Failing module `b01_contact_r02/tapes.py`:**

| File | How it hits the module |
| --- | --- |
| `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/test_experiment.py` | L30–32 imports `production_training_inputs`; L208–212 calls it. L218–225 subprocesses `scripts/run_frrie_b01_contact_r02.py --test-only` (real `evaluation_tape`, native). |
| `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r09/test_experiment.py` | L123 monkeypatches `experiment.evaluation_tape` (the name imported from `.tapes`). L130–133 subprocesses `python -m scripts.run_frrie_b01_contact_r09 --test-only` (real `evaluation_tape`, native). |

No other test file imports `b01_contact_r02.tapes`. There is no unit test that calls `b01_contact_r02.tapes.evaluation_tape` / `R02EvaluationAddress.canonical_bytes` without going through a runner.

**Sibling `b01/tapes.py` (same `asdict(self.validate())` shape, different class `B01EvaluationAddress`):**

- `tests/.../b01/test_tapes.py` (direct `evaluation_tape`, `B01EvaluationAddress`, `dataclasses.asdict`, `uniform_float32`)
- `tests/.../b01/test_candidate_analysis_contract.py` (imports `b01.tapes.evaluation_tape`)
- `tests/.../b01/test_integrated_contract.py` (same)

**Parent `tapes.py` (training episode tapes / origin schedule, not R02 evaluation addresses):**

- `tests/.../test_rng_tapes.py`
- plus collector/trainer tests that use `generate_episode_tape` / `make_test_update_inputs`

R07’s `b01_contact_r07/test_experiment.py` L113 monkeypatches `experiment.evaluation_tape` the same way as R09; it does not import `tapes.py` directly.

### Tests this scout ran

- `pytest --collect-only` on the four files above: 28 collected.
- `tests/.../b01/test_tapes.py`: **4 passed** in 0.53 s (`-p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/finite_resource_relational_inductive_efficiency/test/grok-map-01`).
- R09 / R02 `test_experiment.py` **not executed**: both subprocess the corresponding runner with `--test-only`, which calls `_build_adapter` (native build) after tapes. Assignment forbade runner / native build.
- Local one-episode `b01_contact_r02.tapes.evaluation_tape` probe (not pytest): succeeded on Windows 3.10.20.

---

## 6. What I could not determine

- Why A01’s `_asdict_inner` local `f` was a `tuple_iterator` while `type(obj).__dataclass_fields__` held 12 `Field`s. No constructing line exists in these bytes.
- Whether original R09 exit 139 (SIGSEGV, 16 s, no Python traceback) and A01 `AttributeError` share a cause. This map does not classify that.
- Exact `(episode, roster, slot, sender, receiver, kind)` at the A01 crash. Historical ADDRESS/COUNTERS commands missed `R02EvaluationAddress` fields and `evaluation_tape` locals.
- How many `asdict` calls succeeded before the failing uplink assignment (L216 proves the event-time loop of *that* tape finished; not which uplink cell).
- Whether WSL CPython 3.10.21 `dataclasses.py` bytes differ from local 3.10.20 beyond matching line numbers 1238/1245. Remote stdlib was not read.
- Whether `pdb -c continue` / `-X faulthandler` changed allocation enough to turn a signal into `AttributeError`.
- Whether import-time libtorch/numpy left heap damage that later appeared as a bad `f`. Not observable from static source.
- Production-scale 256×2 `evaluation_tape` behavior on these bytes (only episode 0, roster 9 was probed locally).
- `main` content of files other than the named four plus the three extra identical blobs above, except noting unrelated `b01` training-shard/pilot additions.

scope: none
