# Remote Log Sync

This directory is an isolated Windows-side utility for pulling cloud experiment
logs back to the HMASD workspace through SSH.

Edit `remote_log_sync.config.json`:

- `remote`: SSH target, for example `ubuntu@1.2.3.4`.
- `remoteLogRoot`: remote log root, for example `/home/ubuntu/HMASD/logs_cloud_p0_32env`.
- `localLogRoot`: local mirror directory relative to the repo root, an absolute
  path, or `auto`.
- `intervalMinutes`: scheduled sync period. The default is `30`.
- `ssh.port`: SSH port. Use `0` for the SSH default.
- `ssh.identityFile`: private key path, or an empty string for the SSH default.
- `sync.includePatterns`: relative file patterns below each run directory.

For SSH key authentication, copy `remote_log_sync.ssh_key.example.json` to your
own config file and update `remote`, `remoteLogRoot`, and `ssh.identityFile`.
When `localLogRoot` is `auto`, the script writes to
`dist\remote_log_sync\synced\<remoteLogRoot folder name>`. For example,
`/home/ubuntu/HMASD/logs_cloud_p0_32env` becomes
`dist\remote_log_sync\synced\logs_cloud_p0_32env`.

Default sync content is intentionally lightweight:

- `standalone_train.log`
- `metrics/*.csv`
- `_monitor/*.txt`

Run one dry-run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\dist\remote_log_sync\sync_remote_logs_ssh.ps1 `
  -Config .\dist\remote_log_sync\remote_log_sync.config.json `
  -DryRun
```

Run one real sync:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\dist\remote_log_sync\sync_remote_logs_ssh.ps1 `
  -Config .\dist\remote_log_sync\remote_log_sync.config.json
```

Register the scheduled task from the config:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\dist\remote_log_sync\register_remote_log_sync_task.ps1 `
  -Config .\dist\remote_log_sync\remote_log_sync.config.json `
  -RunNow
```

Preview the scheduled task command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\dist\remote_log_sync\register_remote_log_sync_task.ps1 `
  -Config .\dist\remote_log_sync\remote_log_sync.config.json `
  -DryRun
```

Check or remove the scheduled task:

```powershell
schtasks.exe /Query /TN "HA-CTSE Remote Log Sync" /V /FO LIST
schtasks.exe /Delete /TN "HA-CTSE Remote Log Sync" /F
```
