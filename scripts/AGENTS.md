# scripts/

run_<prefix>_<object>.py is one research object's entry; hmasd_*.py and schemas are
shared workflow tools. Analysis/plotting belongs in tools/analysis. Derive repository
paths from __file__; child interpreters use sys.executable or HMASD_PYTHON, never a
hard-coded user-profile interpreter. New result roots are runs/<id>/<tag>/; temporary
support work stays in temp/. Retain the exact entrypoint and output contract of a named
frozen object, including hmasd_run.py and historical temp paths where bound. The notebook
links the recoverable artifacts; layout alignment is not a reason to relaunch or move them.

Prefer a simple list of commands for a queue; use scheduling when the actual workload benefits.
New result entries use hmasd_launch.py and call hmasd_admission.require_admission before
scientific effects; direct CLI invocation without the single-use admission refuses.
The kernel applies fresh actual-node memory admission immediately before release, with current
pause/lead, published-source and duplicate-claim checks. Frozen historical commands retain
their bound interface at their original sha. A failed run retains log and partial
output; another authorized attempt gets a new root, never overwrites or silently resumes.
