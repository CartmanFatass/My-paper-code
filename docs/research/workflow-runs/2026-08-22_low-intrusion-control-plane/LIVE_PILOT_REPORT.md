# Live Pilot Report

The file-backed pilot was exercised without formal training:

- Ordinary path: no lifecycle Hook table or control-plane prompt is configured.
- Assignment path: both seeded assignments parse and validate by file path;
  the result IDs match their assignments.
- Incident path: the synthetic Agentify E1 fences only the exact resend and
  preserves Root/CM continuation.
- Runtime path: current CPU/memory preflight selected two workers for the
  native route; manifest validation required the same width, C++ backend and
  parallel execution.
- Supervisor path: start/status/stop wrappers are explicit-only and record
  `automatic_wake=false`; no periodic model message is emitted.

Native auto-compaction was not forced by this pilot and is therefore
`UNOBSERVED`, not a defect.
