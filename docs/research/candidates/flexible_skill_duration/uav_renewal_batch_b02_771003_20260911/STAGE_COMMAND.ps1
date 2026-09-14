param([Parameter(Mandatory = $true)][string]$SourceSha)
# Run from the existing codex/fsd checkout. One allocated source staging command; scientific launch remains separate.
@'
import datetime, json, pathlib, subprocess, sys, time
ev = pathlib.Path("docs/research/candidates/flexible_skill_duration/uav_renewal_batch_b02_771003_20260911")
cmd = [sys.executable, "tools/experiments/fsd_stage_source.py",
       "--control-root", "C:/Projects/HMASD", "--sha", sys.argv[1],
       "--destination", "/home/wu/hmasd-worktrees/fsd-uav-renewal-batch-b02-771003-20260911",
       "--commands-dir", "docs/research/candidates/flexible_skill_duration/uav_renewal_batch_b02_771003_20260911",
       "--receipt", str(ev / "STAGING_READBACK.json"), "--seconds", "45"]
started = time.monotonic()
receipt = {"command": cmd, "outer_limit_seconds": 45,
           "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    result = subprocess.run(cmd, capture_output=True, timeout=45)
    receipt.update(returncode=result.returncode,
                   stdout=result.stdout.decode("utf-8", errors="replace"),
                   stderr=result.stderr.decode("utf-8", errors="replace"))
except subprocess.TimeoutExpired as exc:
    receipt.update(returncode=None, error="external complete-command timeout",
                   stdout=(exc.stdout or b"").decode("utf-8", errors="replace"),
                   stderr=(exc.stderr or b"").decode("utf-8", errors="replace"))
receipt["complete_helper_wall_seconds"] = time.monotonic() - started
receipt["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt["includes"] = "Helper interpreter/startup, transport, readback, its receipt publication, stdout and exit."
receipt["outside_this_interval"] = "This caller's setup and collection of the command receipt; charged in outer tool wall."
(ev / "CHECK_COMMAND_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if receipt["returncode"] == 0 else 1)
'@ | python - $SourceSha
exit $LASTEXITCODE
