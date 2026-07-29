# Temporary cross-task handoffs

`temp/handoffs/` holds local, short-lived payloads shared between HMASD Codex
tasks in this checkout. Use it when a UTF-8 payload exceeds 8 KiB or exact bytes
must survive task-message rendering and summarization.

Create and verify payloads with:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  '.agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py' write `
  --label <purpose> --source <source-file>

& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  '.agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py' verify `
  --path <temp/handoffs/path> --bytes <count> --sha256 <digest>
```

Actual payloads are ignored by Git. A cross-task message carries only the
relative path, byte count, SHA-256, UTF-8 encoding and purpose. The receiver
verifies before reading and acknowledges the same path and digest after use.
Payloads are never deleted automatically; cleanup is a separate explicit action
after acknowledgement.
