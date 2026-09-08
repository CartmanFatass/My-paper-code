# P47 native crash repair evidence — 2026-09-08

Status: bounded diagnosis in progress; no production correction established.
Authority: P47, “FRRIE and CBSC: repair within the research chains”. This is
technical A/RECON evidence under evidence-spec §§3–4,5.1,11.8.5–7, with zero
learners, optimizer steps, scientific evaluation, or new research seeds.

## Source inspection and retained facts

Authoring checkout: `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`,
`codex/frrie`, clean start `389d6222eb0eefde7f49e47aa35d6a57ecb661c3`.
The P47 handoff confirms all three comparison batches completed. Production
source is unchanged. DM retains scientific intake/card ownership.

Reused the full `NATIVE_CRASH_FORENSIC_RESULT_20260908.md` and its direct static
review and interruption context in `C:/Projects/HMASD/temp/native-crash-repair-20260908/`.
Four matching-symbol core analyses already locate invalid interpreter state,
including the semantic-address validation caller and CBSC Enum/list callers;
they do not identify a corrupting writer. The successful tape-only and six-million
call checks exclude only those simplified patterns as sufficient reproducers.

Inspected `rng.py`, `tapes.py`, B01/R02 tape producers, `native_adapter.py`,
`native/native_abi.py`, the C++ batch exports and their indexed FIFO/pending paths.
Tape construction owns immutable byte-backed arrays. Native payloads pad to21
agents. Adapter calls retain direct ctypes arrays synchronously; snapshots own
exact `STATE_SIZE * count` bytes. ABI argument/restype declarations and state-size
checks match the inspected exports. Pending uplinks are created for listening
relay indices, bounded by the registered roster. No concrete fault was found
in these inspected boundaries; this is not a complete memory-safety proof.
The C++ and ABI source diff against historical `43eec21e9584c83e5e8d940402d7e4570b454e59`
is empty. No production correction is justified by static inspection alone.

## Selected bounded native discriminator (recorded before invocation)

Hypothesis: the retained A07 native library's direct reset/observe/step/state-copy
boundary can reproduce corruption on fixed legal inputs without a learner.
The earlier tape/import checks do not exercise this boundary. Reuse unchanged
`experiments/candidates/finite_resource_relational_inductive_efficiency/native_crash_repair/reproduce_native.py`
at the starting SHA; its previous committed presence is not passing evidence.

The probe uses four rosters (6,9,15,21), eight resets each,32 lanes and12 slots:
32 reset calls plus384 calls each to observe/snapshot/restore/step =1,568 native
calls and12,288 fixed-input lane transitions. It checks allocated buffer borders,
state-copy equality and terminal slot12, without reading an algorithm endpoint.
Expected observation is either a concrete call/assertion/fatal failure or completion
of those checks. A pass cannot clear the production collector, worker topology,
full initialization, interpreter, or historical crashes.

Per-invocation cost projection: no complete-path timing yet for this native probe;
known work is the counts above, fixed buffers and existing library load. One
complete invocation is capped at120s (TERM115s plus5s grace), including admission,
imports, calls and output. No fresh build or profiling. This is one diagnostic,
not a scientific arm or sweep; capped wall sum/critical path120s, aggregate CPU
unknown until observed. Focused-test allowance remains separately300s.

Post-learner path coverage: no learner/publication path is changed or claimed.
The diagnostic's primary output is its terminal JSON plus admission, supervisor
exit and wall/RSS receipt. Existing publication failures remain unresolved.

Execution binding: `hmasd-wsl-node`, CPU; historical interpreter
`/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python`;
OMP/MKL/OpenBLAS/NumExpr thread limits1. No host/device substitution.
Fresh detached cwd `/home/wu/hmasd-worktrees/frrie-p47-native-boundary-20260908`
at `389d6222eb0eefde7f49e47aa35d6a57ecb661c3`.
Handle `frrie-p47-native-boundary-20260908`, configured `agent-task` supervisor.
Relative output `temp/directions/finite_resource_relational_inductive_efficiency/exp/p47_native_boundary`.
Adjacent `admit-memory && python -X faulthandler -m experiments.candidates.finite_resource_relational_inductive_efficiency.native_crash_repair.reproduce_native`
uses the existing A07 artifact argument
`/home/wu/hmasd-worktrees/frrie-a07-scheduled-stack-p35-43eec21e/experiments/candidates/finite_resource_relational_inductive_efficiency/_native/libfrrie_ridgegate2z_external.so`.
Preserved artifact reuse is diagnostic only; it does not enter the fresh-build
production loader or change that loader's admission meaning. Artifact identity,
full shell invocation and actual receipts will be retained with the result.

Engineering-scope §4 additions: none. No new process framework, namespace,
utility build, compatibility layer, or production guard. Independent review is
required if a native/semantic production correction emerges; none exists yet.

## Recovery allocation

DM's P47 review identifies no currently runnable learner remainder: R09 is
`NO_RETRY_ALLOCATED`, P22 is one pair/no retry and P35/P37 ended at A07.
P47 authorizes this ordinary non-learning repair work, not another R09 invocation.
Historical failures and all original scientific meanings remain unchanged.
