"""Run one paired negative: perturb a guard, prove it goes red, restore.

A guard test that has never been watched failing is indistinguishable from a
comment. This repository requires every new assertion to be seen red under a
change that breaks exactly the property it names -- and doing that by hand is
the most-repeated mechanical sequence in the workflow: read the line, write the
mutation, read it back off disk, run the suite, interpret the result, restore.

It has failed by hand twice, both times producing a false result:

  * a heredoc invoked bare `python`, which on this machine is a WindowsApps stub.
    The mutation never reached disk and the suite reported 183 passed -- read as
    "the guard is fine" when nothing had been perturbed at all.
  * a multi-line replacement rewrote only the first line, so the suite died
    during COLLECTION. An error is not a red test, and it was recorded as one.

Both are eliminated here by construction: the mutated region is read back off
disk and printed before pytest starts, and a run that errors during collection
is reported as INCONCLUSIVE, never as a passing paired negative.

Usage, either address the region by line or by exact text:

    paired_negative.py --file scripts/x.py --line 310 \\
        --new "    if False:  # MUTATION" --test tests/x_test.py -k sentinel

    paired_negative.py --file scripts/x.py \\
        --old "if not complete:" --new "if False:" --test tests/x_test.py

`--old` is the safer form for anything spanning lines: the replacement must
match exactly once, or nothing is written.

Exit 0 means the guard reddened -- the paired negative PASSED. Exit 1 means it
stayed green, which is a defect in the guard, not in this script. Exit 2 means
the run was inconclusive and proved nothing either way.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

INTERPRETER = r"C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe"


def _apply(path: Path, old: str | None, new: str, line: int | None) -> tuple[str, str]:
    """Returns (original_text, mutated_region_description)."""
    original = path.read_text(encoding="utf-8")
    if old is not None:
        count = original.count(old)
        if count != 1:
            raise SystemExit(
                f"--old matched {count} times in {path}; it must match exactly once. "
                f"Nothing was written.")
        mutated = original.replace(old, new)
        return original, f"replaced {len(old.splitlines())} line(s) matching --old"
    if line is None:
        raise SystemExit("give either --line or --old")
    lines = original.splitlines(keepends=True)
    if not 1 <= line <= len(lines):
        raise SystemExit(f"--line {line} is outside {path} (1..{len(lines)})")
    ending = "\n" if lines[line - 1].endswith("\n") else ""
    lines[line - 1] = new + ending
    mutated = "".join(lines)
    path.write_text(mutated, encoding="utf-8", newline="")
    return original, f"rewrote line {line}"


def _read_back(path: Path, line: int | None, new: str) -> str:
    """Prove the mutation reached disk. This is the step whose absence produced
    a false green: the suite ran against unmutated code and passed."""
    text = path.read_text(encoding="utf-8")
    if new.strip() and new.strip() not in text:
        raise SystemExit(
            f"MUTATION DID NOT REACH DISK: {path} does not contain the replacement. "
            f"Any suite result now would be measuring unmutated code.")
    if line is not None:
        return text.splitlines()[line - 1]
    first = new.splitlines()[0] if new.splitlines() else new
    for i, existing in enumerate(text.splitlines(), start=1):
        if first in existing:
            return f"{i}: {existing}"
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one paired negative and restore.")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--line", type=int)
    parser.add_argument("--old")
    parser.add_argument("--new", required=True)
    parser.add_argument("--test", action="append", required=True)
    parser.add_argument("-k", dest="keyword")
    parser.add_argument("--basetemp", default=None,
                        help="pytest tmp root. The default is not writable in this sandbox.")
    args = parser.parse_args(argv)

    path = args.file.resolve()
    if not path.is_file():
        raise SystemExit(f"no such file: {path}")

    backup = Path(tempfile.mkdtemp(prefix="paired_negative_")) / path.name
    shutil.copy2(path, backup)

    try:
        if args.old is not None:
            original = path.read_text(encoding="utf-8")
            count = original.count(args.old)
            if count != 1:
                raise SystemExit(
                    f"--old matched {count} times in {path}; it must match exactly once "
                    f"(this is the check that catches a multi-line replacement rewriting "
                    f"only its first line). Nothing was written.")
            path.write_text(original.replace(args.old, args.new), encoding="utf-8", newline="")
            how = f"replaced an exact {len(args.old.splitlines())}-line region"
        else:
            _apply(path, None, args.new, args.line)
            how = f"rewrote line {args.line}"

        shown = _read_back(path, args.line, args.new)
        print(f"MUTATION APPLIED  {path.name}: {how}")
        print(f"  read back off disk -> {shown}")
        print()

        cmd = [INTERPRETER, "-m", "pytest", *args.test, "-q"]
        if args.keyword:
            cmd += ["-k", args.keyword]
        if args.basetemp:
            cmd += ["--basetemp", args.basetemp]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        out = proc.stdout + proc.stderr

        failed = [l for l in out.splitlines() if l.startswith("FAILED")]
        errored = [l for l in out.splitlines() if l.startswith("ERROR")]
        summary = next((l for l in reversed(out.splitlines())
                        if re.search(r"\d+ (passed|failed|error)", l)), "(no summary line)")

        print(f"SUITE  {summary}")
        if errored:
            print("\nINCONCLUSIVE -- the suite ERRORED rather than failing. An error is not")
            print("a red test: collection never completed, so no guard was exercised.")
            for line in errored[:5]:
                print(f"  {line}")
            return 2
        if not failed:
            print("\nPAIRED NEGATIVE FAILED -- the suite stayed GREEN under this mutation.")
            print("The guard cannot detect the property it names. That is a defect in the")
            print("guard; do not weaken the mutation to make this pass.")
            return 1
        print(f"\nPAIRED NEGATIVE PASSED -- {len(failed)} test(s) reddened:")
        for line in failed:
            print(f"  {line}")
        return 0
    finally:
        shutil.copy2(backup, path)
        restored = path.read_text(encoding="utf-8")
        if args.new.strip() and args.new.strip() in restored:
            print(f"\nWARNING: {path} still contains the mutation after restore. Check it.")
        else:
            print(f"\nrestored {path.name}; no residue")
        shutil.rmtree(backup.parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
