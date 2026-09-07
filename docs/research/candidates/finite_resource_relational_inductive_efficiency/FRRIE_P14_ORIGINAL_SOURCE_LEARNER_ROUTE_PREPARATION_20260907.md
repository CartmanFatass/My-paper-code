# FRRIE P14 original-source learner-route preparation — 2026-09-07

**Return: one precise missing artifact prevents a complete setup handoff.** The permitted
installed-package inventory contains no CPython-3.12 Torch distribution. Original R09 source,
system Python, the NumPy binary and the native-build route can be named. No runtime amendment,
installation, package/workload import, build, probe, tape or learner execution is authorized or
performed. This is A/RECON source/metadata preparation, not a new learner result.

Assignment: **P14-FRRIE-ORIGINAL-SOURCE-LEARNER-ROUTE-01**, [P14 handoff](../../portfolio/handoffs/2026-09-07-p14-vsp02-code-and-direction-continuations.md)
at `9698394554eb6a7d14c9e67a12fd7f51a744772d`. The question and inventory scope were supplied
before observation by that assignment and [P13 intake §5](FRRIE_R09_A04_SCIENTIFIC_INTAKE_20260907.md#5-smallest-next-sourceruntime-decision-missing-input-and-prospective-return).

## 1. Source and evidence checked

Scientific source is **`43eec21e9584c83e5e8d940402d7e4570b454e59`**, as required by P14.
Read its R09 wrapper, `b01_contact_r02/experiment.py`, `b01/r128_smoke.py`, the named compute
constants/profile, native-adapter build path and relevant dependency manifests through Git,
without checking out or importing that code. The later 246-line addition to imported
`b01/trainer.py` recorded in P13 is not included in this source binding. Current HEAD is not
substituted and no history or source is reverted.

Reused the [R09 card](FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md), its retained portability,
work and branch rules, [A03 stop](FRRIE_R09_SEGFAULT_A03_TAPE_ISOLATION_INTAKE_20260906.md#4-decisions-this-intake-produces),
A04 installation/technical receipts and P13 intake. Applied current AGENTS focused reading,
evidence-spec §§4, 5.1, 11.4, 11.8.5–11.8.7 and 11.9, and engineering-scope §§4–5.
Scientific-tools informed this source/metadata reading; no new baseline, mechanism, literature
claim or performance experiment is selected.

P14's controlling boundary, verbatim:

> A bounded read-only installed-package inventory is permitted; no workload import, download, install, native build, probe, tape creation or learner execution.

The inventory below meets that path/measurement boundary. It is not a compatibility execution
or a new observation of R09. No setup payload or proposed command was executed.

## 2. Direct installed metadata and its limits

[Raw inventory](FRRIE_P14_LEARNER_STACK_INVENTORY_20260907.json), observed
`2026-09-07T22:45:42.974365+00:00` on configured `hmasd-wsl-node` / `LAPTOP-U9TDKC8A`.
One bounded read used `/usr/bin/python3.12 -I -S -` and only standard-library file/path/JSON
operations. It read five venvs and seven package roots; the bound was 32 venvs, four Python
library roots per venv and only NumPy/Torch distributions. No package was imported. Compiler
facts are executable-path resolution and dpkg metadata; no compiler command was run.

| Required surface | Direct evidence | What remains unobserved |
| --- | --- | --- |
| Python | `/usr/bin/python3.12`, CPython 3.12.3 / GCC 13.3.0; four observed venvs resolve to it | Full R09 behavior under this interpreter |
| NumPy | A04 venv contains `numpy-1.26.3.dist-info`; `Requires-Python: >=3.9`; wheel tags `cp312-cp312-manylinux_2_17_x86_64` / `manylinux2014_x86_64` | A separate learner-environment install; A04 did not run the learner |
| Torch | Only `/home/wu/.venvs/hmasd/lib/python3.10/site-packages/torch-2.7.0+cu118.dist-info`; wheel tag `cp310-cp310-manylinux_2_28_x86_64` | A cp312 Torch artifact and its exact acquisition/setup inputs |
| C++ compiler | `/usr/bin/c++` and `/usr/bin/g++` resolve to `/usr/bin/x86_64-linux-gnu-g++-13`; installed g++-13 package `13.3.0-6ubuntu2~24.04.1` | Actual build/load on the proposed chain |
| Native headers/runtime | dpkg marks `libstdc++-13-dev` and `libc6-dev` installed | No claim of executed native ABI compatibility |

No Torch metadata was found in the six checked system312/system package roots. This is a
bounded installed-state fact, not a claim that no suitable wheel exists elsewhere or can be
acquired. The package metadata's `Requires-Python: >=3.9.0` alone does not establish a cp312
binary. Both observed Torch/NumPy distributions lack `direct_url.json`; no exact wheel URL
or downloaded archive is inferred from their names.

Original-source `requirements_sb3.txt` names `torch==2.7.0+cu118` and the cu118 index, but is
an older Windows export, not a cp312/Linux artifact record. `requirements-cloud-test.txt`
names `torch==2.7.0+cpu` for a Python-3.10 compatibility test, not this R09 route. The server
manifest does not pin Torch; the science-tools environment is Windows/Python3.11 with NumPy2.
None supplies the missing cp312 Torch artifact. A CPU computation does not automatically
select the `+cpu` distribution in place of the recorded `+cu118` build.

The retained Torch METADATA also names `setuptools` when Python >=3.12 and the Linux
CUDA/cuDNN/triton dependencies for this distribution. Those are setup dependencies even if
R09 uses only CPU tensors. A candidate setup must not copy the cp310 extension into system312,
reuse the shared site-packages, install with unresolved dependencies, or silently change the
Torch variant to avoid this missing input.

## 3. Exact missing input and native-build route

**Missing artifact:** a verified **CPython3.12 / Linux x86_64 binary distribution of
`torch==2.7.0+cu118`**, including its actual filename/acquisition source, wheel ABI/platform
metadata and Python-3.12-applicable dependency metadata. This is the minimally changed candidate
relative to the retained remote stack. No exact filename, URL, digest, package availability
or successful import is fabricated. A separately selected `2.7.0+cpu` route would need its own
artifact evidence and explicit variant decision; the cloud manifest alone does not provide it.

The missing input is artifact/metadata evidence, not a request to diagnose the historical
corruption. Acquisition/import/build can be included in one later allocated learner chain;
no standalone smoke, causal panel or full-stack certification is made a B prerequisite.
Current P14 permits neither acquisition nor an artifact-discovery download.

The native route is already expressed by original `b01/r128_smoke.py::_build_adapter`:
`build_package_native_artifact()` followed by `load_package_native_adapter(named_compute_profile())`.
On this Linux node the accepted `native_adapter.py` chooses the observed `/usr/bin/c++` and
builds `native/frrie_ridgegate2z_external.cpp` into the package `_native/` shared library, with:

```text
-O3 -std=c++17 -shared -fPIC -fno-fast-math -ffp-contract=off
```

The source uses its existing temporary artifact publication and ctypes ABI. The builder has
an internal 60 s timeout and expects its fresh package artifact, which is why any future
launch uses a fresh detached worktree at the original source rather than an old built tree.
That existing timeout is part of the complete chain, not another allocation. No native wrapper,
new Python extension, cache/rebuild machinery or source change is needed to state this route.

## 4. Prospective source/runtime decision and handoff boundary

The R09 card's “Predictions, exposure, cost, cap and portability” section explicitly declares
CPU FP32/Torch1/native32 execution prospectively portable across configured Linux/Windows
surfaces, without compiler-bit-identity pinning. Moving the candidate from uv CPython3.10 to
system CPython3.12 on the same remote node is therefore a proposed **object-tier execution-
substrate amendment within that recorded portability boundary**, provided the actual algorithm,
information, dtype/reductions, RNG, comparison and work remain intact. It is not a new family,
recast, C object or Portfolio disposition, and it does not require unique old-cause attribution.

The later A03 instruction still says **“no R09 launch on this substrate until it is answered”**;
the original uv stack remains stopped. A04's card also expressly denies automatic R09 release
on either stack. P14 supplies preparation only. Thus **no amendment is applied here**: DM must
record the explicit source/runtime choice under a later authorized task, and Portfolio must
supply any actual setup/learner allocation through Root. No unresolved frozen scientific-
meaning conflict was found in this proposed unchanged comparison. Substituting the later
trainer, another Torch variant, a different backend or numerical/work settings would be a
separate named change; it is not covered by the proposed system312 route.

Five-item prospective handoff, retained as preparation with the above missing artifact:

1. **Deliverable:** one setup-through-publication R09 third-root B using original source,
   if separately allocated after the explicit runtime decision. This return supplies the
   source/native route and the exact missing dependency; it is not a runnable setup command.
2. **Paths/entry:** future exact-SHA detached worktree under `/home/wu/hmasd-worktrees/`,
   a new dedicated FRRIE learner venv under `/home/wu/.venvs/`, and a distinct direction output
   root. Do not mutate A04 or `/home/wu/.venvs/hmasd`. Original entry is
   `scripts/run_frrie_b01_contact_r09.py`; its wrapper binds seed3. Existing flags are
   `--output-root` and `--admission-receipt`; do not use `--test-only` or `--role-column-cut`.
   No source paths are owned for implementation by this task.
3. **Preserved semantics:** R09 card's root, treatment/comparator, work and rule sections:
   root/label3, beta ±0.04/±1.50, LR0.003, CPU FP32 model, original FP64 reductions,
   Torch1, native32, original `CPP_BATCH_W32_WORKERS4_THREADS1_V1` profile; 128 updates,
   N15 primary/full N9, checkpoints0/32/64/128, uniform reference, six branches and MEI0.005.
   “Torch1” is not permission to replace the existing worker profile. Keep the card's existing
   optional debugger observation boundary; no new exception/retry machinery is proposed.
4. **Acceptance:** reuse the accepted source and original checks. A later authorized chain
   records actual runtime/dependency facts, fresh on-node >=4GiB physical/effective admission
   immediately before the runner, actual source/root/LR, all learner/evaluation counts and
   complete summary, then applies the original card's ordered rule. No workload check,
   publication certificate, output-equality comparison or performance claim is performed here.
   If compatibility later requires code, return the exact defect/full common spec to Root's
   five-arm capture before any implementation; no CM warm-up or source repair is commissioned.
5. **Budget/stop:** current allocation is zero installs, builds, probes, tapes, learners and
   source edits. Future original caps remain four attributed hours per arm and eight hours
   complete; the 28,795 s outer TERM bound plus at most 5 s grace must include setup, imports,
   native build, learning, evaluation and publication. No separate setup cap is added. Return
   original failure/missing output without retry or an outcome-dependent budget extension.

P13's machine-produced work remains the unchanged candidate: two arms × 128 updates × 64
factual episodes; 256 Adam steps, 196,608 factual transitions, 1,261,568 training native slots;
18 evaluation cells / 4,608 episodes / 55,296 slots, total1,316,864 native slots. Input work is
8,192 training +512 evaluation tapes. Nominal LR exposure relative to initial half-range is
7.68, not a motion bound. Added validation/diagnostic invocations are zero. R07's 903 s historical
supervisor anchor and A04's 16 s do not measure new-stack setup/learner cost; it remains unknown.

## 5. Decisions, interpretation and return

Options: (a) retain original source and the minimally changed `2.7.0+cu118` candidate, returning
its exact missing cp312 artifact; (b) substitute `+cpu` from the historical cloud manifest;
(c) seek compatibility by an installation/import/probe outside P14. Recommend/select **(a)**.
The evidence does not complete either Torch artifact route, and P14 excludes (c).
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a), preparation/dependency
return only.** The original source binding itself is P14's direct instruction. No runtime
amendment, R09 release or direction-tier decision is inferred.

Strongest support for the prospective path is A04's bounded system312/NumPy completion and
an existing source-defined C++/ctypes route with installed compiler metadata. Strongest
limitation is the absent cp312 Torch artifact in this inventory and the unexecuted learner/
native chain; A03's same-host failure remains. The A04 completion ceiling, historical R06–R08
signs, prior quarantine, R09 rule/prediction and absent host headroom record are unchanged.
This metadata observation has no algorithm MEI or native-return polarity. No new performance
prediction was made; owner prediction is not taken. A04's previously scored prediction is not
rescored as a second success. Resource/throughput measurement was not the inventory's question.

At the clean boundary, `item.py reviews --json` on current main returned `[]`; relevant FRRIE
owner cells are empty. P13 rows are now integrated at audit lines90–91. There is no unapplied
owner instruction, new card or P1/P2 item. Current work is source/metadata preparation, excluded
from the CM comparison because it creates no new coding assignment or historical replay.

Authoring reused the clean `codex/frrie` checkout at
`C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, starting `291cb3447`. Own only this
preparation, the raw inventory and the [Chinese brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_P14-learner-route-preparation.md).
Source, cards, DIRECTION, shared audit and other writers' files are untouched.

**Next owner:** Root integrates the named paths and returns the **cp312 Torch artifact/metadata
input** to Portfolio for the next scoped command. DM retains the eventual source/runtime
amendment; an artifact record would not itself authorize launch. The next scientific
discriminator remains the original complete third-root native-return comparison, not another
input-only diagnostic. No complete setup payload is issued while this artifact is unspecified.

Root appends this supplied row at integration; it is not claimed already appended here:

```text
| 2026-09-07T15:49:45-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) retain original43eec21e/cu118 candidate and return missing cp312 artifact; (b) substitute historical cpu manifest; (c) install/import/probe outside P14 | (a): original source/native route bound; five venvs/seven roots contain no cp312 Torch; no amendment/code/setup/learner allocation | yes | OWNER_DELEGATED (unattended, 2026-09-03 instruction); P14-FRRIE-ORIGINAL-SOURCE-LEARNER-ROUTE-01 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_P14_ORIGINAL_SOURCE_LEARNER_ROUTE_PREPARATION_20260907.md | none | |
```

scope: none
