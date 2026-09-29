"""coupled_host_replan_timing: R1-lite (zero fits) -- a single-event subclass of D2's coupled relay
host (``event_host.py``), the ordinary re-deployment rules KEEP / cold SET-now / warm SET and the
departure small grid (``rules.py``), and the runner (``run_r1lite.py``).

D2's frozen modules (``experiments/candidates/coupled_host_joint_skills_stage1``) are imported,
never edited.  Nothing is imported here (numpy only below; no torch).
"""
