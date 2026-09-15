# Independent native engineering review

Author: `/root/lcac_b01_code_review`, registered `hmasd-reviewer`, Astra/high. Parent: LCAC DM `/root`. Reviewed diff `22260a8e3..26e23ff3`. The following is the full final response received natively, transcribed without changing its substantive text. No native experiment was invoked by the Reviewer.

---

One material finding in reviewed commit `26e23ff3`:

- **P2 — Incomplete wall-time boundaries:** `study.py:74,83,118,124–126` excludes shared model initialization from arm timers and samples pair elapsed before resource collection and summary publication. These fields cannot represent complete invocation costs. Label their actual scopes, record shared setup, and use enclosing process measurements through publication. DM has acknowledged this repair.

No material defect found in reward/action binding, prefit baseline freezing, factual Q fitting, advantage normalization, gradient isolation, recurrent ordering, seed pairing, or primary aggregation.

Independent tensor-only checks verified:

- Full `[2,256,5]`, chunk32 replay against sequential actor execution: maximum difference **0**.
- Other agents unchanged after perturbing one agent’s observations.
- Nonlinear focal-Q enumeration and clipped-policy derivatives against independent calculations: maximum difference **2.98e-8**.
- Counts: **147,456 native ticks**, **1,024 Adam calls**, **2,293,760 Q baseline rows**.

Scope: **406 source lines**, including **23 runner lines**; within limits. CPU telemetry needs explicit accounting scope under runtime §6, reconciling the current “§4 additions: none” statement. No other prohibited machinery identified.

Residual limits: no native experiment was executed for this review; actual remote topology, complete costs, learner behavior and final artifacts remain runtime evidence. Synthetic checks establish implementation behavior, not scientific efficacy. Same-batch timing correction remains available for review.

---

## Full same-batch correction response

No material finding in timing correction `133218a8`.

The renamed fields accurately describe their measurement boundaries; shared setup is recorded separately. Removing in-run CPU/resource telemetry resolves the scope discrepancy and optional-module publication dependency. No stale consumers of the removed fields were found in the assigned code/tests.

Scientific computations, RNG, exposure and primary aggregation are unchanged. No additional probe was warranted.

The original timing finding is resolved in source and reporting scope. Complete invocation wall and peak RSS remain dependent on the planned enclosing GNU-time measurement; its actual output has not been reviewed here.
