---
name: hmasd-slice-interface
description: Use when a top-level HMASD Root, Portfolio, EM/, or CM/ task receives an exact v2 message or completes a bounded session slice.
---

# HMASD Slice Interface

Read `docs/project/WORKFLOW_PROTOCOL.md` sections 3.1-3.3 and the applicable
section 4 body contract, plus the current task's role prompt. Run
`scripts/hmasd_session_envelope.py --help`, then `read-message --help` for
intake or the applicable outbound subcommand `--help`.

Pass the exact native one-line input to `read-message`. For outbound, prepare
only the body input and send the CLI's exact message to its exact recipient
once. If delivery is unknown, follow section 3.1 and observe recipient history.
For REANCHOR, run `scripts/hmasd_control_release.py verify --help` and verify
the expected release before role work resumes.
