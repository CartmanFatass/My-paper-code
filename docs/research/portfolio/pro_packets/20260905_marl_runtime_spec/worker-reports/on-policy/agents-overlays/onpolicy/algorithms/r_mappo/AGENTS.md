# Local HMASD navigation overlay

`r_mappo.py` selects feed-forward, naive-recurrent, or chunked-recurrent buffer generators for
each PPO epoch and performs one actor/critic update per yielded sample. `algorithm/rMAPPOPolicy.py`
wraps actor and critic; `algorithm/r_actor_critic.py` moves NumPy inputs to the selected device and
executes MLP/CNN plus optional GRU. This local file indexes the fixed SHA and does not authorize
source edits.
