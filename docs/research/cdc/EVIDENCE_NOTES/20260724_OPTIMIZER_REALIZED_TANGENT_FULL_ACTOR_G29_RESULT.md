# G29 optimizer-realized-tangent full-actor bounded result

```text
status=COMPLETE
formal=false
iteration_consumed=false
accepted_source_commit=212bbb192b6a4f6c08be8ab250313d723ad0fcfc
accepted_run=logs/nonformal_optimizer_realized_tangent_full_actor_g29_20260724_212bbb1_pm2
branch=NONFORMAL_NO_DELAYED_ACCESS_REALIZED_TANGENT_G29
iterations_remaining=8
```

## Evidence closure

The repaired CPU one-thread artifact completed all three mechanical stages.
Replay and applied-parameter identity error are exact zero, every Adam actor
state advances exactly once per pass, lifecycle and ownership pass, and the
minimum realized-displacement immediate dot is positive. The first attempt at
source `42cba77b43015b465bcd6832676868db50488c72` emitted no result because the
shared G19 reducer required an internal legacy metric key. Its temporary input
adapter is absent from persisted G29 rows and metrics. The failed artifact is
operational only and consumes no iteration.

## Registered result

G17 remains strong: IID/held-out utility is `0.9609785/0.9566336`, minimum
episode `0.9324918`, effort/mix correlation `0.9921637/0.9937766`, and all
mapping and gain gates pass.

G18 loses access. Utility falls from the fast anchor `0.5833333` to
`0.5167945`, gain is `-0.0665388`, spike and minimum-step utility are exact
zero, and rotating effort share is `0.5003782`. The registered first-match
branch is `NONFORMAL_NO_DELAYED_ACCESS_REALIZED_TANGENT_G29`.

The realized constraint triggered on 234 of 600 G18 actor passes and the actor
maximum change was only `0.0807724`; G28 triggered its raw constraint on 120
passes and reached `0.8898338` spike utility. The actual-step constraint is
therefore more restrictive in this source, not a relaxation of G28.

## Scientific disposition

G29 is closed without optimizer-state rollback, threshold, budget, seed or UAV
rescue. It does not license formal compute. The next smallest axis returns to a
pre-Adam guarantee but removes raw channel-magnitude dominance: combine the two
global unit gradient directions equally. This preserves the complete successor
direction and guarantees a nonnegative raw immediate dot algebraically, without
a projection coefficient or new threshold.
