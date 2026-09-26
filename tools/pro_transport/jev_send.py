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
import signal
import subprocess
import sys
import time
import tomllib
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SETTINGS = REPO / ".codex" / "hmasd-transport.toml"

# A hydrated composer has one editable field inside its form. The pending-home-input textarea
# is only a loading placeholder. Require one valid candidate so a changed/ambiguous UI fails closed.
COMPOSER_LOOKUP = """() => {
  const candidates = [...document.querySelectorAll('#prompt-textarea, [data-composer-markdown]')];
  if (candidates.length !== 1) return null;
  const e = candidates[0];
  if (!e.closest('form')) return null;
  const legacy = e.id === 'prompt-textarea';
  const role = e.getAttribute('role');
  if (e.tagName === 'TEXTAREA') return legacy && (!role || role === 'textbox') ? e : null;
  if (e.getAttribute('contenteditable') !== 'true') return null;
  return (e.hasAttribute('data-composer-markdown') ? role === 'textbox'
    : legacy && (!role || role === 'textbox')) ? e : null;
}"""

SEND_LOOKUP = """() => {
  const form = (__COMPOSER_LOOKUP__)()?.closest('form');
  if (!form) return null;
  const candidates = [...form.querySelectorAll('button[data-testid="send-button"], button[type="submit"]')]
    .filter(e => !e.disabled && (e.getAttribute('data-testid') === 'send-button' ||
      (e.type === 'submit' && /^(发送|Send)$/.test(e.getAttribute('aria-label') || ''))));
  return candidates.length === 1 ? candidates[0] : null;
}""".replace("__COMPOSER_LOOKUP__", COMPOSER_LOOKUP)

UPLOAD_LOOKUP = """() => {
  const form = (__COMPOSER_LOOKUP__)()?.closest('form');
  if (!form) return null;
  const candidates = [...form.querySelectorAll('input[type="file"]')].filter(e =>
    !(e.getAttribute('accept') || '').trim() &&
    (e.id === 'upload-files' || /^(附加文件|Attach files|Attach file)$/.test(e.getAttribute('aria-label') || '')));
  if (candidates.length !== 1) return null;
  const input = candidates[0];
  if (!/^[A-Za-z0-9_-]+$/.test(input.id)) return null;
  return document.querySelectorAll('input[id="' + input.id + '"]').length === 1 ? input.id : null;
}""".replace("__COMPOSER_LOOKUP__", COMPOSER_LOOKUP)


# Read-only page facts. Selectors are reads only; no click or text ever comes from them.
PAGE_FACTS = """(() => {
  const text = e => (e?.innerText || '').trim();
  const composer = (__COMPOSER_LOOKUP__)();
  const send = (__SEND_LOOKUP__)();
  const legacyMessages = [...document.querySelectorAll('[data-message-author-role]')];
  const modernUnits = [...document.querySelectorAll('[data-chatgpt-search-unit-key]')]
    .filter(unit => /:(user|assistant)$/.test(unit.getAttribute('data-chatgpt-search-unit-key') || ''));
  const legacyTurns = legacyMessages.map(message => {
    const container = message.closest('article,[data-testid^="conversation-turn"]') || message;
    const messageBody = message.getAttribute('data-message-author-role') === 'user'
      ? message.querySelector('.whitespace-pre-wrap') : null;
    return {role: message.getAttribute('data-message-author-role'), text: text(message),
      message_body: messageBody ? text(messageBody) : null, turn_text: text(container),
      // Tool work can continue after an opening assistant message with no Stop
      // button. The completed response's feedback control belongs to this turn.
      final_controls: message.getAttribute('data-message-author-role') === 'assistant'
        && !!container.querySelector('[data-testid="feedback-turn-action-button"]')};
  });
  const modernTurns = modernUnits.map(unit => {
    const key = unit.getAttribute('data-chatgpt-search-unit-key') || '';
    const match = key.match(/^(.*):([0-9]+):(user|assistant)$/);
    const container = unit.closest('[data-content-search-turn-key]');
    if (!match || !container || container.getAttribute('data-content-search-turn-key') !== match[1])
      return null;
    if (match[3] === 'user') {
      const bubbles = [...unit.querySelectorAll('[data-user-message-bubble="true"]')];
      const bodies = bubbles.length === 1 ? [...bubbles[0].querySelectorAll('.whitespace-pre-wrap')] : [];
      if (bodies.length !== 1) return null;
      return {role: 'user', text: text(unit), message_body: text(bodies[0]),
        turn_text: text(unit), final_controls: false};
    }
    const bodies = [...unit.querySelectorAll('[data-markdown-text-style="assistant-message"]')];
    const siblings = modernUnits.filter(other =>
      other.closest('[data-content-search-turn-key]') === container &&
      /:assistant$/.test(other.getAttribute('data-chatgpt-search-unit-key') || ''));
    const footers = [...container.querySelectorAll('.turn-action-controls')].filter(footer =>
      footer.closest('[data-content-search-turn-key]') === container &&
      footer.querySelectorAll('button[aria-label="重新生成回复"], button[aria-label="Regenerate response"]').length === 1 &&
      footer.querySelectorAll('button[aria-label="回复不佳"], button[aria-label="Bad response"]').length === 1);
    const footer = footers.length === 1 ? footers[0] : null;
    const finalControls = !!footer && siblings[siblings.length - 1] === unit && bodies.length === 1;
    return {role: 'assistant', text: bodies.length === 1 ? text(bodies[0]) : '',
      message_body: null, turn_text: text(unit), final_controls: finalControls};
  });
  const turns = legacyMessages.length && modernUnits.length ? [] :
    legacyMessages.length ? legacyTurns : modernTurns.every(Boolean) ? modernTurns : [];
  const users = turns.filter(turn => turn.role === 'user').map(turn => turn.text);
  const assistants = turns.filter(turn => turn.role === 'assistant').map(turn => turn.text);
  const userTurns = legacyMessages.length ?
    [...document.querySelectorAll('article,[data-testid^="conversation-turn"]')]
      .filter(e => e.querySelector('[data-message-author-role="user"]')).map(text) :
    turns.filter(turn => turn.role === 'user').map(turn => turn.turn_text);
  const pageText = text(document.body).slice(0, 800);
  return {
    url: location.href,
    title: document.title,
    composer: composer ? (composer.tagName === 'TEXTAREA' ? composer.value.trim() : text(composer)) : null,
    send_button: !!send,
    form_text: text(composer?.closest('form')),
    user_turns: users.length ? userTurns : [],
    stop_button: !!document.querySelector('[data-testid="stop-button"]'),
    login: !!document.querySelector('[data-testid="login-button"]'),
    approval: [...document.querySelectorAll('main button')].map(text)
      .filter(t => /^(允许一次|始终允许|拒绝|Allow once|Always allow|Deny)$/.test(t)),
    // The words of the prompt those buttons belong to: the largest enclosing block that is still short.
    approval_text: (() => {
      let e = [...document.querySelectorAll('main button')].find(b => /^(始终允许|Always allow)$/.test(text(b)));
      let words = '';
      for (let i = 0; e && i < 7; i++, e = e.parentElement) if (text(e).length < 500) words = text(e);
      return words;
    })(),
    challenge: /just a moment|verify you are human/i.test(document.title + ' ' + text(document.body).slice(0, 400)),
    auth_required: !composer && /log in|sign in|sign up|登录|登入|注册/i.test(document.title + ' ' + pageText),
    page_error: location.protocol === 'chrome-error:' || /aw, snap|page unresponsive|页面崩溃/i.test(document.title),
    users, assistants, turns,
  };
})()""".replace("__COMPOSER_LOOKUP__", COMPOSER_LOOKUP).replace("__SEND_LOOKUP__", SEND_LOOKUP)

NODE_FACTS = """(node => {
  const e = window.__jevFast?.nodes.get(node);
  const composer = (__COMPOSER_LOOKUP__)();
  const send = (__SEND_LOOKUP__)();
  return e ? {testid: e.getAttribute('data-testid'), id: e.id, inside_composer_form:
    !!composer && e.closest('form') === composer.closest('form'), role: e.getAttribute('role'),
    haspopup: e.getAttribute('aria-haspopup'),
    model_trigger: e.getAttribute('data-codex-intelligence-trigger') === 'true' &&
      e.getAttribute('data-composer-navigation-target') === 'reasoning',
    is_composer: !!composer && (e === composer || composer.contains(e)),
    is_send: !!send && (e === send || send.contains(e)),
    text: (e.innerText || '').trim()} : null;
})""".replace("__COMPOSER_LOOKUP__", COMPOSER_LOOKUP).replace("__SEND_LOOKUP__", SEND_LOOKUP)

FOCUS_COMPOSER = """(() => {
  const composer = (__COMPOSER_LOOKUP__)();
  if (!composer) throw new Error('composer unavailable');
  composer.focus();
})()""".replace("__COMPOSER_LOOKUP__", COMPOSER_LOOKUP)

MODEL_PROOF = """(() => {
  const form = (__COMPOSER_LOOKUP__)()?.closest('form');
  if (!form) return null;
  const triggers = [...form.querySelectorAll('[aria-haspopup="menu"]')].filter(e =>
    e.id && /^(选择 ChatGPT 模型|Choose ChatGPT model)$/.test(e.getAttribute('aria-label') || '') &&
    e.getAttribute('data-codex-intelligence-trigger') === 'true' &&
    e.getAttribute('data-composer-navigation-target') === 'reasoning');
  if (triggers.length !== 1) return null;
  const menus = [...document.querySelectorAll('[role="menu"][aria-labelledby]')].filter(e =>
    e.getAttribute('aria-labelledby') === triggers[0].id);
  if (menus.length !== 1) return null;
  const menu = menus[0];
  const toggle = [...menu.querySelectorAll('[data-model-picker-view-toggle="true"][role="menuitem"]')];
  const maximum = [...menu.querySelectorAll('[data-maximum="true"]')];
  const sliders = [...menu.querySelectorAll('[data-reasoning-slider="true"] [role="slider"], [data-reasoning-slider="true"][role="slider"]')];
  const selected = [...menu.querySelectorAll('[role="menuitemradio"][aria-checked="true"][data-model-selected="true"]')];
  if ([toggle, maximum, sliders, selected].some(items => items.length !== 1)) return null;
  const text = e => (e.innerText || '').replace(/\\s+/g, ' ').trim();
  const nowAttribute = sliders[0].getAttribute('aria-valuenow');
  const maxAttribute = sliders[0].getAttribute('aria-valuemax');
  if (nowAttribute === null || maxAttribute === null) return null;
  const now = Number(nowAttribute);
  const max = Number(maxAttribute);
  if (!Number.isInteger(now) || !Number.isInteger(max) || max < 1 || now < 0 || now > max)
    return null;
  return {model: text(toggle[0]), effort: text(maximum[0]), selected: text(selected[0]),
    now, max, trigger_id: triggers[0].id};
})()""".replace("__COMPOSER_LOOKUP__", COMPOSER_LOOKUP)

MODEL_SLIDER_FOCUS = """(() => {
  const proof = __MODEL_PROOF__;
  if (!proof) return false;
  const menu = [...document.querySelectorAll('[role="menu"][aria-labelledby]')].find(e =>
    e.getAttribute('aria-labelledby') === proof.trigger_id);
  const slider = menu?.querySelector('[data-reasoning-slider="true"] [role="slider"], [data-reasoning-slider="true"][role="slider"]');
  slider?.focus();
  return !!slider;
})()""".replace("__MODEL_PROOF__", MODEL_PROOF)


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
    """Prove the configured model/effort from a closed legacy pill or the linked modern menu.

    Jev opens the menu. Arrow keys only move its slider, then the menu closes and a fresh
    observation is returned for Jev's next decision.
    """
    page = browser.observe(screenshot=False)
    for action in page["actions"]:
        if action["kind"] != "click" or action["label"] != effort:
            continue
        node = browser.evaluate(NODE_FACTS + f"({json.dumps(action['node'])})")
        if node and node["inside_composer_form"] and node["haspopup"] == "menu" and \
                squash(node["text"]) == effort:
            return page, "legacy"
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
    modern = browser.evaluate(MODEL_PROOF)
    if modern:
        if effort != "6 Pro" or modern["model"] != effort or modern["effort"] != "Pro" or \
                modern["selected"] not in {"最新", "Latest"}:
            raise PreSendFailure(f"linked model menu does not prove configured effort {effort!r}")
        steps = modern["max"] - modern["now"]
        if steps and not browser.evaluate(MODEL_SLIDER_FOCUS):
            raise PreSendFailure("linked model menu has no focusable slider")
        proof = "modern"
    else:
        if node["model_trigger"]:
            raise PreSendFailure("linked model menu is missing or ambiguous")
        if not browser.evaluate(f"(() => {{ const s={SLIDER}; s?.focus(); return !!s; }})()"):
            raise PreSendFailure("the effort menu has no slider")
        steps = int(browser.evaluate(f"{SLIDER}.getAttribute('aria-valuemax')")) - \
            int(browser.evaluate(f"{SLIDER}.getAttribute('aria-valuenow')"))
        proof = "legacy"
    for _ in range(steps):
        for kind in ("keyDown", "keyUp"):
            browser.call("Input.dispatchKeyEvent", type=kind, key="ArrowRight", code="ArrowRight",
                         windowsVirtualKeyCode=39)
        time.sleep(0.4)
    if modern:
        refreshed = browser.evaluate(MODEL_PROOF)
        if not refreshed or refreshed["model"] != effort or refreshed["effort"] != "Pro" or \
                refreshed["selected"] not in {"最新", "Latest"} or \
                refreshed["now"] != refreshed["max"]:
            raise PreSendFailure("linked model menu did not confirm Pro at its maximum effort")
    for kind in ("keyDown", "keyUp"):
        browser.call("Input.dispatchKeyEvent", type=kind, key="Escape", code="Escape",
                     windowsVirtualKeyCode=27)
    time.sleep(0.4)
    time.sleep(0.8)
    page = browser.observe(screenshot=False)
    if proof == "legacy" and not any(a["label"] == effort for a in page["actions"]):
        raise PreSendFailure(f"effort control does not show {effort!r} after the slider was set")
    return page, proof


def attach(browser, path):
    """Uploads are outside Jev's action space: the composer's own file input receives the file over CDP."""
    upload_id = browser.evaluate(f"({UPLOAD_LOOKUP})()")
    if not upload_id:
        raise PreSendFailure("the composer has no unique document upload input")
    root = browser.call("DOM.getDocument", depth=0)["root"]["nodeId"]
    node = browser.call("DOM.querySelector", nodeId=root, selector=f'input[id="{upload_id}"]')["nodeId"]
    if not node:
        raise PreSendFailure("the composer has no document upload input")
    browser.call("DOM.setFileInputFiles", nodeId=node, files=[str(path)])
    wait_for(browser, lambda f: path.name in (f["form_text"] or ""), 60, f"the attachment chip {path.name}")
    ready_to_send(browser, 120)


def ready_to_send(browser, seconds):
    """The send button is disabled while a file is processed, and a disabled control is not in Jev's
    element table. Asking Jev before it is back only burns decisions, so the driver waits for it:
    enabled on four samples in a row, because it is briefly enabled before the upload starts."""
    deadline, streak = time.monotonic() + seconds, 0
    while time.monotonic() < deadline:
        streak = streak + 1 if facts(browser)["send_button"] else 0
        if streak >= 4:
            return
        time.sleep(0.7)
    raise PreSendFailure("the send button did not become available")


FILL_GOAL = """You are on ChatGPT. The configured model and reasoning effort ('{effort}') were independently verified; leave those controls alone.
Type the prepared message into the message box only, replacing any old draft.
Do not click Send, do not submit, and do not add files. DONE when the prepared message fills the box."""

SEND_GOAL = """You are on ChatGPT. The configured model and reasoning effort ('{effort}') were independently verified; leave those controls alone.
The prepared message is already in the box and its exact text has been verified.{attachment}
Click the Send button exactly once. Do not type, change the model, attach files, or click any other control.
After Send do nothing else. DONE as soon as the sent message is visible in the conversation."""


def phase_goal(ready, effort, attachment=""):
    """Tell Jev only the next action allowed by the driver's verified composer state."""
    return (SEND_GOAL if ready else FILL_GOAL).format(effort=effort, attachment=attachment)


def command_send(args, cfg):
    prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if not prompt:
        raise PreSendFailure("prompt file is empty")
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    operation = Operation(cfg, args.key)
    if operation.data.get("send_attempted"):
        return {**operation.data, "note": "send already attempted for this key; observe with `wait`, never resend"}
    if operation.data.get("prompt_sha256") and operation.data["prompt_sha256"] != digest:
        raise PreSendFailure("this key is bound to a different prompt")
    url = cfg["provider_root"] if args.conversation == "new" else args.conversation
    operation.save(key=args.key, prompt_sha256=digest, conversation=args.conversation,
                   squashed_sha256=hashlib.sha256(squash(prompt).encode()).hexdigest(),
                   mode=args.mode, effort=args.effort, send_attempted=False)

    document = Path(args.attach).resolve(strict=True) if args.attach else None
    note = ""
    if document:
        operation.save(attachment=document.name,
                       attachment_sha256=hashlib.sha256(document.read_bytes()).hexdigest())

    chrome_start(cfg, args.mode)
    load_jev(cfg)
    import jev_ultrafast.agent as jev_agent
    from jev_ultrafast.browser import StalePage

    # The text is the committed prompt, verbatim; no model writes or paraphrases it.
    jev_agent.field_text = lambda context: (prompt, {"model": "committed-prompt", "latency_ms": 0, "usage": {}})
    agent = jev_agent.Agent(url, phase_goal(False, args.effort))
    browser, state = agent.browser, agent.state
    # With an attachment the user turn also carries the file chip; the committed text is contained in it.
    sent = lambda f: any(squash(prompt) in squash(u) for u in f["users"] + f["user_turns"])  # noqa: E731
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
            # A long restored draft makes the box taller than the viewport, and Jev rightly refuses a
            # target whose centre it cannot hit. Select-all and Backspace empty the box first.
            browser.evaluate(FOCUS_COMPOSER)
            for key, code, virtual, extra in (("a", "KeyA", 65, {"modifiers": 2, "commands": ["selectAll"]}),
                                              ("Backspace", "Backspace", 8, {})):
                browser.call("Input.dispatchKeyEvent", type="keyDown", key=key, code=code,
                             windowsVirtualKeyCode=virtual, **extra)
                browser.call("Input.dispatchKeyEvent", type="keyUp", key=key, code=code,
                             windowsVirtualKeyCode=virtual, **{k: v for k, v in extra.items() if k == "modifiers"})
            wait_for(browser, lambda f: not f["composer"], 10, "the emptied message box")
        time.sleep(2)  # the composer's pills render after the box
        if document and document.name in (facts(browser)["form_text"] or ""):
            raise PreSendFailure(f"an attachment named {document.name} is already in the composer")

        # Jev runs the whole goal. The loop only keeps the books: it records the attempt before a
        # send click, refuses that one click if effort or text is wrong, and ends once the outcome shows.
        steps, attached = [], False
        while state["status"] not in {"done", "blocked"} and len(steps) < 14:
            current = facts(browser)
            if operation.data["send_attempted"] or sent(current):
                break
            # Jev cannot compare the box with a text it never sees; the driver states that one fact.
            if squash(current["composer"]) == squash(prompt):
                if document and not attached:
                    # Uploaded only once the text is in place: a typing failure before this point
                    # leaves no copy of the document in the account's file store.
                    attach(browser, document)
                    attached = True
                    note = (f" The document {document.name} is already attached to the message; "
                            "do not add, open or remove files.")
                ready_to_send(browser, 60)
                ready = True
            else:
                ready = False
            # Any typing, upload or previous browser action invalidates the earlier proof. Verify
            # again, close the menu, and let Jev choose from the newly observed closed page.
            state["page"], effort_proof = ensure_effort(browser, args.effort)
            proof_fingerprint = state["page"]["fingerprint"]
            state["goal"] = phase_goal(ready, args.effort, note)
            state["plan"] = [state["goal"]]
            try:
                agent.command("predict")
                choice = state["decision"]["choice"]
                action = next((a for a in state["page"]["actions"] if a["id"] == choice), None)
                steps.append(f"{state['decision']['operation']} {action['label'] if action else choice}")
                if os.environ.get("HMASD_JEV_DEBUG"):
                    table = [a["label"][:24] for a in state["page"]["actions"] if a["kind"] == "click"][-8:]
                    print(json.dumps({"step": steps[-1], "last_clickables": table,
                                      "op_p": state["decision"].get("operation_probabilities")},
                                     ensure_ascii=False), file=sys.stderr, flush=True)
                node = browser.evaluate(NODE_FACTS + f"({json.dumps(action['node'])})") \
                    if action and action["kind"] == "click" else None
                if action and action["kind"] == "click" and node and node["is_send"]:
                    if effort_proof not in {"legacy", "modern"} or \
                            state["page"]["fingerprint"] != proof_fingerprint:
                        raise PreSendFailure("send chosen without fresh model and effort proof")
                    if document and document.name not in (facts(browser)["form_text"] or ""):
                        raise PreSendFailure(f"send chosen while {document.name} is not attached")
                    if squash(facts(browser)["composer"]) != squash(prompt):
                        operation.save(steps=steps)
                        raise PreSendFailure(f"composer text differs from the committed prompt: {steps}")
                    if args.dry_run:
                        # Everything up to the click was exercised and checked; the click is withheld.
                        state["decision"] = None
                        operation.save(steps=steps, dry_run="reached the send button with effort, text and "
                                       "attachment verified; not clicked")
                        return operation.data
                    operation.save(send_attempted=True, send_effect="uncertain", steps=steps)
                elif action and action["kind"] == "click":
                    if not node or not node["is_composer"]:
                        raise PreSendFailure(f"unrecognized click chosen before send: {steps}")
                elif action and action["kind"] in {"fill", "type"}:
                    target = browser.evaluate(NODE_FACTS + f"({json.dumps(action['node'])})")
                    if not target or not target["is_composer"]:
                        raise PreSendFailure(f"text action did not target the composer: {steps}")
                elif not action or action["kind"] not in {"fill", "type", "wait"}:
                    raise PreSendFailure(f"unrecognized action chosen before send: {steps}")
                agent.command("act", {"fingerprint": state["page"]["fingerprint"]})
            except StalePage as stale:
                steps.append(f"STALE {stale}")
                effort_proof = None
                state.update(decision=None, status="ready")
                state["page"] = browser.observe(screenshot=False)
        operation.save(steps=steps)
        if not operation.data["send_attempted"]:
            raise PreSendFailure(f"Jev stopped before the send button ({state['status']}): {steps}")
        try:
            page = wait_for(browser, sent, 45, "the submitted message")
            operation.save(send_effect="sent", conversation_url=page["url"])
            if document:
                operation.save(attachment_seen=any(document.name in turn for turn in page["user_turns"]))
            page = wait_for(browser, lambda f: SETTLED_URL.search(f["url"]), 90, "the settled conversation URL")
            operation.save(conversation_url=page["url"])
        except PreSendFailure as error:
            operation.save(unresolved=str(error), conversation_url=facts(browser)["url"])
        return operation.data
    finally:
        agent.close()


def command_reconcile(args, cfg):
    """Read-only evidence for an uncertain send. The provider clears the draft when it accepts a message,
    so the committed text still sitting as the new-chat draft, with no settled conversation recorded,
    shows the click did not submit. Only then is the key released, once."""
    operation = Operation(cfg, args.key)
    data = operation.data
    if not data.get("send_attempted") or data.get("send_effect") == "sent":
        raise PreSendFailure("nothing uncertain under this key")
    if data.get("released"):
        raise PreSendFailure("this key was already released once; a second uncertain send goes to the owner")
    if SETTLED_URL.search(data.get("conversation_url") or ""):
        raise PreSendFailure("a settled conversation was recorded; observe it with `wait`")
    chrome_start(cfg, data["mode"])
    load_jev(cfg)
    from jev_ultrafast.browser import Browser
    browser = Browser(cfg["provider_root"])
    try:
        page = wait_for(browser, lambda f: f["composer"] is not None, 40, "the composer")
        time.sleep(3)
        page = facts(browser)
        draft = hashlib.sha256(squash(page["composer"]).encode()).hexdigest()
        if draft != data["squashed_sha256"]:
            return {"released": False, "reason": "the new-chat draft is not the committed text; still uncertain"}
        operation.save(send_attempted=False, send_effect="not submitted", released=True,
                       released_evidence="committed text still present as the unsent new-chat draft",
                       released_prompt_sha256=data["prompt_sha256"], prompt_sha256=None)
        return {"released": True, "evidence": operation.data["released_evidence"]}
    finally:
        browser.close()


ALWAYS_ALLOW = ("始终允许", "Always allow")
WAIT_RPC_SECONDS = 20.0
WAIT_OPEN_SECONDS = 40.0
WAIT_RECOVERY_ATTEMPTS = 2
WAIT_SAMPLE_SECONDS = 3.0


class WaitCallTimeout(BaseException):
    """A wait-side watchdog escaped browser helpers that catch Exception/OSError."""


class WaitReadFailure(RuntimeError):
    """The read-only browser target, page or operation binding is unusable."""


def bounded_wait_call(call, seconds, label):
    """Bound one wait-side browser/harness call on POSIX without a worker thread.

    Browser Harness currently bounds each CDP IPC response at five seconds. This outer
    timer also covers constructor retry loops and protects against a wedged harness call.
    The wait recovery path is supported on the WSL/POSIX transport host; it refuses an
    unbounded fallback on platforms without ``setitimer``.
    """
    seconds = max(0.001, float(seconds))
    if not hasattr(signal, "setitimer"):
        raise WaitCallTimeout(f"{label} cannot be bounded on this platform")
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def expired(_signum, _frame):
        raise WaitCallTimeout(f"{label} timed out after {seconds:g}s")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    started = time.monotonic()
    try:
        return call()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            remaining = max(0.001, previous_timer[0] - (time.monotonic() - started))
            signal.setitimer(signal.ITIMER_REAL, remaining, previous_timer[1])


def make_wait_observer(url, cfg):
    # A browser dependency is not a model dependency. Ordinary reads load no Jev credentials.
    try:
        from tools.pro_transport.cdp_observer import ConversationObserver
    except ModuleNotFoundError:
        from cdp_observer import ConversationObserver
    return ConversationObserver(url, cfg["cdp_url"])


def interact_with_connector(url, operation, cfg):
    """Only an already authorised browser interaction invokes Jev; never sends a question."""
    load_jev(cfg)
    import jev_ultrafast.agent as jev_agent
    agent = jev_agent.Agent(url, "Handle only the authorised connector permission prompt.")
    try:
        return approve_connector(agent, operation, cfg)
    finally:
        agent.close()


def _conversation_id(url):
    match = SETTLED_URL.search(url or "")
    return match.group(0) if match else None


def _wait_seconds(deadline, limit):
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise WaitCallTimeout("the total wait deadline expired")
    return min(limit, seconds)


def _observe_wait_page(agent, cfg, deadline):
    if not bounded_wait_call(
        lambda: cdp_version(cfg), _wait_seconds(deadline, WAIT_RPC_SECONDS), "CDP health check"
    ):
        raise WaitReadFailure("Chrome/CDP is not running")
    page = bounded_wait_call(
        lambda: facts(agent.browser), _wait_seconds(deadline, WAIT_RPC_SECONDS), "browser observation"
    )
    if not isinstance(page, dict) or not isinstance(page.get("turns"), list):
        raise WaitReadFailure("browser observation returned no conversation facts")
    return page


def _bind_operation_turn(page, operation, committed):
    """Relocate this operation's user turn in the current DOM observation."""
    expected_hash = operation.get("squashed_sha256")
    candidates = []
    for index, turn in enumerate(page["turns"]):
        if turn.get("role") != "user":
            continue
        body = turn.get("message_body")
        message = squash(body if body is not None else turn.get("text"))
        matches = message == committed if committed is not None else (
            bool(expected_hash)
            and hashlib.sha256(message.encode()).hexdigest() == expected_hash
        )
        if matches:
            candidates.append((index, turn))
    if len(candidates) != 1:
        raise WaitReadFailure(
            "conversation does not contain exactly one user turn for this operation"
        )
    index, turn = candidates[0]
    attachment = operation.get("attachment")
    if attachment and attachment not in (turn.get("turn_text") or ""):
        raise WaitReadFailure("the operation's attachment is absent from its user turn")
    return index


def _answer_after_turn(page, user_index):
    """Return the last assistant text only after its own final controls appear."""
    answers = []
    for turn in page["turns"][user_index + 1:]:
        if turn.get("role") == "user":
            break
        if turn.get("role") == "assistant" and (turn.get("text") or "").strip():
            answers.append(turn)
    if not answers or answers[-1].get("final_controls") is not True:
        return ""
    return answers[-1]["text"].strip()


def _receipt_commits(answer):
    """Keep only hashes presented as a newly written result, not arbitrary source references."""
    receipt_words = re.compile(
        r"\b(?:wrote|written|created|pushed|committed|updated)\b|"
        r"(?:已|成功)?(?:写入|提交|推送|更新)",
        re.IGNORECASE,
    )
    delivery_words = re.compile(r"github|answer|notes|repository|repo|答案|答复|仓库|文件", re.IGNORECASE)
    failed_words = re.compile(r"unavailable|failed|unable|cannot|can't|不可用|失败|无法|不能", re.IGNORECASE)
    commits = []
    for line in answer.splitlines():
        if receipt_words.search(line) and delivery_words.search(line) and not failed_words.search(line):
            commits.extend(re.findall(r"\b[0-9a-f]{40}\b", line, re.IGNORECASE))
    return list(dict.fromkeys(commit.lower() for commit in commits))


def approve_connector(agent, operation, cfg):
    """Owner, 2026-09-19: Jev answers a connector permission prompt with "Always allow", for the
    connectors the owner named in ``approval_connectors`` (GitHub, needed for engineering collaboration).

    Jev finds and clicks the button. The one click that executes is "Always allow" on a prompt that
    names an allowed connector; any other prompt or target leaves the prompt for a human.
    """
    from jev_ultrafast.browser import StalePage
    state, browser = agent.state, agent.browser
    words = facts(browser)["approval_text"]
    connector = next((c for c in cfg.get("approval_connectors", []) if c.lower() in words.lower()), None)
    if cfg.get("approval_policy") != "always_allow" or connector is None:
        return False
    goal = (f"A permission prompt asks whether to allow the {connector} connector for this conversation. "
            "Click the button named exactly '始终允许' (Always allow). Click nothing else. "
            "DONE when the prompt is gone.")
    state.update(goal=goal, plan=[goal], history=[], status="ready", decision=None)
    for _ in range(4):
        if not facts(browser)["approval"]:
            break
        state["page"] = browser.observe(screenshot=False)
        try:
            agent.command("predict")
            choice = state["decision"]["choice"]
            action = next((a for a in state["page"]["actions"] if a["id"] == choice), None)
            if action and action["kind"] == "wait":
                state["decision"] = None
                time.sleep(1)
                continue
            node = browser.evaluate(NODE_FACTS + f"({json.dumps(action['node'])})") \
                if action and action["kind"] == "click" else None
            if not node or node["text"] not in ALWAYS_ALLOW:
                state["decision"] = None
                return False
            agent.command("act", {"fingerprint": state["page"]["fingerprint"]})
            operation.save(approvals=operation.data.get("approvals", []) + [f"{connector}: always allow"])
            time.sleep(2)
        except StalePage:
            state.update(decision=None, status="ready")
    return not facts(browser)["approval"]


def command_wait(args, cfg):
    """Observe one accepted conversation and recover a failed read channel without resending."""
    operation = Operation(cfg, args.key)
    data = operation.data
    if not data.get("send_attempted"):
        raise PreSendFailure("no attempted send under this key")
    recorded_url = data.get("conversation_url") or ""
    url = args.conversation_url or recorded_url
    if not SETTLED_URL.search(url):
        raise PreSendFailure("no settled conversation URL; find the conversation and pass --conversation-url")
    if _conversation_id(recorded_url) and _conversation_id(recorded_url) != _conversation_id(url):
        raise PreSendFailure("--conversation-url is not this operation's settled conversation")

    committed = squash(Path(args.prompt_file).read_text(encoding="utf-8")) \
        if args.prompt_file else None
    if committed and hashlib.sha256(committed.encode()).hexdigest() != data.get("squashed_sha256"):
        raise PreSendFailure("--prompt-file is not this operation's committed text")

    deadline = time.monotonic() + max(0.0, args.timeout)
    mode = args.mode or data["mode"]
    told = None
    agent = None
    recoveries = 0
    last_error_type = None
    verified = False
    previous, stable, answer = None, 0, ""
    needs_recovery = False

    def status(value):
        nonlocal told
        if value != told:
            print(f"wait: {value}", file=sys.stderr, flush=True)
            told = value

    def remaining(limit):
        return _wait_seconds(deadline, limit)

    def close_agent():
        nonlocal agent
        if agent is not None:
            try:
                bounded_wait_call(agent.close, min(WAIT_RPC_SECONDS, 2.0), "browser close")
            except WaitCallTimeout:
                pass
            except Exception:
                pass
        agent = None

    def finish(state, reason=None, **extra):
        value = {"state": state, "conversation_url": url, "recoveries": recoveries, **extra}
        if reason:
            value["reason"] = reason
        return value

    try:
        while time.monotonic() < deadline:
            if agent is None:
                try:
                    cdp_alive = bool(bounded_wait_call(
                        lambda: cdp_version(cfg), remaining(WAIT_RPC_SECONDS), "CDP health check"
                    ))
                except WaitCallTimeout as error:
                    cdp_alive = False
                    last_error_type = type(error).__name__
                except Exception:
                    cdp_alive = False
                    last_error_type = "CDPHealthCheckError"
                needs_recovery = needs_recovery or not cdp_alive
                if needs_recovery:
                    if recoveries >= WAIT_RECOVERY_ATTEMPTS:
                        status("error")
                        return finish(
                            "ERROR",
                            "browser recovery budget exhausted before the conversation was readable",
                            error_type=last_error_type or "ChromeUnavailable",
                        )
                    recoveries += 1
                    status("recovering")
                try:
                    if not cdp_alive:
                        bounded_wait_call(
                            lambda: chrome_start(cfg, mode),
                            remaining(WAIT_OPEN_SECONDS),
                            "Chrome recovery",
                        )
                    agent = bounded_wait_call(
                        lambda: make_wait_observer(url, cfg),
                        remaining(WAIT_OPEN_SECONDS),
                        "conversation open",
                    )
                    page = _observe_wait_page(agent, cfg, deadline)
                except WaitCallTimeout as error:
                    last_error_type = type(error).__name__
                    close_agent()
                    needs_recovery = True
                    continue
                except Exception as error:
                    last_error_type = type(error).__name__
                    close_agent()
                    needs_recovery = True
                    continue
            else:
                try:
                    page = _observe_wait_page(agent, cfg, deadline)
                except WaitCallTimeout as error:
                    last_error_type = type(error).__name__
                    close_agent()
                    needs_recovery = True
                    previous, stable = None, 0
                    continue
                except Exception as error:
                    last_error_type = type(error).__name__
                    close_agent()
                    needs_recovery = True
                    previous, stable = None, 0
                    continue

            if page.get("login") or page.get("auth_required"):
                status("auth")
                return finish("NEEDS_HUMAN", "provider login is required")
            if page.get("challenge"):
                status("auth")
                return finish("NEEDS_HUMAN", "provider human verification is required")
            if page.get("page_error"):
                status("error")
                return finish("ERROR", "provider page reported an unrecoverable error")
            current = _conversation_id(page.get("url"))
            if current and current != _conversation_id(url):
                status("error")
                return finish("ERROR", "browser moved to a different settled conversation")
            if current is None:
                # A newly created CDP tab may still be about:blank during navigation.
                # Give it this bounded window instead of repeatedly destroying loading tabs.
                status("loading")
                previous, stable = None, 0
                time.sleep(min(WAIT_SAMPLE_SECONDS, max(0.0, deadline - time.monotonic())))
                continue
            if not page["turns"]:
                status("loading")
                time.sleep(min(WAIT_SAMPLE_SECONDS, max(0.0, deadline - time.monotonic())))
                continue
            try:
                bound_turn = _bind_operation_turn(page, data, committed)
            except WaitReadFailure as error:
                status("error")
                return finish("ERROR", str(error), error_type=type(error).__name__)
            needs_recovery = False
            if not verified:
                operation.save(
                    conversation_url=url,
                    send_effect="sent",
                    attachment_seen=bool(
                        not data.get("attachment")
                        or data["attachment"] in (page["turns"][bound_turn].get("turn_text") or "")
                    ),
                )
                verified = True
                previous, stable = None, 0
                status("accepted")

            if page.get("approval"):
                words = page.get("approval_text", "")
                permitted = cfg.get("approval_policy") == "always_allow" and any(
                    connector.lower() in words.lower() for connector in cfg.get("approval_connectors", [])
                )
                if not permitted:
                    return finish("NEEDS_HUMAN", "an authorization prompt requires human review",
                                  approval_prompt=page["approval"])
                # Release the read-only tab before the narrowly authorised Jev interaction.
                close_agent()
                try:
                    approved = bounded_wait_call(
                        lambda: interact_with_connector(url, operation, cfg),
                        remaining(WAIT_OPEN_SECONDS),
                        "connector approval",
                    )
                except WaitCallTimeout:
                    approved = False
                except Exception:
                    approved = False
                if approved:
                    previous, stable = None, 0
                    continue
                status("auth")
                return finish(
                    "NEEDS_HUMAN",
                    "an authorization prompt requires human review",
                    approval_prompt=page["approval"],
                )

            answer = _answer_after_turn(page, bound_turn)
            status("generating" if page.get("stop_button") else "accepted")
            stable = stable + 1 if answer and not page.get("stop_button") and answer == previous else 0
            if stable >= 3:  # four equal final-response samples, no Stop control
                break
            previous = answer
            time.sleep(min(WAIT_SAMPLE_SECONDS, max(0.0, deadline - time.monotonic())))

        if stable < 3:
            return finish(
                "IN_PROGRESS",
                "observation window ended while Pro was still thinking"
                if told == "generating"
                else "observation window ended before a final reply was observed",
                partial_answer_chars=len(answer),
            )

        out = Path(args.answer_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(answer + "\n", encoding="utf-8")
        answer_sha256 = hashlib.sha256(answer.encode()).hexdigest()
        commits = _receipt_commits(answer)
        kind = "receipt" if commits and len(answer) < 1500 else "chat answer"
        operation.save(completion="COMPLETE", answer_sha256=answer_sha256, receipt_commits=commits)
        status("complete")
        return finish(
            "COMPLETE",
            answer_file=str(out),
            answer_sha256=answer_sha256,
            answer_chars=len(answer),
            kind=kind,
            receipt_commits=commits,
        )
    finally:
        close_agent()


def git(*argv):
    return subprocess.run(["git", "-C", str(REPO), *argv], check=True, capture_output=True, text=True).stdout


def answer_block(text, question_heading, answer_heading):
    """(before, answer, after) around the answer subsection of one question; None if the headings are not unique."""
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line.strip() == question_heading.strip()]
    if len(starts) != 1:
        return None
    end = next((i for i in range(starts[0] + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    heads = [i for i in range(starts[0], end) if lines[i].strip() == answer_heading.strip()]
    if len(heads) != 1:
        return None
    return "\n".join(lines[:heads[0] + 1]), "\n".join(lines[heads[0] + 1:end]), "\n".join(lines[end:])


def command_deliver(args, cfg):
    """Read the delivery, not the receipt: find the answer commit and check it against the pinned source."""
    git("fetch", "--quiet", args.remote, args.branch)
    tip = f"{args.remote}/{args.branch}"
    candidates = git("rev-list", "--reverse", f"{args.source_sha}..{tip}", "--", args.target_path).split()
    receipt = Operation(cfg, args.key).data.get("receipt_commits", []) if args.key else []
    source = answer_block(git("show", f"{args.source_sha}:{args.target_path}"), args.question_heading,
                          args.answer_heading)
    if source is None:
        raise PreSendFailure("the pinned source does not hold exactly one such question and answer heading")
    found = []
    for commit in candidates:
        parent = git("rev-parse", f"{commit}^").strip()
        block = answer_block(git("show", f"{commit}:{args.target_path}"), args.question_heading, args.answer_heading)
        before = answer_block(git("show", f"{parent}:{args.target_path}"), args.question_heading, args.answer_heading)
        if block is None or before is None or block[1].strip() == before[1].strip():
            continue  # this commit did not write this answer
        files = git("diff", "--name-only", parent, commit).split()
        found.append({
            "commit": commit, "parent": parent, "parent_is_source": parent == args.source_sha,
            "named_in_receipt": commit in receipt, "files": files,
            "question_unchanged": block[0] == source[0],
            "rest_of_file_unchanged": block[0] == before[0] and block[2] == before[2],
            "answer_was_empty": not before[1].strip(), "answer_chars": len(block[1].strip()),
        })
    clean = [f for f in found if f["files"] == [args.target_path] and f["question_unchanged"]
             and f["rest_of_file_unchanged"] and f["answer_was_empty"]]
    state = "DELIVERED" if len(found) == 1 and clean else "CONFLICT" if found else "NOT_DELIVERED"
    result = {"state": state, "branch": tip, "commits": found,
              "receipt_commits_not_on_branch": [c for c in receipt if c not in candidates]}
    if state == "DELIVERED" and args.answer_out:
        out = Path(args.answer_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(answer_block(git("show", f"{found[0]['commit']}:{args.target_path}"),
                                    args.question_heading, args.answer_heading)[1].strip() + "\n", encoding="utf-8")
        result["answer_out"] = str(out)
    return result


def question_key(repository, branch, subject, source_sha, target_path, question_heading):
    fields = [repository, branch, subject, source_sha, target_path, question_heading]
    return "hmasd:" + hashlib.sha256(json.dumps(fields).encode()).hexdigest()


def command_compose(args, cfg):
    """Keep the complete author message in the attachment and compose its short cover note."""
    message = Path(args.message_file).read_text(encoding="utf-8").strip() + "\n"
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", args.slug):
        raise PreSendFailure("slug: lower-case letters, digits and hyphens")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    document = out / f"hmasd-pro-question-{args.slug}.md"
    document.write_text(message, encoding="utf-8")
    digest = hashlib.sha256(message.encode()).hexdigest()
    short = out / f"{args.slug}.short.txt"
    short.write_text(
        f"这是一项 HMASD Pro 研究请求（主题：{args.subject}）。完整请求在附件 {document.name} 中，"
        "请阅读全文，包括其中的材料读取要求、答复要求和 GitHub Answer 写入位置，并严格据此作答。\n\n"
        "请优先将完整答复写入附件指定的 GitHub Answer。若 GitHub 读取或写入不可用，请如实说明；"
        "若已读材料足以支持答复，仍请在当前聊天中输出完整答复，并明确任何信息缺口。"
        "若缺少关键来源，请说明缺口，不要假装已经阅读，也不要凭记忆补全。"
        "若无法读取附件，请说明后停止，不要凭记忆作答。\n",
        encoding="utf-8")
    return {"document": str(document), "document_sha256": digest, "short_message": str(short)}


def public(result, show_url):
    """Owner, 2026-09-18: this account's conversation addresses stay in the local operation file."""
    if show_url or not isinstance(result, dict):
        return result
    return {key: ("recorded locally" if key == "conversation_url" and value else value)
            for key, value in result.items()}


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
    send.add_argument("--attach", default=None, help="one document uploaded with the message")
    send.add_argument("--mode", choices=("headless", "headed"), default="headless")
    send.add_argument("--dry-run", action="store_true", help="stop at the send button without clicking it")
    reconcile = sub.add_parser("reconcile")
    reconcile.add_argument("--key", required=True)
    wait = sub.add_parser("wait")
    wait.add_argument("--key", required=True)
    wait.add_argument("--answer-file", required=True)
    wait.add_argument("--timeout", type=float, default=1470, help="bounded observation seconds; queue wait windows supply the remaining time")
    wait.add_argument("--prompt-file", default=None, help="the committed text, to verify the conversation holds it")
    wait.add_argument("--conversation-url", default=None, help="reconcile a URL the send could not observe")
    wait.add_argument("--mode", choices=("headless", "headed"), default=None)
    question = argparse.ArgumentParser(add_help=False)
    for name in ("--repository", "--branch", "--subject", "--source-sha", "--target-path", "--question-heading"):
        question.add_argument(name, required=True)
    sub.add_parser("key", parents=[question])
    compose = sub.add_parser("compose")
    compose.add_argument("--message-file", required=True, help="the author's complete message, unchanged")
    compose.add_argument("--slug", required=True)
    compose.add_argument("--subject", required=True, help="direction id or 'portfolio'")
    compose.add_argument("--out-dir", default=str(REPO / "temp" / "pro_transport"))
    deliver = sub.add_parser("deliver")
    deliver.add_argument("--key", default=None, help="to compare against the commits the chat receipt named")
    for name in ("--branch", "--source-sha", "--target-path", "--question-heading"):
        deliver.add_argument(name, required=True)
    deliver.add_argument("--answer-heading", default="### Answer")
    deliver.add_argument("--remote", default="origin")
    deliver.add_argument("--answer-out", default=None, help="also save the delivered answer text here")
    for command in (send, wait, reconcile):
        command.add_argument("--show-url", action="store_true",
                             help="print the conversation address; by default it stays in the local operation file")
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
        elif args.command == "reconcile":
            result = command_reconcile(args, cfg)
        elif args.command == "key":
            result = {"key": question_key(args.repository, args.branch, args.subject, args.source_sha,
                                          args.target_path, args.question_heading)}
        elif args.command == "compose":
            result = command_compose(args, cfg)
        elif args.command == "deliver":
            result = command_deliver(args, cfg)
        else:
            # A stopped script window cancels observation only. Unwind the wait's finally
            # block so the CDP tab owned by this process is closed before exit.
            previous_term = signal.getsignal(signal.SIGTERM)
            def cancel_observation(_signum, _frame):
                raise KeyboardInterrupt("observation cancelled")
            signal.signal(signal.SIGTERM, cancel_observation)
            try:
                result = command_wait(args, cfg)
            finally:
                signal.signal(signal.SIGTERM, previous_term)
    except PreSendFailure as error:
        print(json.dumps({"error": str(error), "pre_send": args.command == "send"}, ensure_ascii=False))
        return 2
    print(json.dumps(public(result, getattr(args, "show_url", False)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
