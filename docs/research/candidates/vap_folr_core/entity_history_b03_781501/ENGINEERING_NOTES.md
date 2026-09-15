# FOLR entity-history B03 engineering notes

Scope: none.

B03 is selected explicitly with `--fresh-learning-b03`. It reuses the B01/B02
learner, environment, replay, RNG reset, evaluation, MEI, and publication path while
binding object `FOLR_ENTITY_HISTORY_B03_781501` to training/evaluation seeds
781501/1781501. Both arms construct fresh learners. BANK accepts only the collected
B03 Generic identity; an incomplete or wrong-exposure Generic can accompany BANK-only
facts but cannot produce `pair_primary`.

The focused committed-source check is:

```bash
/home/wu/.venvs/hmasd/bin/python -m pytest -q \
  --basetemp temp/directions/vap_folr_core/test/entity_history_b03_<tag> \
  tests/experiments/candidates/vap_folr_core/entity_history_b03/test_b03.py
```

Create arm output directories below
`temp/directions/vap_folr_core/exp/entity_history_b03_781501/`, then invoke
`GENERIC.sh <sha> <checkout> <generic-output>` followed by
`BANK.sh <sha> <checkout> <bank-output> <generic-output>/summary.json` through the
configured exact-SHA `agent-task` route. Each script performs the adjacent memory
admission and records whole-invocation wall/RSS/CPU through GNU time. The scripts do
not impose a wall timeout: `--cap-seconds 3600` remains the reused fresh-mode planning
reference recorded in the summary, while the ordinary supervisor and monitor track
actual progress.
