# GPT-5.6 Pro Launch Clarification — R51-AMDT Exposure Arithmetic

Date: 2026-07-16

## Review mode

Read-only launch clarification. Do not redesign AMDT, change its reward,
architecture, thresholds, seeds, team sizes, horizon, result branches, or
scientific interpretation. Resolve only the optimizer/exposure contradiction
below and return one launch-exact contract.

## Repository files to inspect

1. `docs/external-review/gpt5_6_pro/20260716_variable_team_toy_design/GPT5_6_PRO_QUESTION.md`
2. `docs/external-review/gpt5_6_pro/20260716_variable_team_toy_design/GPT5_6_PRO_RESPONSE_RAW.md`
3. `docs/external-review/gpt5_6_pro/20260716_variable_team_toy_design/DISPOSITION.md`
4. `memory/CURRENT_WORK.md`

## Accepted boundary

The controller accepts `ACCEPT_VARIABLE_TEAM_TOY_REQUIREMENTS` and the sole
`R51-AMDT-G0` route. The Anonymous Maintenance--Dispatch Task, model, PPO
objective, comparator, seeds, evaluation, M0--M2 gates, terminal branches, and
prohibitions are unchanged. No other question is open.

## Contradiction

The response simultaneously registers:

```text
N values                    5: {2,3,4,5,6}
parallel environments       16
episode / rollout           32 / 32
total transitions per arm   320,000
transitions per N per arm    64,000
episodes per N per arm        2,000
outer updates                  625
PPO epochs                       1
shared optimizer steps        3,125
specialist steps/model           625
specialist aggregate          3,125
```

But one N-specific rollout batch contains:

```text
16 * 32 = 512 transitions.
```

Therefore:

```text
64,000 / 512 = 125 N-specific batches per N
125 * 5 = 625 N-specific batches across all N
```

With PPO epoch `1` and one optimizer update per collected N-specific batch, the
consistent optimizer counts are:

```text
shared optimizer steps       625 total
specialist steps/model       125
specialist aggregate         625
```

The stated 3,125/625-per-model counts instead require five optimizer passes per
batch, equivalent to PPO epochs `5`, or require 1,600,000 transitions per arm.
Either changes a registered causal exposure.

## Controller-recommended correction

Preserve the user's fast local boundary, the declared data exposure, and PPO
epoch `1`:

```text
balanced cycles                 125
N-specific batches/cycle          5
episodes/N/cycle                  16
transitions/N/cycle              512
transitions/N total           64,000
transitions/arm total         320,000
shared optimizer steps           625
specialist steps/model            125
specialist aggregate              625
PPO epochs                          1
```

Within each cycle the five N-specific batch/substep orders use the registered
fixed RNG and are shared between treatment and matching specialists. At most
16 environments run concurrently; the five N buckets may execute sequentially
within a cycle. All existing metrics and thresholds remain unchanged.

## Requested decision

Return exactly one of:

```text
CONFIRM_R51_AMDT_625_STEP_CONTRACT
REPLACE_R51_AMDT_EXPOSURE_CONTRACT
```

Prefer `CONFIRM_R51_AMDT_625_STEP_CONTRACT` unless the original thresholds
scientifically require repeated optimization on the same data.

If confirming, restate the corrected launch table and explicitly confirm that
all original environment, model, reward, seed, metric, threshold, branch, and
no-rescue clauses remain unchanged.

If replacing, give one internally consistent table containing transitions per
N, total transitions, episodes, N-specific batches, PPO epochs/data reuse,
shared optimizer steps, specialist steps per model, specialist aggregate
steps, and expected wall clock. Explain why the larger optimizer/data exposure
is necessary. Do not offer alternatives or modify any other R51 component.
