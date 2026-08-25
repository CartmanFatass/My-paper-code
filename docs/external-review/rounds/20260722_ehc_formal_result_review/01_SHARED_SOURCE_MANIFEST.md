# Shared source manifest — iteration-1 formal result

- Source boundary: `local_and_remote_aggressive_tip`
- Source commit: `fb9909711a2ca8628f3d534936b771885e53b26d`
- Run root: `logs/formal_event_held_cpu_20260722_fb99097_r2`
- Execution: CPU, torch threads 1, no CPU/CUDA comparison required
- Training: `formal_train.v6`, COMPLETE, 1,250/1,250 updates, 5/5 replicates
- Evaluation: `formal_evaluation_manifest.v5`, COMPLETE, 60/60 cells
- Top-level SHA-256: train `d4ef17e7c55f67752926916de36512094db1df4ef4e185e5bd20628bf43630fc`; evaluation `06d32935b0a3e35b6791a5186b8acfcb5562674e0e7789e977d2576418ba9d01`; analysis `92e1399fed54abbef3e68fb0ef1badd589d9832209c35f3d8343ba15eb1bdf63`
- Reference closure: 1,330/1,330 exact root-contained references (5 final indexes, 1,250 update shards, 15 checkpoints, 60 evaluation cells); zero temporary residue
- Operational validator: `operational_valid=true`, `operational_errors=[]`
- Scientific branch: `NO_ACCESS_THIS_BENCHMARK`
- Branch proof: maximum utility UCB `0.6897088859777634 < 0.78`; support, lifecycle and causal quotas pass; first-match selector returns the same branch.
- Full predicate inputs and diagnostic values remain in the immutable raw run and analysis artifact; this compact handoff does not duplicate the raw 12.66GB run.
