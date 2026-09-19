"""Pro transport through Jev Ultrafast: one committed question, at most one Send.

Run with the Jev checkout's own interpreter (it carries browser-harness), never an HMASD venv:

    <jev_root>/.venv/bin/python tools/pro_transport/jev_send.py <command> ...

Jev chooses the operation and the target from the observed element table; this driver supplies
the exact committed text and runs the whole goal itself (effort, typing, one Send). This driver
supplies the committed text verbatim, persists ``send_attempted`` before the send click, refuses
that click if effort or text is wrong, and afterwards only observes. Settings come from ``[jev]`` in
``.codex/hmasd-transport.toml``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import tomllib
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SETTINGS = REPO / ".codex" / "hmasd-transport.toml"

# Read-only page facts. Selectors are reads only; no click or text ever comes from them.
PAGE_FACTS = """(() => {
  const text = e => (e?.innerText || '').trim();
  const composer = document.querySelector('#prompt-textarea');
  const users = [...document.querySelectorAll('[data-message-author-role="user"]')].map(text);
  const assistants = [...document.querySelectorAll('[data-message-author-role="assistant"]')].map(text);
  return {
    url: location.href,
    composer: composer ? text(composer) : null,
    send_button: !!document.querySelector('[data-testid="send-button"]'),
    stop_button: !!document.querySelector('[data-testid="stop-button"]'),
    login: !!document.querySelector('[data-testid="login-button"]'),
    challenge: /just a moment|verify you are human/i.test(document.title + ' ' + text(document.body).slice(0, 400)),
    users, assistants,
  };
})()"""

NODE_FACTS = """(node => {
  const e = window.__jevFast?.nodes.get(node);
  return e ? {testid: e.getAttribute('data-testid'), id: e.id, inside_composer_form:
    !!e.closest('form')?.querySelector('#prompt-textarea'), role: e.getAttribute('role'),
    haspopup: e.getAttribute('aria-haspopup'),
    text: (e.innerText || '').trim()} : null;
})"""


# A new conversation first shows a provisional /c/WEB:<id> address that cannot be reopened.
SETTLED_URL = re.compile(r"/c/[0-9a-f]{8}-[0-9a-f-]{27}")


class PreSendFailure(RuntimeError):
    """Nothing was submitted; the named fact may be repaired and the same key reused."""


def settings():
    table = tomllib.loads(SETTINGS.read_text(encoding="utf-8"))["jev"]
    return {key: os.path.expanduser(value) if isinstance(value, str) else value
            for key, value in table.items()}


def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


def load_jev(cfg):
    """Jev's credentials stay in its own ignored .env; only names are read here."""
    root = Path(cfg["root"])
    for line in (root / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"'))
    # Jev prefers the Vercel gateway whenever its key is present; the gateway rate-limits (HTTP 429).
    # With a native TypeSafe key available, the gateway key is left out of this process.
    if not os.environ.get("TYPESAFE_API_KEY", "vck_").startswith("vck_"):
        os.environ.pop("AI_GATEWAY_API_KEY", None)
    os.environ["BU_CDP_URL"] = cfg["cdp_url"]
    sys.path.insert(0, str(root))


def cdp_version(cfg):
    try:
        with urllib.request.urlopen(cfg["cdp_url"] + "/json/version", timeout=3) as response:
            return json.load(response)
    except OSError:
        return None


def chrome_mode(version):
    return "headless" if "Headless" in version.get("User-Agent", "") + version.get("Browser", "") else "headed"


def chrome_start(cfg, mode):
    """One Chrome on the logged-in profile. A running one in the other mode is reported, not killed."""
    version = cdp_version(cfg)
    if version:
        running = "headless" if Path(cfg["state_dir"], "chrome-headless").exists() else chrome_mode(version)
        if running != mode:
            raise PreSendFailure(f"Chrome already runs {running}; stop it before asking for {mode}")
        return {"chrome": "reused", "mode": mode}
    port = cfg["cdp_url"].rsplit(":", 1)[1]
    argv = [cfg["chrome"], f"--remote-debugging-port={port}", f"--user-data-dir={cfg['profile']}",
            "--no-first-run", "--no-default-browser-check", "--window-size=1280,900"]
    marker = Path(cfg["state_dir"], "chrome-headless")
    marker.parent.mkdir(parents=True, exist_ok=True)
    if mode == "headless":
        # The stock headless user agent names itself; the provider must see the same browser.
        argv += ["--headless=new", f"--user-agent={cfg['user_agent']}"]
        marker.write_text("1", encoding="utf-8")
    else:
        marker.unlink(missing_ok=True)
    log = open(Path(cfg["state_dir"], "chrome.log"), "ab")
    subprocess.Popen(argv + ["about:blank"], stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                     start_new_session=True)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if cdp_version(cfg):
            return {"chrome": "started", "mode": mode}
        time.sleep(0.5)
    raise PreSendFailure("Chrome did not open its debugging port")


def chrome_stop(cfg):
    if not cdp_version(cfg):
        return {"chrome": "not running"}
    load_jev(cfg)
    from browser_harness.admin import ensure_daemon
    from browser_harness.helpers import cdp
    ensure_daemon()
    try:
        cdp("Browser.close")
    except Exception:  # the socket closes with the browser
        pass
    Path(cfg["state_dir"], "chrome-headless").unlink(missing_ok=True)
    return {"chrome": "stopped"}


class Operation:
    """The persisted boundary: send_attempted is written before the external click."""

    def __init__(self, cfg, key):
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", key):
            raise PreSendFailure("question key has unsupported characters")
        self.path = Path(cfg["state_dir"], "operations", key.replace(":", "_") + ".json")
        self.data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def save(self, **facts):
        self.data.update(facts, updated=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)


def facts(browser):
    return browser.evaluate(PAGE_FACTS)


def wait_for(browser, test, seconds, what):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        current = facts(browser)
        if current and test(current):
            return current
        time.sleep(0.5)
    raise PreSendFailure(f"timed out waiting for {what}")


SLIDER = "document.querySelector('[data-radix-popper-content-wrapper] [role=slider]')"


def ensure_effort(browser, effort):
    """The effort control is a slider, a widget Jev's action space does not cover; arrow keys set it.

    The highest position is the Pro effort. The observed pill label, not the key count, is the fact.
    """
    page = browser.observe(screenshot=False)
    if any(a["label"] == effort for a in page["actions"]):
        return page
    for action in page["actions"]:
        if action["kind"] != "click" or "expanded" not in action:
            continue
        node = browser.evaluate(NODE_FACTS + f"({json.dumps(action['node'])})")
        if node and node["inside_composer_form"] and node["haspopup"] == "menu" and node["text"]:
            browser.act(action, page)
            break
    else:
        raise PreSendFailure("no reasoning-effort control in the composer")
    time.sleep(1.2)
    if not browser.evaluate(f"(() => {{ const s={SLIDER}; s?.focus(); return !!s; }})()"):
        raise PreSendFailure("the effort menu has no slider")
    steps = int(browser.evaluate(f"{SLIDER}.getAttribute('aria-valuemax')")) - \
        int(browser.evaluate(f"{SLIDER}.getAttribute('aria-valuenow')"))
    for key, code, virtual in [("ArrowRight", "ArrowRight", 39)] * steps + [("Escape", "Escape", 27)]:
        for kind in ("keyDown", "keyUp"):
            browser.call("Input.dispatchKeyEvent", type=kind, key=key, code=code, windowsVirtualKeyCode=virtual)
        time.sleep(0.4)
    time.sleep(0.8)
    page = browser.observe(screenshot=False)
    if not any(a["label"] == effort for a in page["actions"]):
        raise PreSendFailure(f"effort control does not show {effort!r} after the slider was set")
    return page


GOAL = """You are on ChatGPT. Do these in order, each once.
1. The reasoning-effort button beside the message box already shows '{effort}'. Leave it alone.
2. Type the prepared message into the message box.{draft}
3. Click the send button exactly once.
After the message is sent do nothing else: never click Stop, Regenerate, Edit, Retry, or send again.
DONE as soon as the sent message is visible in the conversation."""


def command_send(args, cfg):
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if not prompt:
        raise PreSendFailure("prompt file is empty")
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    operation = Operation(cfg, args.key)
    if operation.data.get("send_attempted"):
        return {**operation.data, "note": "send already attempted for this key; observe with `wait`, never resend"}
    if operation.data and operation.data.get("prompt_sha256") != digest:
        raise PreSendFailure("this key is bound to a different prompt")
    url = cfg["provider_root"] if args.conversation == "new" else args.conversation
    operation.save(key=args.key, prompt_sha256=digest, conversation=args.conversation,
                   squashed_sha256=hashlib.sha256(squash(prompt).encode()).hexdigest(),
                   mode=args.mode, effort=args.effort, send_attempted=False)

    chrome_start(cfg, args.mode)
    load_jev(cfg)
    import jev_ultrafast.agent as jev_agent
    from jev_ultrafast.browser import StalePage

    # The text is the committed prompt, verbatim; no model writes or paraphrases it.
    jev_agent.field_text = lambda context: (prompt, {"model": "committed-prompt", "latency_ms": 0, "usage": {}})
    agent = jev_agent.Agent(url, GOAL.format(effort=args.effort, draft=""))
    browser, state = agent.browser, agent.state
    sent = lambda f: any(squash(u) == squash(prompt) for u in f["users"])  # noqa: E731
    try:
        page = wait_for(browser, lambda f: f["composer"] is not None or f["login"] or f["challenge"],
                        40, "the composer")
        if page["login"] or page["challenge"] or page["composer"] is None:
            raise PreSendFailure("provider needs a human: " + ("login" if page["login"] else "challenge"))
        if page["stop_button"]:
            raise PreSendFailure("a generation is active in this conversation")
        if sent(page):
            raise PreSendFailure("the exact prompt is already submitted here; observe with `wait`")
        if page["composer"]:
            # The provider restores local drafts. Jev's fill replaces the whole box (select-all, insert),
            # and the send click is refused unless the box equals the committed prompt.
            operation.save(draft_replaced_sha256=hashlib.sha256(page["composer"].encode()).hexdigest())
            state["goal"] = GOAL.format(effort=args.effort, draft=" The box currently holds an outdated draft, "
                                        "not the prepared message: typing replaces it, so step 2 is still required.")
            state["plan"] = [state["goal"]]
        time.sleep(2)  # the composer's pills render after the box
        state["page"] = ensure_effort(browser, args.effort)

        # Jev runs the whole goal. The loop only keeps the books: it records the attempt before a
        # send click, refuses that one click if effort or text is wrong, and ends once the outcome shows.
        steps = []
        while state["status"] not in {"done", "blocked"} and len(steps) < 14:
            if operation.data["send_attempted"] or sent(facts(browser)):
                break
            try:
                agent.command("predict")
                choice = state["decision"]["choice"]
                action = next((a for a in state["page"]["actions"] if a["id"] == choice), None)
                steps.append(f"{state['decision']['operation']} {action['label'] if action else choice}")
                node = browser.evaluate(NODE_FACTS + f"({json.dumps(action['node'])})") \
                    if action and action["kind"] == "click" else None
                if node and node["testid"] == "send-button":
                    labels = {a["label"] for a in state["page"]["actions"]}
                    if args.effort not in labels:
                        raise PreSendFailure(f"send chosen while no control shows effort {args.effort!r}")
                    if squash(facts(browser)["composer"]) != squash(prompt):
                        operation.save(steps=steps)
                        raise PreSendFailure(f"composer text differs from the committed prompt: {steps}")
                    operation.save(send_attempted=True, send_effect="uncertain", steps=steps)
                agent.command("act", {"fingerprint": state["page"]["fingerprint"]})
            except StalePage:
                state.update(decision=None, status="ready")
                state["page"] = browser.observe(screenshot=False)
        operation.save(steps=steps)
        if not operation.data["send_attempted"]:
            raise PreSendFailure(f"Jev stopped before the send button ({state['status']}): {steps}")
        try:
            page = wait_for(browser, sent, 45, "the submitted message")
            operation.save(send_effect="sent", conversation_url=page["url"])
            page = wait_for(browser, lambda f: SETTLED_URL.search(f["url"]), 90, "the settled conversation URL")
            operation.save(conversation_url=page["url"])
        except PreSendFailure as error:
            operation.save(unresolved=str(error), conversation_url=facts(browser)["url"])
        return operation.data
    finally:
        agent.close()


def command_wait(args, cfg):
    """Read-only. COMPLETE needs equal assistant text across two samples three seconds apart and no Stop."""
    operation = Operation(cfg, args.key)
    if not operation.data.get("send_attempted"):
        raise PreSendFailure("no attempted send under this key")
    url = args.conversation_url or operation.data.get("conversation_url") or ""
    if not SETTLED_URL.search(url):
        raise PreSendFailure("no settled conversation URL; find the conversation and pass --conversation-url")
    chrome_start(cfg, args.mode or operation.data["mode"])
    load_jev(cfg)
    from jev_ultrafast.browser import Browser
    browser = Browser(url)
    try:
        prompt_seen = wait_for(browser, lambda f: f["users"], 40, "the conversation")
        wanted = operation.data.get("squashed_sha256")
        if wanted and not any(hashlib.sha256(squash(u).encode()).hexdigest() == wanted for u in prompt_seen["users"]):
            raise PreSendFailure("this conversation does not hold the operation's prompt")
        operation.save(conversation_url=url, send_effect="sent")
        deadline = time.monotonic() + args.timeout
        previous, state = None, "IN_PROGRESS"
        while time.monotonic() < deadline:
            page = facts(browser)
            answer = page["assistants"][-1] if len(page["assistants"]) >= len(page["users"]) else ""
            if answer and not page["stop_button"] and answer == previous:
                state = "COMPLETE"
                break
            previous = answer
            time.sleep(3)
        result = {"state": state, "conversation_url": url, "users": len(prompt_seen["users"])}
        if state == "COMPLETE":
            out = Path(args.answer_file)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(answer + "\n", encoding="utf-8")
            result.update(answer_file=str(out), answer_sha256=hashlib.sha256(answer.encode()).hexdigest(),
                          answer_chars=len(answer))
            operation.save(completion="COMPLETE", answer_sha256=result["answer_sha256"])
        return result
    finally:
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    chrome = sub.add_parser("chrome")
    chrome.add_argument("action", choices=("start", "stop", "status"))
    chrome.add_argument("--mode", choices=("headless", "headed"), default="headless")
    send = sub.add_parser("send")
    send.add_argument("--key", required=True)
    send.add_argument("--prompt-file", required=True)
    send.add_argument("--conversation", required=True, help="'new' or the conversation URL of this account")
    send.add_argument("--effort", default=None)
    send.add_argument("--mode", choices=("headless", "headed"), default="headless")
    wait = sub.add_parser("wait")
    wait.add_argument("--key", required=True)
    wait.add_argument("--answer-file", required=True)
    wait.add_argument("--timeout", type=float, default=60)
    wait.add_argument("--conversation-url", default=None, help="reconcile a URL the send could not observe")
    wait.add_argument("--mode", choices=("headless", "headed"), default=None)
    args = parser.parse_args()
    cfg = settings()
    try:
        if args.command == "chrome":
            version = cdp_version(cfg)
            result = (chrome_start(cfg, args.mode) if args.action == "start" else
                      chrome_stop(cfg) if args.action == "stop" else
                      {"chrome": "running" if version else "not running",
                       "mode": chrome_mode(version) if version else None})
        elif args.command == "send":
            args.effort = args.effort or cfg["effort_label"]
            result = command_send(args, cfg)
        else:
            result = command_wait(args, cfg)
    except PreSendFailure as error:
        print(json.dumps({"error": str(error), "pre_send": args.command == "send"}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
