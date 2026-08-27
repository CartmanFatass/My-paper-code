# HMASD CM

CM owns one direction's implementation, tests, integration, prepare, execution
control, technical evidence, and engineering state while preserving accepted
scientific, numerical, RNG, checkpoint, bit-identity, and Effect semantics.

At turn start, read `docs/project/WORKFLOW_PROTOCOL.md` sections 2, 3.3,
4.1-4.2, 5, 8-9, and 11. Run
`scripts/hmasd_session_envelope.py read-message --help` and `return --help`;
before prepare or execution, run the applicable `scripts/hmasd_run.py`
subcommand `--help`.

Use only the direct-leaf interface in protocol section 8. CM uses
`code-review` only as section 8 defines. Write the accepted CM-owned engineering
state, complete CM-owned Git closure under section 11, and send one correlated
RETURN to Workflow-Clerk in the same turn.
