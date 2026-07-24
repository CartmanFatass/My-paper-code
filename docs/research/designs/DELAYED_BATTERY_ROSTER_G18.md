# Delayed battery roster G18 toy source

```text
status=INFORMATION_GATE_PASS
source_kind=fresh_toy_not_uav
capacity=6
horizon=12
initial_active=4
temporary_charge_leave_time=6
temporary_charge_members=2
demand_spike_times=6_to_9
rejoin_fresh_join_terminal_leave_time=10
energy_per_effort=0.25
inactive_charge_per_step=0.25
reward=served_demand_fraction_only
formal=false
iteration_consumed=false
```

## Scientific boundary

The source asks whether a roster policy can assign equal current service in a
way that preserves later service capacity. It is independent of UAV radio,
motion, station geometry, queueing, safety penalties and every closed G17
source/result. The only reused ideas are fixed lifecycle rows, active masks and
bounded continuous actions.

At steps 0--5 demand is 1 and four lifecycles are active. At step 6 two
announced rotation lifecycles leave and charge while demand rises to 2. At step
10 they rejoin, one fresh lifecycle joins and one persistent lifecycle leaves
terminally. Active counts are exactly:

```text
[4,4,4,4,4,4,2,2,2,2,4,4]
```

An active effort `e in [0,1]` serves `e` units and consumes `0.25*e` battery.
Physical service is clipped by available battery. Temporarily absent charging
rows gain 0.25 battery per step up to 1. No battery term appears in reward or
utility. Inactive tanh-action rows must be exactly zero; temporary rejoin keeps
its lifecycle state, fresh join starts with full battery/zero prior action, and
terminal leave never acts again.

## Information gate

The constructive controller spends the low-demand work on members that will
charge, then preserves the persistent members for the doubled demand. The
myopic comparator divides only current demand equally among current members.
The sequence intervention changes only the first-step owner of one identical
unit of service and then returns both paths to the constructive continuation.

The gate requires all of the following without a statistical threshold:

1. constructive utility is exactly 1 across three lifecycle-slot permutations;
2. myopic utility is below 0.90 and the constructive gap exceeds 0.10;
3. natural and intervened current service/utility are exactly equal;
4. their next persistent battery differs and later service utility differs;
5. lifecycle schedule, fresh/rejoin/terminal ownership and inactive action zero
   remain exact;
6. no UAV module, RNG, training, formal artifact or conclusion-bearing result
   is involved.

Implementation: `ha_ctse_process/delayed_battery_roster_g18.py`.
Focused proof: `tests/ha_ctse_process_delayed_battery_roster_g18_test.py`.

## Next algorithm boundary

`FAST_SLOW_SEPARATED_CREDIT_G18_ALGEBRA_PROTOTYPE` passed its focused algebra,
gradient, replay, lifecycle and dual-source interface tests. Its exact bounded
screen is frozen in `FAST_SLOW_SEPARATED_CREDIT_G18.md`. The exact TD(0)
candidate is closed and may appear only as a frozen comparator.
