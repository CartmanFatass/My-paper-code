# Follow-up: localization and decision-kernel classification

Sent 2026-07-22 in the same conversation, after the structural ruling.

---

```
Localization and decision-kernel classification, as you required for the
AMD-host disposition. Both are measurements, not inferences.

MEASUREMENT 1 - per-field localization of the natural-branch mismatch.

Wrapped `_audit_row_errors` non-invasively and re-ran
test_three_branch_width16_batched_audit_matches_sequential_oracle on CPU.
Reproduces in 5 seconds. Exactly two of the seventeen continuous fields are
nonzero:

  event_old_mark_component_logp
    absolute_error 1.1920928955078125e-07
    stored -0.2560405433177948   replayed -0.2560406625270844
    float32 ULP at that magnitude 2.9802322387695312e-08
    ulp_distance 4.0
    3 nonzero of 3648 elements, worst coordinate [4, 1, 7], shape [76, 6, 8]

  event_old_joint_logp
    absolute_error 4.76837158203125e-07
    stored -4.2429704666137695  replayed -4.242970943450928
    float32 ULP at that magnitude 4.76837158203125e-07
    ulp_distance 1.0
    1 nonzero of 456 elements, worst coordinate [4, 1], shape [76, 6]

Every other field is bitwise identical: observations, rewards, hidden_before,
hidden_after, prefix_counts, primitive_z, event_inputs, event_u, event_z_pre,
event_new_z, candidate_u, candidate_z, old_log_probs, old_values,
event_old_cat_logp. discrete_mismatch is 0, segment_equal and outcome_equal
both hold.

So your entire exact-identity list from section 1 is satisfied. The only two
nonzero fields are in the derived-record class you assigned to the frozen
replay rules.

MEASUREMENT 2 - the decision kernel, compared exactly.

You said per-field localization alone may not settle Case B, and that the
decision-producing kernel must be compared directly. The event/mark decision
kernel is `_row_stable_event_heads` returning (logits, mark_output), with
mu, sigma = _normal_parameters(mark_output) a pure function of mark_output.

We wrapped that helper and, for every call and every row, keyed on the exact
bytes of the input row together with the exact bytes of event_head.weight,
event_head.bias, mark_head.weight and mark_head.bias. Identical key means an
identical mathematical query. We then recorded digests of that row's logits, mu
and sigma, and flagged any case where one key produced different output bytes
at two different packed widths.

  head calls                          62
  distinct (parameters, input row) keys  1611
  packed widths observed              14,17,19,20,21,22,23,25,26,28,29,30,31,
                                      32,34,35,36,37,38,40,41,42,43,44,45,46,
                                      48,53,54,55,56,65,68
  keys actually evaluated at two or more different widths   203
  width-dependent output violations   0
  same-width nondeterminism           0

The 203 figure is reported so a pass cannot read as vacuous: 203 identical
queries genuinely were evaluated at two different packed widths, for example
56 and 68, and logits, mu and sigma agreed bitwise every time.

WHAT WE HAVE NOT INSTRUMENTED, DISCLOSED. We compared the event/mark kernel
directly. We did not directly instrument the primitive categorical logits or
CDF. Our indirect evidence there is that old_log_probs, primitive_z and the
sampled actions are all bitwise identical in measurement 1, but that is stored
output rather than the kernel itself, which is exactly the substitution you
warned against. We will instrument it directly if you want it before ruling.
We also have not verified that the specific n versus n-1 drop the fork performs
on the focal row is among the 203 compared pairs; we verified that identical
queries at different widths agree, not that every width transition the fork
uses was exercised.

CLASSIFICATION WE READ FROM THIS, FOR YOUR CONFIRMATION OR REJECTION.

This is your Case B with the benign resolution: the underlying kernel is exact
and only post-decision density arithmetic differs. Under the corrected typed
contract, causal_identity_passed would be true, and derived_record_fidelity
would be evaluated under the frozen replay rules, where both values pass with
large margin - 1.192e-07 against a mixed bound of about 1.0000122e-06, and
4.768e-07 against about 3.02e-06, with expm1 ratio drift about 4.8e-07 against
the 1e-4 cap.

If that is right, then P1b is not confirmed on this AMD host, the fork is
admissible here under the corrected contract, and the CPU run is not restricted
to the fork-independent claims. We are aware this is the convenient conclusion
and that we reached the last convenient conclusion too early on a
known-insufficient measurement, which is why we are putting it to you rather
than acting on it.

QUESTIONS.

1. Do you confirm Case B benign, or does something in measurement 1 or 2 fail
   to establish it?

2. Do you require direct primitive-kernel instrumentation, and the explicit
   demonstration that the fork's own n versus n-1 width transition is among the
   compared pairs, before the AMD host is credited with fork capability?

3. If confirmed: does the required prelaunch corrections list from your ruling
   change? Items 1, 3, 4, 5, 6 and 7 look independent of this result and still
   required. Item 8 - "correct P1 and reopen P1b" - would become "correct P1 and
   close P1b for this host, retaining the Intel-host record". Item 2, exact
   audit coverage for the sampling kernels, would become the permanent
   implementation of measurement 2 rather than a diagnostic. Is that right?

4. Does confirming fork capability on this host license the complete G0
   disposition, or does the partial-evidence machinery still need to exist first
   because capability is per-row and can fail at formal coordinates that this
   test did not reach?
```
