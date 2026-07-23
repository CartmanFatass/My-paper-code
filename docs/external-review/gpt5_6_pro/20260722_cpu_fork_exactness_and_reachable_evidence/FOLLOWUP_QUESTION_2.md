# Follow-up 2: executed sampling CDFs, per call site

Sent 2026-07-22 in the same conversation.

---

```
Sampling-CDF measurement, broken down per call site so the vacuity question is
answered rather than assumed. Your numerical correction is accepted: the mixed
bound at magnitude 0.2560406625 is 1.1220897e-6, not the 1.0000122e-6 we quoted
- we dropped a digit. The observed 1.1920929e-7 is about 10.6% of it.

METHOD. The event gate is built inline
(`event_uniforms.unsqueeze(-1) > torch.cumsum(torch.softmax(logits, -1), -1)`),
so there is no helper to wrap. We wrapped the CDF-forming operations in the
torch namespace itself - torch.softmax, torch.cumsum, F.log_softmax - which
catches every sampling path wherever implemented, and attributed each call to
its source line. For every call and row we keyed on the exact bytes of the
input row and recorded the exact bytes of the output row, flagging any key that
produced different output bytes at two different leading widths.

RESULT.

  event categorical CDF
    torch.softmax @ event_held_commitment_link.py:958
      62 calls, 1596 distinct rows, 204 rows compared at >=2 widths, 0 violations
    torch.cumsum  @ event_held_commitment_link.py:958
      62 calls, 1575 distinct rows, 206 rows compared at >=2 widths, 0 violations
    widths seen: 14,17,19,20,21,22,23,25,26,28,29,30,31,32,34,35,36,37,38,
                 40,41,42,43,44,45,46,48,53,54,55,56,65,68

  event categorical log-probability
    F.log_softmax @ event_held_commitment_link.py:1016
      62 calls, 1596 distinct rows, 204 rows compared at >=2 widths, 0 violations

  primitive categorical path
    F.log_softmax @ dynamic_roster_direct.py:286
      1488 calls, 15482 distinct rows, 0 rows compared at >=2 widths
    torch.cumsum  @ dynamic_roster_direct.py:294
      1488 calls, 15365 distinct rows, 0 rows compared at >=2 widths
    widths seen: [16] only

  total violations across all sites: 0

WHAT THIS DOES AND DOES NOT ESTABLISH.

The event categorical CDF is directly covered and exact. 206 identical queries
were genuinely evaluated at two different packed widths and the executed
cumulative distribution agreed bitwise every time. That is your "causal gate"
for the event sampler, measured rather than inferred.

The primitive categorical CDF is NOT covered, and we want to be exact about why
rather than report a pass. Our instrument recorded zero cross-width comparisons
there because the primitive sampler is only ever evaluated at width 16 -
FORMAL_NUM_ENVS - in this fixture. So the measurement proves nothing about
primitive width-invariance. What it does show is that the packing change the
fork performs does not reach the primitive policy at all: the fork drops the
focal request from the packed event/mark batch, and the primitive forward step
(event_held_commitment_link.py:1109 -> arm.base.forward_step) runs at the fixed
environment width regardless.

If that reading is right, primitive width-invariance is inapplicable here rather
than unverified, and the requirement should be restated as an invariant to
assert - "the primitive sampler is evaluated at the registered environment width
on both the source and the natural branch" - rather than a numerical comparison
to perform. We would rather you rule on that than have us assert it.

STILL OUTSTANDING FROM YOUR LIST. We have not yet built the coordinate-bound
source-natural pairing that binds joint coordinate [4, 1] and component
coordinate [4, 1, 7] to the specific source and natural call identifiers and
packed widths. That is provenance work in the production audit rather than a new
numerical hypothesis, and it belongs with prelaunch item 2. We have not started
it because it is protected-semantics implementation and we wanted your reading
of the primitive result first.

QUESTIONS.

1. Does the event-CDF result close that half of your requirement?

2. Is the primitive analysis right - inapplicable because the fork never varies
   that width - and if so, should it become an asserted structural invariant
   rather than a width sweep? If you disagree, what would you have us measure,
   given that a synthetic width sweep of the primitive head is exactly the kind
   of proxy you ruled cannot license anything?

3. With event CDF exact, mu/sigma/logits exact, event_u and all realized samples
   exact, every causal field exact, and only the two derived likelihood records
   moving - is causal_identity_passed now established for this fixture, pending
   only the coordinate binding? Or does the coordinate binding have to land
   before you will credit it?
```
