Claim: A08 will locate the original R09 process's native fault context if a fatal stop yields a readable PC/module or native caller record within one bounded observation.
Binding MARL structure: systems / information flow.

This runtime question does not test partial observability or non-stationarity;
it inspects the execution path carrying event-addressed randomness into the
same-information multi-agent learner and its native consequence.

Object: `FRRIE-R09-NATIVE-FATAL-A08-P39-20260908`. Class: **A/RECON**.
Status: `COMMAND_NOT_ACCEPTED / LIVE_INVOCATIONS_0`.
Live invocations:0. This is a new prospective observation under P39; A07 remains
ended with its original rule and scheduled MEI miss. A has no consumption state.

## 1. Question, authority and selected observation

[P39](../../portfolio/handoffs/2026-09-08-p39-frrie-native-fault-context.md) at
`bbdafe545315735bac5b4ebc8ef04d5ba7b0b541` authorizes this conditional route.
The [retained-material intake](FRRIE_NATIVE_CONTEXT_P39_RETAINED_INTAKE_20260908.md)
accepts the allowed lookup's unavailable native context; no offline GDB or target
was invoked. Reuse [A07 intake §4](FRRIE_R09_SCHEDULED_STACK_A07_SCIENTIFIC_INTAKE_20260908.md)
for the diagnostic-versus-minimal-B decision. Evidence-spec §§3–4,5.1,11.8.1,
11.8.6–7 and11.9 control this A, without requiring a complete causal diagnosis.

Question: what native PC/instruction/module and bounded caller context can be
retained at the first fatal stop of the original scientific process? A07's
Python `validate:133` method-entry line cannot supply that native location.
The next observation may justify a focused source/runtime inspection or identify
the need for a credible alternative path; a fault site alone is not its writer.

Use the already installed `/usr/bin/gdb`15.1. Reuse the same-host
[P36 E0](../capability_bound_semantic_currentness/CBSC_B05_NATIVE_FATAL_P36_RESULT_EVIDENCE_20260908.md)
and [static containment finding](../capability_bound_semantic_currentness/CBSC_B05_NATIVE_FATAL_P36_ROOT_HANDOFF_20260908.md).
Do not rerun that inventory. The GDB inferior may enter a separate process group
before post-startup EXITKILL; a debugger-only timeout does not enclose this
creation interval. CM may establish a command using existing host facilities,
supported by relevant source/configuration facts, without a runtime containment
test, target launch, new utility or installation. No method is assumed here.

At the first fatal stop, retain the signal and at most32 **current stopped
thread** native frames, one instruction at PC and this named x86_64 general
register set: `rax rbx rcx rdx rsi rdi rbp rsp r8 r9 r10 r11 r12 r13 r14 r15 rip eflags`.
Retain available executable/module identity and symbol/matching warnings, with
only the context needed to attribute the PC/callers. No all-thread backtrace,
locals/full-frame dump, arbitrary memory walk or symbol-download campaign.
Selected fatal signals are SIGSEGV, SIGBUS, SIGILL, SIGFPE and SIGABRT; freeze
their stop/print/nopass handling in CM's diagnostic input. Report the actual
signal even if different from A07's SIGSEGV. After the first
captured fatal stop, kill/quit; no continue, step, rearm or repeated sample.

Preserve normal ASLR (`set disable-randomization off`); disable GDB startup
shell, auto-loading and debuginfo downloads. The original A06 Python command's
`-X faulthandler`, pdb initial `continue`, accepted A05 helper/stdin/q/EOF are
retained; **omit A07's scheduled-arming argument**. The new observation is GDB
native first-fatal context around that original execution, not another timed or
Python-only sample. The helper can retain an ordinary uncaught exception if
that occurs instead; any helper failure stays separate from original output.
Fatal signal delivery is stopped for the native report, then the inferior is
killed; this observation change is explicit, not an original normal exit.

## 2. Primary record, reading and prediction

Primary: attributable first-fatal native context from the original process,
with enough PC/module or caller information to select a bounded next inspection.
Retain GDB's selected thread/signal, output and failures without assigning other
threads to a role. A missing symbol narrows interpretation; addresses and module
identity remain reportable if independently trustworthy. No runtime reliability,
causal writer, repeated-failure rate, parameter movement or native-return claim.

Apply the first matching row:

| Branch | Rule and bounded reading |
| --- | --- |
| `A08_NONCONFORMING` | Original source/runtime/RNG/numerical/schedule or accepted observation bytes differ; containment does not cover creation through forced KILL; the complete bound/allocation is breached; an unauthorized continuation, repeat or scientific traversal occurs. Preserve independent facts without a conforming diagnostic or algorithm polarity. |
| `A08_NATIVE_SITE_CAPTURED` | A first-fatal report attributable to the original process provides a readable PC/module or native caller location within the accepted boundary. Report the actual signal, instruction/register/frame availability and symbol/matching limits; location does not establish a causal writer or clear any earlier attempt. |
| `A08_PARTIAL_NATIVE_CONTEXT` | A first fatal stop is attributable, but missing symbols, unavailable instruction/module context or capture failure prevents the preceding site reading. Preserve every trustworthy register/address/frame fact and the exact missing dependency; no retry or causal inference. |
| `A08_OTHER_FAILURE_OBSERVED` | No preceding native reading applies, but a different original exception, signal or terminal failure is retained. Preserve its identity and any trustworthy original output, with debugger/helper errors separate; it does not reproduce or clear A07's fatal event. |
| `A08_NORMAL_COMPLETION` | The original program completes normally within the full cap with its normal outputs retained and no uncaught exception. Preserve them for separate validity review; no automatic full-B acceptance, native-fault explanation or runtime-reliability claim. |
| `A08_INCONCLUSIVE` | Admission failure, timeout, missing/ambiguous original-process evidence or reporting/termination uncertainty prevents the preceding readings. Retain exact partial facts and stop without extension, repeat, cause attribution or scientific polarity. |

Categorical **MEI:** one attributable PC/module or native caller location useful
for a focused next inspection. Above this criterion, recommend that bounded
inspection; incomplete context leaves the native dependency unresolved. A
different failure or normal completion preserves a different observation rather
than declaring a repair. The table, not this narrative, controls the reading.

DM prediction: **usable native fatal-site context before the cap, low confidence**.
A07's62.86s fatal event and A05's42.71s termination support trying one bounded
observation; A06's118.40s timeout contradicts assuming recurrence or sufficient
time. A readable nonreproducing failure or normal completion contradicts this
prediction; failed admission, nonconformance, timeout or failed native capture
leaves it unscored. No particular module or writer is predicted. Owner prediction:
**not taken (unattended)** unless a reply exists at intake.

No tuned same-information host headroom record exists. This A does not measure
it; reuse the R09 baseline set and MEI0.005 unchanged. R06 root1 N15
+0.005548293532 remains conditional support, R07 root2−0.001948094523 contradicts
material recurrence, and R08's root1 cut adds no independent-root evidence.
No mechanism, C, transfer, UAV, family, lifecycle or priority conclusion follows.

## 3. Scientific bindings, paths and complete exposure

Reuse [A07 card §§3–4](FRRIE_R09_SCHEDULED_STACK_A07_SCIENCE_CARD_20260908.md)
and [A06 exact original-program handoff](FRRIE_R09_FATAL_CALLPATH_A06_ROOT_HANDOFF_20260908.md)
atfc279590ecd88aa3cc2d5c10348453b7dcd4e9fe. Explicit prospective bindings:

| Quantity | Bound value |
| --- | --- |
| Original scientific/preflight source | `43eec21e9584c83e5e8d940402d7e4570b454e59` |
| Helper/stdin source and staged files | `30643b7359b35c6e9d5751147d0999bc629a966d`; original A05 staged files/hashes unchanged |
| Node / interpreter | `hmasd-wsl-node`, LAPTOP-U9TDKC8A WSL2; `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python` |
| Runtime | P22 system CPython3.12.3/GCC13.3.0 and its23 retained pins, including NumPy1.26.3/Torch2.7.0+cu118 |
| Scientific profile | Root3, CPU FP32/original FP64 reductions, Torch1/four-worker/native32, LR0.003/beta boxes,128 paired updates and original checkpoints/uniform/rosters/RNG |
| Proposed fresh handle / cwd | `frrie-a08-native-fault-p39-43eec21e`; `/home/wu/hmasd-worktrees/frrie-a08-native-fault-p39-43eec21e` |
| Proposed fresh relative output | `temp/directions/finite_resource_relational_inductive_efficiency/exp/a08_native_fatal_p39` |
| Proposed input staging | `/home/wu/hmasd-inputs/frrie-a08-native-fault-p39/`; exact script/GDB input bytes and names remain CM binding work |
| Primary / optional output | Accepted new supervisor log/native report; original learner output and unchanged A05 bounded exception state in the fresh output |

Exact input/literal acceptance is pending; none of these paths is a launched
identity. Preserve all old handles/outputs and fresh original native build/load.
No old artifact reuse, source repair, serialization workaround, seed change,
phase cutoff, setup or local fallback. Fresh original on-node memory admission
must pass physical/effective availability≥4GiB adjacent to program execution;
P39 lookup and A07 admission do not substitute for it.

One detached **TERM115s + at most5s grace =120s complete observation** includes
admission, all debugger/inferior startup, imports/build, initialization/evaluation/
learning, reporting/publication and forced termination of descendants. There is
no uncharged inferior-startup interval or separate capture allowance. Root alone
launches/observes after accepted command and commit/push. Every terminal outcome
ends this route; missing symbols, timeout, a different failure or nonreproduction
never authorizes a retry, extra sample, cap reset or full B.

Dominant algorithm ceilings: one chain×two arms×128 updates,8192 training tapes,
512 evaluation tapes,16384 factual training episodes,256 Adam/backward calls and
1316864 native slots. Nominal per-arm LR exposure≤0.384 or7.68 initialization
half-ranges is not measured motion. Reuse A07's tool-calculated configuration
receipt; actual work is unknown until retained counters establish it. Added
observation is one debugger plus one bounded first-fatal report, no arm/seed
multiplier. Unknown report/containment overhead stays within120s, not a separate
pilot. Invocation-wall sum/critical path≤120s; aggregate CPU/scratch/complete
descendant RSS remain unmeasured unless existing receipts supply them.

## 4. Engineering scope, acceptance and stop

Scope §4 named need: **one bounded native fault-context report and existing-host
containment of its debugger/inferior** for section2's location measurement.
Reuse the original exception/fatal facilities. All other §4 additions:none.
No new utility/framework, recurring monitor, source/test change, runtime
containment experiment, package/setup operation or §5 exception is authorized.

CM prepares one complete existing-facility command/diagnostic-input handoff or
returns the exact missing containment method with a bounded engineering proposal.
Static acceptance covers original program/input/source/profile preservation,
first-fatal report/kill/quit, ASLR and auto-load/download/startup-shell settings,
shell/input syntax without execution, and source/configuration support for the
complete creation-through-KILL boundary. Reuse P36 evidence; do not infer the
missing early interval from graceful GDB quit or post-startup EXITKILL alone.
No live target, test inferior, import, smoke or additional core lookup is allowed
in preparation. Ordinary static source/configuration reads are for this method,
not a capability experiment or standing audit.

Same CM owns only the new `FRRIE_R09_NATIVE_FATAL_A08_ROOT_HANDOFF_20260908.md`
and ignored `exp/a08_preparation_p39/` command/input/acceptance receipts, in the
same `codex/frrie` authoring checkout. DM owns this card/intake/item/brief. Keep
one writer through edit/check/commit/push; no new child or branch. The three CM
comparison batches have ended; this command-input preparation creates no new
coding arm or scientific invocation.

If containment cannot be established within this existing-facility scope, stop
with **COMMAND_NOT_ACCEPTED / LIVE_INVOCATIONS_0**, naming the missing method and
bounded out-of-scope engineering task. Do not invent a ready literal, repeat a
capability check or silently relax the complete boundary. Independent supported
facts remain reportable. If accepted, DM binds exact bytes/argv and Root performs
one fresh admitted invocation; same CM collects E0 and DM applies section2.

## 5. Delegated selection and owner surface

Options: (a) prepare one P39 native observation after the retained-material miss;
(b) repeat/add Python-only samples; (c) unsupported source repair or full B.
Recommend/select **(a), preparation pending exact method acceptance**.
**Owner-delegated decision (unattended,2026-09-03 instruction): (a).** This is
object-tier observation inside P39, with no family or Portfolio disposition.
The new-card P2
[20260908-frrie-003](../../portfolio/owner/inbox/2026-09-08/20260908-frrie-003.json)
is published through the owner console; current main reviews are empty and no
reply is needed to perform the assigned preparation.

```text
| 2026-09-08T09:13:46Z | finite_resource_relational_inductive_efficiency | object | selection | (a) prepare P39 one native observation after retained miss; (b) Python-only repeat; (c) unsupported patch/full B | (a):A08 A_RECON question/report/source/profile/cap frozen;existing-facility creation-through-KILL method and exact bytes pending;live invocations0 | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P39 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_NATIVE_FATAL_A08_SCIENCE_CARD_20260908.md | none | |
```

## 6. Preparation return — no live command accepted

The [CM handoff](FRRIE_R09_NATIVE_FATAL_A08_ROOT_HANDOFF_20260908.md) at
`9d94806a598bd461ba84a796d64ab030d0c4b5eb` and
[DM intake](FRRIE_R09_NATIVE_FATAL_A08_PREPARATION_INTAKE_20260908.md) record
the supported source/configuration facts, exact remaining method, checks,
counts, costs, prediction status and next-task proposal. The intake links the
Chinese brief and supplies audit rows.

The existing user systemd manager/cgroup and versioned sources supply a static
containment route before GDB target exec, addressing P36's separate-pgrp gap.
The candidate's115+5s timer starts after frontend/unit-request time, so it does
not establish this card's complete startup-to-termination bound. Killing only
the frontend does not cancel an already accepted unit. This is a method gap,
not an observed escape, overrun or proof that every existing method is impossible.

Five enclosing static host/syntax calls sum6.0143048s; no service, GDB, inferior,
namespace, target import, fixture, setup or new core lookup occurred. Draft
input/syntax checks passed, but their receipt explicitly denies launch authority.
The drafts remain ignored and **must not be staged or dispatched**. The conditional
one native invocation remains unused; there is no accepted handle or launch input.

Apply section4's **COMMAND_NOT_ACCEPTED / LIVE_INVOCATIONS_0** preparation stop.
Native-site MEI and prediction are untested/unscored, with owner prediction not
taken. All prospective scientific fields and section2 runtime rules remain
unchanged; none is applied as an observed runtime result. No scope §5 breach is
evidenced. A07 and every earlier outcome/quarantine are preserved.

Object-tier choice: accept the bounded finding and return the exact method gap,
rather than launch, exempt startup or add a utility/test. Recommend/select(a).
**Owner-delegated decision (unattended,2026-09-03 instruction): (a).** The intake
returns one focused static existing-utility outer-timer/namespace proposal via
Root to Portfolio. It does not dispatch that task or change a scientific budget,
family, lifecycle, priority or UAV-entry state.

scope: one bounded native fault-context report and existing-host debugger/inferior containment per section4
