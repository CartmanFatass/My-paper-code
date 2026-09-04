# FRRIE contact-active R128 R02 — R03 failure intake (2026-09-04)

Status: `R03_IMPLEMENTATION_INVALID / EXACTNESS_GUARD_REPRODUCED / B_OBJECT_UNCHANGED`.

This is an intake of a failed implementation attempt and its technical reproduction, not a valid
algorithm result. The reproduction has A/RECON ceiling: a numerical execution-path fact on the
recorded host, parameters, and suffix. The attempted scientific object remains the unchanged
`FRRIE-B01-CONTACT-ACTIVE-R128-R02-20260904`, class `B/EXPLORE`.

## What I checked

I checked the R02 science card, evidence specification §§4, 6.2 and 11.4, engineering scope §§4–5,
the CM execution receipt, tracker terminal notification relayed by Root, and the actual source
checks in `b01/batch_collector.py` and its R02 caller. I inspected how the factual native return
is reused only after suffix replay and separated intermediate tensor equality from sampled
action, information, native transition, and return equality.

CM directly confirmed the failed task and reproduced the same exception over committed source
`36b538ba1b91eede9f528dd315fa624f8c1d53e5`, with the same literal R02 root, CPU FP32 computation,
first tight-arm collector update, and a fresh admitted remote worktree. No production guard was
suppressed in the reproduction: the original exception propagated. Diagnostic continuation used
the unchanged actor/native calls and literal uniforms and did not update an optimizer.

## Rule and attempt disposition

The card's first rule is retained verbatim:

> A common-integrity item fails; remote/local admission is absent or below 4 GiB; real learner transition/update/evaluation counts or exposure are zero/missing; information/work differs; raw initialization is not paired; the initial tight clip does not change exactly five coordinates; optimizer moments change during projection; or required learner-side curves/counts are absent. Quarantine; no result.

`_03` did not complete the 128-update learner or publish the required curves/counts. It is an
incomplete implementation attempt with the disposition `R02_INVALID_INCOMPLETE`; no return-based
scientific branch is reached. Quarantine means preserve its log, successful admission, empty
result directory, and source identity, and neither resume nor salvage it. B objects have no
consumption state. The attempted card's semantic branch order is not rewritten.

## Counts and receipts

- Task: `frrie_b01_contact_r02_36b538ba_03`, `wsl_4070` via `hmasd-wsl-node`.
- Source worktree: `/home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba` at the SHA above.
- Admitted: `2026-09-04T21:45:48.033417Z`; physical/effective availability each
  `13,205,676,032` bytes, above the `4,294,967,296`-byte floor.
- Terminal: exit 1 at `2026-09-04T21:46:23Z`, after 35 supervisor seconds.
- Log: `/home/wu/.agent-tasks/frrie_b01_contact_r02_36b538ba_03/task.log`.
- Result root: `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r02_r03`
  under the source worktree, present but empty.
- Receipt: the source worktree's
  `temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_r03_admission.json`.
- The traceback reached first-update collection. No optimizer step was completed and no valid
  learner/evaluation summary or terminal learning curve was published. Native work before the
  failure is not a complete R128 observation and is not assigned return polarity.
- Successful exact-step reproduction used a fresh same-SHA worktree because an existing native
  build guard refused reusing the original worktree's retained library. Its fresh admission
  measured physical/effective availability `12,966,584,320` bytes; the reproduced guard exited 1
  after seven supervisor seconds. The CM receipt records the diagnostic command and artifacts.

Earlier `_01` and `_02` retain their separate diagnoses: `_01` was a reproduced omitted committed
preflight dependency, restored without source changes; `_02` failed before native/model/learner
execution, and its tape-validation error remains unclassified after the exact tape expression
subsequently passed. Neither is reclassified by this reproduction.

## Direct numerical observation

The failing cell was `PHY_TRUST_004`, update 1, `N=9`, origin slot 0 to future slot 1, a seven-lane
replay chunk against the original factual width 32. The affected replay lane was 6, factual
episode 31, role 2. Its incoming recurrent state was exactly equal before the actor call.

| measured field | direct difference |
| --- | --- |
| hidden state | 10 of 576 FP32 values differ; maximum absolute difference `2.9802322388e-8` |
| action probabilities | 1 of 54 values differs by `2.9802322388e-8` |
| differing probability | factual `0.33068668842315674`; replay `0.33068665862083435` |
| sampled actions | exactly equal |
| same seven-lane inputs with grad enabled | same intermediate discrepancy |
| the same inputs padded to width 32 in a diagnostic control | hidden states and probabilities exactly equal |

CM directly continued all seven failing-chunk lanes through future slots 1–11. Every sampled
action, native step, state snapshot, next observation, and terminal native return remained exactly
equal. The largest later hidden difference was `5.96046448e-8`; the largest probability difference
was `2.98023224e-8`. The padding control was diagnostic only; production computation was not
changed or padded.

This supports a batch-width-dependent FP32 intermediate identity failure on this observed suffix.
It does not show a grad-mode cause, native factual-Q divergence, global numerical equivalence, or
absence of future action divergence. It is not an observation of the treatment's learning value.

## Scientific and engineering reading

The current card preserves CPU FP32, literal RNG coupling, matched work/information, actual
factual and counterfactual suffix returns, and the native action/return endpoint. It explicitly
does not bind compiler bit identity. Evidence §11.4 does not permit an unrequested intermediate
bit-identity predicate to hold this B launch.

Exact sampled-action and native-path reproduction still matters: it justifies reuse of the
factual return for the factual Q entry. Those checks must remain, including pre/post snapshots,
observations, roles, legal masks, steps and terminal returns. A repair that merely suppresses
native divergence, changes actor arithmetic/batch width, or adds arbitrary numerical tolerances
would alter or weaken a meaningful part of the comparison and is not selected.

Strongest support for the narrow repair is the directly identical action/native/return suffix
despite the measured intermediate rounding. Strongest remaining limitation is its bounded scope:
one reproduced suffix at the first tight-arm update. Retaining exact discrete/native checks
ensures a later material divergence still stops the incomplete implementation for investigation.

## Decisions this intake produces

### Failed attempt

Options: (a) quarantine `_03` as incomplete after the exact guard was reproduced; (b) salvage,
resume, or interpret it as a B result.

Recommendation and selection: **(a)**. No valid R128 result exists, and the required learner
counts/curves are absent. This is a technical disposition without scientific polarity.

### Minimum repair

Options: (a) skip only unclaimed hidden/probability intermediate bit-identity checks in the R02
factual-suffix path while preserving every actual computation and exact action/native check;
(b) force width-32 replay or alter kernels/arithmetic to obtain exact intermediate tensors;
(c) leave the B object blocked by intermediate exactness.

Recommendation and selection: **(a)**. The smallest R02-only implementation may expose one plainly
named keyword on the existing private audit routine, retain its old default for other callers,
and let only the R02 caller omit incoming-hidden, postdecision-hidden, and probability tensor
identity predicates. It must retain exact sampled actions and native reproduction. No padding,
tolerance, dtype, RNG, policy/native call, grad-mode, recurrence, root, seed, optimizer, exposure,
budget, evaluation, side-effect, or result-rule change is authorized.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)** for the quarantine and
**(a)** for the bounded repair, labelled `OWNER_DELEGATED`. Owner item `20260904-frrie-013`
records this combined technical disposition and its consequences; owner flag `none`.

CM owns the bounded repair through a separate implementer worktree, the relevant toy and a
focused regression protecting actual action/native divergence, and technical acceptance. Exact
source must be committed and pushed before remote verification. No new engineering-scope §4
machinery is authorized. A new result-bearing attempt may be selected only after the minimal
change is inspected against these protected semantics; no blind retry is selected here.

## Owner flags and next discriminator

The DM's R02 scientific prediction is unscored. The owner's slot remains `not taken (unattended)`;
owner reviews returned no unapplied instruction. No Chinese valid-result brief is created for
this failed attempt. `DIRECTION.md` retains the accepted three-root no-contact conclusion.

The next engineering discriminator is whether the narrow R02-only check change lets the real
collector preserve its exact action/native replay while still rejecting deliberate native-path
divergence. The next scientific discriminator remains the unchanged R128 comparison after an
accepted fresh implementation. Source conformance and diagnostic success cannot establish its
native-return advantage.

Evidence: `FRRIE_B01_CONTACT_ACTIVE_R128_R02_SCIENCE_CARD_20260904.md`,
`FRRIE_B01_CONTACT_ACTIVE_R128_R02_REMOTE_EXECUTION_20260904.md`, and
`FRRIE_B01_CONTACT_ACTIVE_R128_R02_RESUME_HANDOFF_20260904.md`.
