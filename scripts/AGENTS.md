# scripts/

run_<prefix>_<object>.py is one research object's entry; hmasd_*.py and schemas are
shared workflow tools. Analysis/plotting belongs in tools/analysis. Derive repository
paths from __file__; child interpreters use sys.executable or HMASD_PYTHON, never a
hard-coded user-profile interpreter. Result roots are temp/directions/<id>/exp/.
Use the exact frozen entrypoint when a card names hmasd_run.py.

A queue is a list of commands, not a scheduler. The execution method requires one fresh
actual-node admit-memory immediately adjacent to each invocation. Remote preflight &&
runner belong inside the same supervised command. A failed run retains log and partial
output; another authorized attempt gets a new root, never overwrites or silently resumes.
