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
