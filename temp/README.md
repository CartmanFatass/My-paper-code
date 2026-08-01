# Temporary cross-task handoffs

`temp/sessions/<role>/handoffs/` holds sender-owned, short-lived payloads shared
between HMASD Codex tasks in this checkout. Use it when a UTF-8 payload exceeds
8 KiB or exact bytes must survive task-message rendering and summarization.

Create and verify payloads with:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  '.agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py' write `
  --owner-role <source-role> `
  --label <purpose> --source <source-file>

& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  '.agents/skills/hmasd-cross-task-routing/scripts/hmasd_cross_task_payload.py' verify `
  --owner-role <locked-source-role> `
  --path <temp/sessions/<role>/handoffs/path> --bytes <count> --sha256 <digest>
```

Actual payloads are ignored by Git. A cross-task message carries only the
relative path, owner role, byte count, SHA-256, UTF-8 encoding and purpose. The
receiver verifies using the locked source role before reading and acknowledges
the same path and digest after use. Payloads are never deleted automatically;
only the source owner may perform a separate cleanup action after
acknowledgement.
