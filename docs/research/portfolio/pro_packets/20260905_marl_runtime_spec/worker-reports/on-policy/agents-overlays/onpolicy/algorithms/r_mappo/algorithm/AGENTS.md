# Local HMASD navigation overlay

`rMAPPOPolicy.py` is the policy façade (`get_actions`, `get_values`, `evaluate_actions`, `act`).
`r_actor_critic.py` builds the actor from local observations and the critic from centralized or
local value inputs. Recurrent behavior is implemented by `algorithms/utils/rnn.py`. This is an
additive survey overlay for the fixed snapshot; upstream code remains read-only.
