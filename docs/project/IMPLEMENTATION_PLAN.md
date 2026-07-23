# Open-roster direct MVP G5 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hash handoffs
> are disabled.

```text
active_implementation=OPEN_ROSTER_DIRECT_MVP_G5
implementation_status=FORMAL_COMPLETE_CLOSED_SUCCESS
design=docs/research/designs/OPEN_ROSTER_DIRECT_MVP_G5.md
backend=cpu
torch_threads=1
primary_goal=absolute_dynamic_roster_usability
comparative_advantage_requirement=none
asynchronous_skill_lifetime=frozen
skill_controller=absent
formal_iteration=6
new_chain_iterations_remaining=7
```

## Goal

Turn the access-valid direct primitive recurrent policy into a genuinely
`N`-independent dynamic-roster MVP. One checkpoint must operate across several
within-episode membership schedules and transfer to unseen active counts. The
model may use ordinary recurrence and active-set context; this stage does not
isolate a novel mechanism or claim advantage.

## Task 1 — Remove the fixed collector width from the algorithm contract

Make `DirectPrimitiveARPolicy`, trajectory replay and evaluation derive their
operational width from the supplied roster batch. Parameter shapes remain
independent of width. Inactive padding is operational only, carries no identity
embedding and cannot change active logits or values.

Focused proof: two different padded capacities containing the same active set
produce the same deterministic active actions, log probabilities, value and
next hidden state; replay remains exact.

## Task 2 — Add the open-roster task family

Retain Generic-SHORT external task semantics while replacing the single
`4 -> 2 -> 6 -> 4` schedule with several generated schedules. Every episode
contains temporary leave, rejoin, genuine join and terminal leave. Training and
held-out profiles differ in active counts; held-out evaluation also uses a
larger operational capacity than training.

Focused proof: constructive utility is 1 for every profile, anonymous
permutation changes no outcome, absent lifecycle hidden state freezes, rejoin
restores it, genuine join starts at zero and no lifecycle key enters the model.

## Task 3 — Add one train/evaluate/analyze path

Use the existing direct PPO core and CPU-only runtime. The runner records exact
profile exposure, transitions, active rows, optimizer steps, replay errors,
checkpoint restoration and per-cell absolute utility. A nonformal exercise
uses reduced counts and is rejected as conclusion-bearing evidence.

Focused implementation checks pass `6/6`. The two-update full-path exercise at
`logs/nonformal_open_roster_direct_g5_20260723_pm1` and the 20-update learning
probe at `logs/nonformal_open_roster_direct_g5_probe20_20260723_pm1` are both
operationally valid and nonformal. Replay errors are zero, source controls have
constructive utility 1 for all five profiles, and the larger held-out capacity
is exercised. The formal G5 budget and first-match outcomes are now frozen in
the design. Assign the exact foreground `train -> evaluate -> analyze` pipeline
to the registered silent experiment operator after Git integration.

## Formal disposition and next boundary

Formal iteration 6 is operationally valid and returns
`USABLE_OPEN_ROSTER_DIRECT_G5`. IID deterministic utility CI95 is
`[0.9985352, 0.9994303, 1.0]`; held-out deterministic utility CI95 is
`[0.9828880, 0.9939927, 1.0]`; every stability and gain gate passes. G5 is now
closed as the usable open-roster base. It does not establish EHC, skill,
lifetime, arbitrary-count scaling or algorithmic superiority.

The next active work is a zero-compute G6 derivation that isolates zero-shot
count-scale transport from membership-event-time transport while reusing the
frozen G5 checkpoints without tuning. Seven conclusion-bearing rounds remain.
