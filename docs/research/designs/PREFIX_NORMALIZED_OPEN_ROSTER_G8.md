# Prefix-normalized open-roster G8

Status: executable definition frozen; implementation PM-accepted and formal-
ready after Git integration.

## Question

Can a fresh direct recurrent policy recover robust absolute usability through
N=40 when the only algorithm change is replacing raw autoregressive action
prefix counts with fractions of the active roster?

This is conclusion-bearing iteration 9. G5/G6 remain closed successes through
N=16, and G7 remains closed as `NO_MODERATE_BEYOND_COUNT_G7` whatever G8
returns.

## Frozen algorithm delta

```text
algorithm=PREFIX_NORMALIZED_OPEN_ROSTER_G8
active_aggregation=sum
count_coordinate=original_log1p
environment_count_feature=log1p(N)/log1p(16)
autoregressive_prefix=prefix_action_count/N
parameter_shape=unchanged_from_G5
```

At each active autoregressive position, the three prefix action counts are
divided by the total active count N before entering both `actor_rnn` and
`action_head`. Raw integer prefix counts remain in the trajectory/replay audit,
so sampling and replay equality retain their exact meaning. The shared member
encoder, embedding sum, recurrent lifecycle state, active-set critic and action
factorization are unchanged.

The choice follows the registered eight-variant nonformal screen. It does not
claim unique causal attribution. Unselected mean-aggregation and bounded-count
prototype branches are removed from the active line.

## Task and evaluation domains

Training uses the exact G5 Generic-SHORT profiles `3→2→4→3`, `4→2→6→4` and
`5→3→7→5`, with the same reward, observation fields, action set, horizon,
membership semantics and PPO update. Evaluation covers:

1. G5 IID profiles;
2. G5 held-out profiles through N=9;
3. G7 `moderate_beyond` through N=24;
4. G7 `far_beyond` through N=40;
5. G7 `joint` scale/event-time profiles through N=40.

Every source-control profile must retain constructive utility one, finite count
features, exact actual-wave demand and unchanged lifecycle behavior.

## Formal execution

```text
authorization_token=AUTHORIZE_PREFIX_NORMALIZED_OPEN_ROSTER_G8_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
replicates=3
updates_per_replicate=250
environments_per_update=8
ppo_passes=4
evaluation_episodes_per_cell=128
evaluation_cells=33
bootstrap_repetitions=10000
model_seed_base=1381000
train_ledger_seed_base=1481000
action_seed_base=1581000
evaluation_seed_base=1681000
iid_ledger_seed=1781000
heldout_ledger_seed=1781100
moderate_ledger_seed=1781200
far_ledger_seed=1781300
joint_ledger_seed=1781400
bootstrap_seed=1881008
```

The 33 cells are three zero-checkpoint joint deterministic cells plus three
replicates × five final domains × deterministic/stochastic. All checkpoints
are newly trained; no G5 checkpoint is resumed or adapted.

## Gates and first match

Operational validity requires the exact source/token/count/runtime contract,
finite updates, replay maximum error `<=1e-6`, lifecycle validity, complete
checkpoint/cell inventory, finite `[0,1]` outcome arrays, exact source controls
and zero model drift during evaluation.

After operational validity, first match is:

1. IID deterministic CI95 LCB `<0.90` → `NO_IID_ACCESS_PREFIX_NORMALIZED_G8`;
2. held-out LCB `<0.90` → `NO_HELDOUT_ACCESS_PREFIX_NORMALIZED_G8`;
3. moderate LCB `<0.90` → `NO_MODERATE_ACCESS_PREFIX_NORMALIZED_G8`;
4. far LCB `<0.90` → `NO_FAR_ACCESS_PREFIX_NORMALIZED_G8`;
5. joint LCB `<0.90` → `NO_JOINT_ACCESS_PREFIX_NORMALIZED_G8`;
6. joint final-minus-zero CI95 LCB `<=0` →
   `NO_LEARNING_GAIN_PREFIX_NORMALIZED_G8`;
7. minimum joint replicate `<0.85` or joint stochastic mean `<0.80` →
   `UNSTABLE_PREFIX_NORMALIZED_G8`;
8. otherwise → `USABLE_PREFIX_NORMALIZED_OPEN_ROSTER_G8`.

Invalid evidence returns `INVALID_PREFIX_NORMALIZED_OPEN_ROSTER_G8` and costs
no iteration. Nonformal exercise returns
`NONFORMAL_PREFIX_NORMALIZED_G8_EXERCISE_COMPLETE` and cannot bear a conclusion.

## Protected interpretation

Success supports a usable algorithm only on the registered task and range
through N=40; it is not arbitrary-N proof or comparative advantage. Failure
does not rescue or relabel G7 and does not imply all prefix-normalized policies
fail. Asynchronous skill lifetime, skill selection, EHC and intrinsic reward
remain frozen.
