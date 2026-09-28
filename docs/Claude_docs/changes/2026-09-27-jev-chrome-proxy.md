# 2026-09-27 — Jev transport: the driver's Chrome receives the page proxy explicitly

Observed on the WSL host after the 2026-09-27 reboot: `tools/pro_transport/jev_send.py send --dry-run`
failed pre-send with `Page.navigate timed out after 5s waiting for the daemon`; the Chrome it had
started could not load any page (a CDP-opened `https://example.com/` tab stayed untitled), while
`curl` through the shell's `https_proxy` reached both chatgpt.com and github.com. Cause: WSL mirrored
networking now carries a TUN adapter (`eth2`, 198.18.0.1/30) whose default route has metric 1, so
direct traffic is black-holed; Chrome does not apply the shell's proxy variables on this host.

## Change

- `tools/pro_transport/jev_send.py`: new `chrome_proxy(cfg)`; `chrome_start` appends
  `--proxy-server=<[jev] proxy_server or https_proxy/HTTPS_PROXY/http_proxy/HTTP_PROXY>` and
  `--proxy-bypass-list=<proxy_bypass or no_proxy/NO_PROXY, commas to semicolons>` when a proxy is
  known; the start result reports `proxy: true|false`. No change when no proxy is configured or set.
- `tests/skills/test_jev_transport.py`: `test_chrome_start_passes_shell_proxy_explicitly`.
- `.codex/hmasd-transport.toml`: commented optional `proxy_server` / `proxy_bypass` keys.

Owner authority: 2026-09-15 lifting of the control-plane restriction (any file, traceable in Git,
documented here) and 2026-09-27 permission to modify the Jev-related tooling. No science, no send
semantics, no send_attempted boundary changed; a running Chrome is never restarted by this change.

## Addendum (same day): the stall was the keyring prompt, not the proxy

Net log of a throwaway profile: the navigation request reached `COMPUTED_PRIVACY_MODE` and never
sent (no request arrived at a logging loopback server), while cookie-less background fetches
completed. The user journal shows `gcr-prompter` starting a keyring password prompt at the moment
the driver's Chrome started; this boot runs a D-Bus session bus and `gnome-keyring-daemon
--components=secrets`, which the previous boots did not expose to Chrome. Chrome auto-selected
the keyring, waited headless for the unlock, and every cookie-bearing request stalled. Throwaway
profiles with `--password-store=basic`, or with `DBUS_SESSION_BUS_ADDRESS` unset, loaded pages at
once (`Example Domain`; the loopback GET arrived). The "Failed to decrypt token" line in
`chrome.log` (17:16 today, first after the reboot) is the same key-store switch seen from the
other side: the profile's stored secrets were written with the basic store.

- `tools/pro_transport/jev_send.py`: `chrome_start` always passes `--password-store=basic`.
- The proxy claim above ("Chrome does not apply the shell's proxy variables") was not established;
  the explicit `--proxy-server` flag is kept because the direct route is black-holed and the flag
  removes the dependence on Chrome's environment detection. Sandbox-disabling diagnostics were
  not run (auto-mode classifier denial, reported to the owner).

## Correction (2026-09-27, later the same day)

The addendum's sentence "the profile's stored secrets were written with the basic store" is withdrawn as
not established. Against it: the previous boot's user journal shows an `org.freedesktop.secrets`
activation on 2026-09-25 05:07 and `~/.local/share/keyrings/Default_Keyring.keyring` was modified at
05:17 that day, so a keyring was live while the pre-reboot Chrome ran. The only cookie database read
first-hand was the legacy `Default/Cookies` (eight fresh v10 cookies from the logged-out page load);
the live store under `Default/Network/` was not read (auto-mode classifier denial, "Credential
Exploration", not pursued). Consequence: the `--password-store=basic` pin may itself make a
keyring-encrypted session invisible; with the pin, the provider page loads logged out and a human
login is required. The pin stays until the owner chooses between re-login under the basic store
(headless-safe across reboots) and keyring recovery (pin made configurable first). The code and
configuration comments were reworded to match.

