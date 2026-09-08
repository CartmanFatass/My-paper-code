"""Sequential local P16 phases. Production calls are injectable for inert tests."""

import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

from .inputs import BODIES
from .processes import remaining

HERE = Path(__file__).resolve().parent
REMOTE_REL = HERE.relative_to(HERE.parents[3]).as_posix() + "/remote.py"


def map_deadline(anchor, local_remaining):
    # A remote sample predates its receipt. Giving it only the remainder at receipt
    # already charges both transit legs. 1% and 1 s conservatively cover clock-rate
    # error and ordinary timer/exec quantization; neither wall-clock epoch is used.
    budget = (local_remaining - 1.0) / 1.01
    if budget <= 0:
        raise TimeoutError("No time remains for the remote boundary")
    return anchor["seconds"] + budget


def ssh_command(args, mode, anchor=None, deadline=None):
    command = [args.remote_python, args.remote_repo + "/" + REMOTE_REL, mode]
    if mode == "anchor":
        command = ["/usr/bin/timeout", "--signal=KILL", "1s", *command]
    else:
        command += ["--python", args.remote_python, "--repo", args.remote_repo,
                    "--out", args.remote_out, "--deadline", str(deadline), "--boot", anchor["boot"],
                    "--handle", args.handle, "--candidate", args.candidate,
                    "--retained", args.retained, "--uv", args.uv, "--source", args.source,
                    "--seed", str(args.seed), "--supervisor", args.supervisor, "--tmux", args.tmux]
    return [args.ssh, "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
            args.ssh_target, shlex.join(command)]


class Calls:
    def __init__(self, args, origin, clock=time.monotonic):
        self.args, self.origin, self.clock = args, origin, clock

    def run(self, argv):
        try:
            return subprocess.run(argv, check=True, capture_output=True,
                                  timeout=remaining(self.origin + 540, self.clock)).stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            (Path(self.args.out) / "local-process.log").write_bytes((exc.stdout or b"") + (exc.stderr or b""))
            raise

    def admission(self):
        return self.run([sys.executable, str(HERE.parents[3] / "scripts/hmasd_resource_preflight.py"),
                         "admit-memory", "--out", str(Path(self.args.out) / "admission.json")])

    def anchor(self):
        return json.loads(self.run(ssh_command(self.args, "anchor")))

    def download(self, body, target):
        _, url, size = body
        output = self.run([self.args.powershell, "-NoLogo", "-NoProfile", "-NonInteractive",
                           "-ExecutionPolicy", "Bypass", "-File", str(HERE / "download.ps1"),
                           "-Url", url, "-Target", str(target), "-ExpectedBytes", str(size)])
        (Path(self.args.out) / (target.name + ".log")).write_bytes(output)

    def transfer(self, files, anchor, deadline):
        argv = ssh_command(self.args, "receive", anchor, deadline)
        with (Path(self.args.out) / "transfer.log").open("wb") as log:
            child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
            try:
                for path in files:
                    with path.open("rb") as stream:
                        while True:
                            remaining(self.origin + 540, self.clock)
                            block = stream.read(1024 * 1024)
                            if not block:
                                break
                            child.stdin.write(block)
                child.stdin.close()
                code = child.wait(timeout=remaining(self.origin + 540, self.clock))
                if code:
                    raise subprocess.CalledProcessError(code, argv)
            finally:
                if child.poll() is None:
                    child.kill()
                child.wait()

    def launch(self, anchor, deadline):
        output = self.run(ssh_command(self.args, "launch", anchor, deadline))
        (Path(self.args.out) / "dispatch.log").write_bytes(output)

    def collect(self, anchor, deadline):
        return json.loads(self.run(ssh_command(self.args, "collect", anchor, deadline)))


def chain(args, origin, calls=None, clock=time.monotonic, bodies=BODIES):
    calls = calls or Calls(args, origin, clock)
    out = Path(args.out)
    out.mkdir(parents=True)
    result = {"ready": False, "phase": "local_admission", "handle": args.handle,
              "command_source_sha": args.source, "seed": args.seed,
              "preflight_source_sha": "ec8866b3968fcb1566976ce405d7c552d4d9a5de",
              "remote_acceptance": "not_attempted", "metadata_collected": False}

    def phase(name):
        result["phase"] = name
        (out / "worker_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        remaining(origin + 540, clock)

    try:
        phase("local_admission")
        calls.admission()
        phase("clock_mapping")
        anchor = calls.anchor()
        deadline = map_deadline(anchor, remaining(origin + 540, clock))
        result["remote_clock"] = anchor
        result["remote_deadline_boottime_seconds"] = deadline
        files = []
        for body in bodies:
            phase("download:" + body[0])
            target = out / body[0]
            calls.download(body, target)
            if target.stat().st_size != body[2]:
                raise RuntimeError("Incomplete body: " + body[0])
            files.append(target)
        phase("transfer")
        calls.transfer(files, anchor, deadline)
        result["remote_acceptance"] = "uncertain"
        phase("remote_launch")
        calls.launch(anchor, deadline)
        result["remote_acceptance"] = "accepted"
        phase("collection")
        payload = calls.collect(anchor, deadline)
        result["remote_terminal"] = payload["terminal"]
        summary = payload["summary"]
        if summary is not None:
            path = out / "summary.json"
            path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            summary = json.loads(path.read_text(encoding="utf-8"))
            result["metadata_collected"] = True
        if payload["terminal"]["exit_code"] != 0 or summary is None or summary.get("metadata_matches") is not True:
            raise RuntimeError("Remote primary metadata is incomplete or unsuccessful")
        phase("complete")
        result["ready"] = True
    except Exception as exc:
        result["error"] = str(exc)
    result["whole_wall_seconds"] = clock() - origin
    if result["whole_wall_seconds"] > 600:
        result["ready"] = False
        result["error"] = "Complete wall bound exceeded"
    (out / "worker_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
