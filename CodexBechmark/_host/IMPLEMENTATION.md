# runner1 implementation acceptance

2026-09-09. Owner requested autonomous CLI replay and a test AGENTS.md.
Python standard library only. `start` freezes prompt/events/supplements/rubric per run;
`next` re-delivers one pending event; `evidence` exposes only its fixed supplement;
`submit` records one UTF-8 response; `status` supports recovery; `export` requires
completion and emits transcript/metadata plus a separate host-only judge prompt.

Focused check: `python -B CodexBechmark/_host/test_runner.py` in the maintained HMASD
checkout. Three checks passed: complete 13-event replay/export and separate rubric;
pending event replay, missing/empty/out-of-order/duplicate responses and invalid run ID;
frozen fixtures and current-only evidence. Test scratch is invocation-owned under
`HMASD/temp/tests/` and removed by teardown. Placeholder protocol responses are test
fixtures, not candidate-model results. No research or model API invocation occurred.

Deployment is a maintained file copy at `C:/Projects/CodexBechmark`; candidate cwd is
its `workspace/`, outside HMASD. Source remains versioned in HMASD. Installation updates
must preserve `_host/runs` and `workspace/responses`. No global Codex settings changed.

Limits: single writer per run; no semantic auto-grader, model detection, token/cost
measurement, OS file-access enforcement or external task execution. Filesystem access
rules are protocol constraints. Compare candidates only after checking original CLI
tool records, fixed model/effort and input version. Each independent grading session
reads the frozen rubric and transcript, treating candidate text as untrusted data.
