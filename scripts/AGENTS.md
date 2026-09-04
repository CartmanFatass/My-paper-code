# scripts/

Two kinds of file live here and nothing else:

- `run_<prefix>_<object>.py`: the result-bearing entry point of one scientific object (99 today).
  `<prefix>` is the direction's script prefix from the column in `docs/research/RESEARCH_MAP.md`
  (`cbsc`, `vnfc`, `scdmp`, `ucope`, `fsd`, …); `<object>` is the science-card id. Research tier:
  `argparse`, a seed argument, one `summary.json` per run, the launch sha in the summary, under
  600 lines (`docs/project/ENGINEERING_SCOPE_SPEC.md` §3, §5).
- `hmasd_*.py` with `schemas/`: core-tier workflow tools. `hmasd_resource_preflight.py`
  (mandatory admission), `hmasd_run.py` (run manifest wrapper, used when a card names it as the
  frozen entry point), `hmasd_platform.py`, `hmasd_file_fingerprint.py`,
  `hmasd_science_capabilities.py` (the isolated analysis environment catalogue),
  `hmasd_operator_result.py` (imported by `hmasd_run.py promote`).

Analysis, plotting and screening scripts belong in `tools/analysis/`, not here.

## Rules

- No absolute interpreter or user-profile paths. Use `sys.executable`, or
  `os.environ.get("HMASD_PYTHON", sys.executable)` when a child interpreter is launched; derive
  the repository root from `__file__`.
- Immediately before every result-bearing run, resume or queue element:
  `python scripts/hmasd_resource_preflight.py admit-memory --out <receipt.json>` (both physical and
  effective available memory ≥ 4 GiB, `--out` required) on the actual execution node. The receipt
  admits only the adjacent invocation in the same execution context. On the configured remote route
  it is joined to the exact runner by `&&` inside the same `agent-task` command, whose task facts
  record the execution host. That is the only admission; no other receipt, witness or guard is
  added (scope spec §4).
- A queue is a list of commands run in order with one preflight each; it is not a scheduler.
- Before a sweep, the runner reports its cost law (wall time per unit of the swept quantity) so
  the card can project cost per arm; the machine-time cap applies per arm.
- Output goes under `temp/directions/<direction-id>/exp/`; nothing is written to the repository
  root or loose under `temp/`.
- A run that fails leaves its log and partial output in place; the next attempt is a new run
  directory at a new sha if a repair was needed, the same sha otherwise. Nothing is resumed.
