#!/usr/bin/env python3
"""Deterministic wait helper for Pi Agent in HMASD.

Replaces runtime-specific Codex UUID queues with transparent local OS/file checks.
Enables waiting for background experiment PIDs or Pro answer deliveries without
wasting LLM context turns or API tokens on polling.

Usage:
    # 1. Wait for a background PID to complete:
    python tools/hmasd_pi_wait.py pid <PID> [--timeout 3600]

    # 2. Wait for a markdown section (e.g., ### Answer) to be populated:
    python tools/hmasd_pi_wait.py section --file docs/research/candidates/<dir>/NOTES.md --heading "### Answer" [--timeout 2700]

    # 3. Wait for an artifact/manifest file to be generated:
    python tools/hmasd_pi_wait.py file --path runs/<dir>/<tag>/summary.json [--timeout 3600]
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path


def wait_pid(pid: int, timeout: int, interval: float = 3.0) -> int:
    start_time = time.monotonic()
    print(f"[hmasd_pi_wait] Waiting for PID {pid} to terminate (timeout: {timeout}s)...")
    while time.monotonic() - start_time < timeout:
        try:
            # 0 signal sends no signal but performs error checking on pid existence
            os.kill(pid, 0)
        except ProcessLookupError:
            elapsed = time.monotonic() - start_time
            print(f"[hmasd_pi_wait] PID {pid} finished after {elapsed:.1f}s.")
            return 0
        except PermissionError:
            # Still running under different permissions
            pass
        time.sleep(interval)

    print(f"[hmasd_pi_wait] ERROR: Timeout of {timeout}s reached waiting for PID {pid}.", file=sys.stderr)
    return 1


def wait_section(filepath: str, heading: str, timeout: int, interval: float = 5.0) -> int:
    path = Path(filepath)
    start_time = time.monotonic()
    clean_heading = heading.strip()
    print(f"[hmasd_pi_wait] Waiting for section '{clean_heading}' in {path} to have non-empty content (timeout: {timeout}s)...")

    while time.monotonic() - start_time < timeout:
        if path.is_file():
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            heading_index = next(
                (i for i, line in enumerate(lines) if line.strip() == clean_heading),
                None,
            )
            if heading_index is not None:
                heading_level = len(clean_heading) - len(clean_heading.lstrip("#"))
                body_lines = []
                for line in lines[heading_index + 1:]:
                    next_heading = re.match(r"^ {0,3}(#{1,6})\s+", line)
                    if next_heading and len(next_heading.group(1)) <= heading_level:
                        break
                    body_lines.append(line)
                section_body = "\n".join(body_lines).strip()
                if len(section_body) > 0:
                    elapsed = time.monotonic() - start_time
                    print(f"[hmasd_pi_wait] Section '{clean_heading}' populated ({len(section_body)} chars) after {elapsed:.1f}s.")
                    return 0
        time.sleep(interval)

    print(f"[hmasd_pi_wait] ERROR: Timeout of {timeout}s reached waiting for section in {path}.", file=sys.stderr)
    return 1


def wait_file(filepath: str, timeout: int, interval: float = 3.0, stable_window: float = 2.0) -> int:
    path = Path(filepath)
    start_time = time.monotonic()
    print(f"[hmasd_pi_wait] Waiting for file {path} to exist and stabilize (timeout: {timeout}s)...")

    while time.monotonic() - start_time < timeout:
        if path.is_file() and path.stat().st_size > 0:
            initial_size = path.stat().st_size
            time.sleep(stable_window)
            if path.stat().st_size == initial_size:
                elapsed = time.monotonic() - start_time
                print(f"[hmasd_pi_wait] File {path} ready ({initial_size} bytes) after {elapsed:.1f}s.")
                return 0
        time.sleep(interval)

    print(f"[hmasd_pi_wait] ERROR: Timeout of {timeout}s reached waiting for file {path}.", file=sys.stderr)
    return 1


def main():
    parser = argparse.ArgumentParser(description="HMASD deterministic wait tool for Pi Agent")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_pid = subparsers.add_parser("pid", help="Wait for a process ID")
    p_pid.add_argument("pid", type=int, help="Target process PID")
    p_pid.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds (default: 3600)")

    p_sec = subparsers.add_parser("section", help="Wait for a markdown section to be populated")
    p_sec.add_argument("--file", required=True, help="Path to markdown file")
    p_sec.add_argument("--heading", required=True, help="Heading text (e.g. '### Answer')")
    p_sec.add_argument("--timeout", type=int, default=2700, help="Timeout in seconds (default: 2700)")

    p_file = subparsers.add_parser("file", help="Wait for an output file to exist")
    p_file.add_argument("--path", required=True, help="Path to target file")
    p_file.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds (default: 3600)")

    args = parser.parse_args()

    if args.subcommand == "pid":
        sys.exit(wait_pid(args.pid, args.timeout))
    elif args.subcommand == "section":
        sys.exit(wait_section(args.file, args.heading, args.timeout))
    elif args.subcommand == "file":
        sys.exit(wait_file(args.path, args.timeout))


if __name__ == "__main__":
    main()
