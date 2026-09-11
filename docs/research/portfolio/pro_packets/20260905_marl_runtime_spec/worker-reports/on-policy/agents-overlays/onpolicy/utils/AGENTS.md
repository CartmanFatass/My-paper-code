# Local HMASD navigation overlay

`shared_buffer.py` stores `[time, rollout_thread, agent, ...]` arrays and emits feed-forward,
naive-recurrent, or chunked-recurrent samples. `separated_buffer.py` stores one `[time,
rollout_thread, ...]` buffer per agent and has an optional factor field used by the separated
agent-update path. Both are NumPy-backed and feed the MAPPO trainer. Source remains read-only;
this is additive navigation for the fixed SHA.
