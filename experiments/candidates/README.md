# Isolated research candidates

This directory contains proof-sized candidate experiments that are not part of
the production HA-CTSE runtime. Each candidate owns one subdirectory containing
only its local schema, deterministic treatment, and executable evidence logic.

- Production code must not import candidate modules.
- Tests mirror the candidate path under `tests/experiments/candidates/`.
- Public science-to-code evidence lives under `docs/research/candidates/`.
- Code moves into `ha_ctse_process/` only after a separate production-integration
  task identifies a real shared consumer.
- Parked, retired, or replaced candidates are deleted as a complete family; Git
  is the archive. Compatibility wrappers and historical-code directories are
  not created.
