# Disposition: R36 Access-Instrument Review

- Source model: GPT-5.6 Pro / ChatGPT web `Pro`
- Date: 2026-07-15
- Related claim: R36 implementation/estimand validity, the meaning of the
  `3.855x` coverage change with zero sparse access, the Alice--Bob hidden-task-
  identity audit, and the single next access-instrument boundary
- Raw evidence: `RESPONSE_RAW.md`
- Disposition: **ACCEPT THE R36 VERDICT AND R37 ROUTE; MODIFY THE CONTROL TO
  MATCH ACTOR INPUT CAPACITY**

## Accepted

1. R36 is a valid `FAIL_M1_RETIRE_R36_AEM`. No audited implementation defect
   changes its estimand or permits a rerun.
2. The treatment demonstrably changed natural visitation: mean 625-cell joint
   coverage rose from `0.016575` to `0.063900`, and the paired interval was
   wholly positive. This establishes successful undirected state-breadth
   expansion under the registered diagnostic only.
3. Zero treatment collections, zero cycle success, and zero paired collection
   effect establish that this broader coarse visitation did not provide first
   sparse task access. Coverage cannot override M1 and is not a contact proxy:
   a `1.6`-wide position bin is coarser than the `0.70` contact radius.
4. The current actor information contract is an upstream benchmark defect for
   access comparison. The active plate and target are randomly initialized and
   hidden from the decentralized actors while the centralized critic sees
   their identities and clocks. The next boundary must test task access after
   exposing only the current active identities.
5. R37 is accepted strictly as an observation-substrate validity gate. It is
   not a skill, intrinsic-reward, exploration, hierarchy, or paper-level
   contribution.

## Registered R37 Clarification

The response requires equal network size while giving only one arm four extra
identity inputs. To make that contract executable and capacity-matched, both
arms use the same 16-value actor observation layout:

```text
[original 12 values,
 active-plate slot (2),
 active-target slot (2)]
```

- `identity_visible`: the four slots contain the current true one-hot values.
- `identity_masked`: the four slots are constant zero, preserving the original
  actor information semantics while matching input width and parameter count.

The existing 19-value centralized critic state is unchanged in both arms. No
clock, contact, collection/progress flag, reward-derived field, future state,
distance shaping, or oracle action enters the actor. Both arms train only the
existing constant-code recurrent actor and centralized critic from the same
neutral zero-step initialization; all skill, high-controller, KEEP/SET,
posterior, and intrinsic paths remain inactive.

The exact formal exposure, gates, mutually exclusive outcomes, and prohibited
changes are registered once in `memory/ExpRecord.md`. A valid R37 PASS can
establish only that the repaired Alice--Bob observation contract has a positive
access floor. A valid FAIL retires sparse Alice--Bob as an algorithm-comparison
gate under the tested horizon and budget.
