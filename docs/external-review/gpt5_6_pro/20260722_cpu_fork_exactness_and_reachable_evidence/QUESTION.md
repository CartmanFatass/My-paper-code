# CPU Fork Exactness And What Evidence The EHC G0 Line Can Still Produce

Sent to GPT-5.6 Pro on 2026-07-22 from branch `Claude`, commit `8e63cb9`.
First external round opened from this branch. No run was launched; no
checkpoint exists.

---

```
Use the GitHub connector on private repository CartmanFatass/My-paper-code,
branch `Claude`, commit 8e63cb9. Relevant code: `_audit_row_errors` and the
batched-audit natural-branch check in ha_ctse_process/event_held_commitment_link.py
(around lines 2717-2750 and 3003-3020), `_AUDIT_CONTINUOUS_FIELDS` around line
3578, the constants in ha_ctse_process/noncalendar_commitment_testbed.py, the
`dense_batch_invariant` fixture in
tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py around line
221, and the natural-branch acceptance in
scripts/run_noncalendar_commitment_benchmark_g0.py around line 2199.

You answered our previous round on per-component replay tolerance. That answer
is implemented and is not being reopened. This is a different question one
level down, about the fork engine's own audit and about what evidence remains
reachable on the only hardware we have.

NOT VISIBLE AT THAT COMMIT. One uncommitted working-tree change:
FORMAL_EXECUTION_BACKEND in noncalendar_commitment_testbed.py is "cuda" at
8e63cb9 and is "cpu" in our tree. That is the change under discussion. The
repository already declares REGISTERED_EXECUTION_BACKENDS = ("cuda", "cpu")
with CPU admitted explicitly as a registered backend and not a fallback, and
PINNED_COLLECTOR_DIGESTS already carries a verified CPU entry which reproduces
bit-for-bit on this host.

HOST. AMD CPU, torch 2.7.0+cpu, python 3.10.20. No CUDA device is present.
CUDA is not available to us at all, not merely unselected.

WHAT HAPPENED. PROBLEM_CACHE.md records P1b: the fork engine cannot run on CPU,
citing a measured dense batch-invariance error of 5.72e-06 on a previous Intel
host. On this AMD host the same synthetic nn.Linear batch-invariance probe
measures exactly 0.0 - invariance holds. We took that as reason to doubt P1b
and recorded a decision resting on it. P1b's own text warned that the synthetic
probe is necessary but not sufficient and that "only the real fork is decisive".
We then ran the real fork on CPU:

  RuntimeError: batched audit natural branch mismatch
    {'discrete_mismatch': 0, 'continuous_error': 4.76837158203125e-07,
     'segment_equal': True, 'outcome_equal': True}

4.76837158203125e-07 = 2^-21. It is bit-for-bit the value P1b records for its
CPU failures on the previous, different-vendor host. Discrete fields, segment
identity and lifecycle outcome all match; only the continuous maximum is
nonzero. We treat P1b as standing: this CPU cannot produce fork evidence.

WHAT WE HAVE NOT MEASURED, DISCLOSED. `_audit_row_errors` returns only the
maximum over all 17 fields in `_AUDIT_CONTINUOUS_FIELDS`. It does not record
which field, which timestep, the two values, or the ULP distance. So we do not
know whether 4.768e-07 sits in `observations`, in `hidden_after`, in
`event_old_mark_component_logp`, or elsewhere, and we do not know whether it is
one ULP or many. This is the same instrumentation defect you flagged in our
replay report last round, in a second place we had not checked. We are
producing the per-field localization now and will send it; we did not want to
delay this question behind it, and we are not going to infer the field.

AN INCONSISTENCY WE FOUND. The engine requires exact equality
(`continuous_error == 0.0`, line 3013). The runner accepts
`continuous_error <= 1e-7` (run_noncalendar_commitment_benchmark_g0.py line
2199). Two different contracts for the same audit exist in the tree. Neither
admits 4.768e-07, so this did not cause the failure, but one of them is wrong
and we do not know which was intended.

A GUARD THAT IS UNSOUND AS A RESULT. The `dense_batch_invariant` test fixture is
documented as deciding "which half of the fork evidence this session can
produce", and asserts `(probe_error == 0.0) is dense_batch_invariant`. On this
host it evaluates True while the real fork fails. It would therefore license
fork evidence that cannot be produced. We have not relaxed it or repaired it
pending your ruling.

QUESTIONS.

1. Is bitwise-zero the correct contract for the fork's natural-branch audit, or
   is it the same unexecutable-form error you identified last round, one level
   down? We can argue it either way and would rather you decide. Against
   loosening: the audit's purpose is to establish that the batched
   counterfactual recomputation IS the same computation as the natural rollout,
   not merely a close one, and any nonzero value is then a real signal that
   batching changed the computation - which is precisely what invalidates the
   counterfactual. For loosening: `observations`, `hidden_after` and the stored
   likelihood components are float32 quantities recomputed under a different
   batch shape, so by your own last-round argument no fixed absolute bound is
   portable, and zero is the least portable bound of all. Which is it, and does
   the answer differ per field - exact for state that must be identical,
   scale-aware for the likelihood components?

2. Given P1b confirmed here, what does the EHC G0 line still legitimately
   produce on CPU? Our reading: G, access and the K-bins are
   backend-independent and survive; the fork-dependent counterfactual evidence
   does not. Separately, PROBLEM_CACHE P1 already blocks the A_KEEP/A_RENEW
   Replacement-C gates on BOTH backends, because the fork engine is
   deterministic-only while Replacement C is defined on held-out stochastic. If
   that reading is right, the CPU restriction costs no evidence that CUDA
   currently delivers either, and a CPU run is worth launching for the
   non-fork claims. If it is wrong, we would rather not launch.

3. `dense_batch_invariant` is falsified as a proxy for fork exactness. Should
   the gate become the real fork audit itself, run as a preflight, or should
   fork-dependent claims simply be recorded unavailable on this backend with
   the reason attached? The first is honest but costs a fork run to decide
   whether a fork run is possible.

4. `formal_evaluate` invokes the fork engine, so a CPU formal run currently
   raises mid-evaluation rather than degrading. How should it degrade - record
   a structured `fork_evidence: unavailable` with the measured audit error and
   continue producing the backend-independent claims, or refuse to start? We
   prefer the first and want it ruled on rather than chosen by us, because
   "degrade and continue" is the option that lets our own run proceed.

5. A separate, smaller question, from the tolerance work you already ruled on.
   The test
   `test_shared_event_heads_are_row_stable_under_collection_and_replay`
   asserts `report["errors"]["mark_component"] == 0.0`. On CPU it measures
   2.384e-07 and `report["passed"]` is True, since the mixed bound you froze
   admits it. The assertion is therefore stricter than the contract it exists to
   protect. Is that deliberate - is it asserting the stronger property that
   collection and replay share one evaluator and so must agree bitwise on any
   device - or should it be aligned to the frozen contract? We will not touch it
   until you say.

6. Do you require the per-field fork localization before ruling on 1 through 4,
   or is the structural question answerable now?

CONSTRAINT. No run has been launched from this branch, no result observed, no
checkpoint written. Every question above is a pre-registration question about a
specification that cannot be executed as written on the hardware we have.
```
