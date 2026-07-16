# GPT-5.6 Pro R51-AMDT Design Disposition

Date: 2026-07-16

Source model: GPT-5.6 Pro (`Pro` web conversation)

Raw evidence: `GPT5_6_PRO_RESPONSE_RAW.md`

Related claim: select one genuinely task-dynamic variable-team toy environment
and the first evidence-bearing cross-episode variable-`N` learning gate.

## Disposition

**Accept the R51-AMDT environment and scientific route, pending one
launch-critical exposure clarification.**

Accepted without redesign:

- Anonymous Maintenance--Dispatch Task as the only environment.
- Stable cross-episode `N in {2,3,4,5,6}` before within-episode membership.
- Persistent stations plus short-lived jobs, fixed 32-step episodes, shared
  sparse terminal reward only, and no shaping or intrinsic reward.
- Anonymous homogeneous agents, set/pointer policy, active-only external AR
  order, no `K^N` enumeration, no dense mandatory agent-agent tensor, no agent
  ID, learned order, role label, skill latent, or KEEP/SET.
- One shared variable-`N` policy versus a capacity-matched fixed-`N`
  specialist family, with specialist access as a prerequisite.
- M0, M1, M2, INVALID, NO_ACCESS, valid shared FAIL, PASS, and no-rescue
  interpretation as stated in the raw response.
- PASS authorizes only a same-task exogenous within-episode membership gate.

## Launch blocker

The exposure and optimizer counts cannot all hold simultaneously:

```text
16 envs * 32 steps = 512 transitions per N-specific batch
64,000 transitions per N / 512 = 125 batches per N
5 sizes * 125 = 625 N-specific batches total
PPO epochs = 1
```

This implies 625 shared optimizer steps and 125 steps per specialist, 625
aggregate. The raw response instead states 3,125 shared steps and 625 per
specialist, 3,125 aggregate. Those counts require five optimizer passes per
batch or five times the registered transitions, contradicting PPO epoch `1` or
the 320K exposure.

The controller recommends preserving 320K transitions, 64K per `N`, and one
PPO epoch, grouping the work as 125 balanced cycles containing five
N-specific batches. That yields 625 shared steps and 125 per specialist.
Because optimizer exposure is part of M0 and can change access, this correction
must be confirmed before implementation or formal registration.

No environment implementation or experiment is authorized until the tracked
launch clarification is answered and dispositioned.
