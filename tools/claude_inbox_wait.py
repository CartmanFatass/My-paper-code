#!/usr/bin/env python3
"""Block until a Root→Claude inbox message lands in this checkout, then exit once.

Trigger-based, no polling: an inotify watch on docs/Claude_docs/inbox catches a file written
in this working tree, and a watch on .git/logs/HEAD catches a commit made in this checkout
(Root commits inbox files here) whose diff touches the inbox. Optional explicit trigger: any
file written under temp/claude_inbox_trigger/ (a peer may touch one after a commit made
elsewhere). Prints one line per changed inbox path and exits 0; exits 3 on --timeout.
Run from the checkout root, e.g. as a background command that notifies the session on exit.
"""
import argparse, ctypes, os, select, struct, subprocess, sys, time

IN_MODIFY, IN_CLOSE_WRITE, IN_MOVED_TO, IN_CREATE = 0x2, 0x8, 0x80, 0x100
INBOX = "docs/Claude_docs/inbox"
TRIGGER = "temp/claude_inbox_trigger"
HEADLOG = ".git/logs/HEAD"


def inbox_paths_in_last_commit():
    try:
        out = subprocess.run(["git", "diff", "--name-only", "HEAD@{1}", "HEAD", "--", INBOX],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return []
    return [p for p in out.split("\n") if p.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=0, help="seconds; 0 = block indefinitely")
    args = ap.parse_args()
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    fd = libc.inotify_init1(0)
    if fd < 0:
        sys.exit("inotify_init1 failed: errno %d" % ctypes.get_errno())
    os.makedirs(TRIGGER, exist_ok=True)
    wds = {}
    for path, mask in ((INBOX, IN_CLOSE_WRITE | IN_MOVED_TO | IN_CREATE),
                       (TRIGGER, IN_CLOSE_WRITE | IN_MOVED_TO | IN_CREATE),
                       (HEADLOG, IN_MODIFY)):
        wd = libc.inotify_add_watch(fd, path.encode(), mask)
        if wd < 0:
            sys.exit("inotify_add_watch(%s) failed: errno %d" % (path, ctypes.get_errno()))
        wds[wd] = path
    deadline = time.time() + args.timeout if args.timeout else None
    print("armed: %s | %s | %s" % (INBOX, TRIGGER, HEADLOG), flush=True)
    while True:
        wait = None if deadline is None else max(0.0, deadline - time.time())
        r, _, _ = select.select([fd], [], [], wait)
        if not r:
            print("timeout: no inbox change", flush=True)
            sys.exit(3)
        buf = os.read(fd, 65536)
        i, hits = 0, []
        while i + 16 <= len(buf):
            wd, mask, cookie, length = struct.unpack_from("iIII", buf, i)
            name = buf[i + 16:i + 16 + length].split(b"\0", 1)[0].decode(errors="replace")
            i += 16 + length
            src = wds.get(wd, "?")
            if src == HEADLOG:
                time.sleep(0.5)  # let the commit finish writing refs
                hits += ["INBOX_COMMIT %s" % p for p in inbox_paths_in_last_commit()]
            elif src == TRIGGER:
                hits.append("INBOX_TRIGGER %s" % name)
            else:
                hits.append("INBOX_FILE %s/%s" % (INBOX, name))
        if hits:
            for h in sorted(set(hits)):
                print(h, flush=True)
            sys.exit(0)


if __name__ == "__main__":
    main()
