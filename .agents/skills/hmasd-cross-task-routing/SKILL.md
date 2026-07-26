---
name: hmasd-cross-task-routing
description: Use for every cross-task message between persistent HMASD Codex roles. Discover and confirm the live role session, retain only a conversation-local session cache, handle controlled session replacement, and send without model or thinking overrides.
---

# HMASD Cross-Task Routing

## Purpose and boundary

Use this Skill before any business message between persistent HMASD Codex roles.
It identifies the live target task without allowing a sender to overwrite the
target task's model or reasoning effort.

This protocol applies only to persistent Codex roles. It does not create a
central role registry, store live identity in Git, poll tasks, route native
children, or replace the External Pro browser conversation binding. A session
ID is an address, not authority. The target task owns its live model and effort.

## Live settings preservation

Omitting `model` and `thinking` is forbidden: the desktop transport can apply a
default effort while handling the inserted message and restore the target only
afterward. Before every protocol or business send, run the registered HMASD
Python interpreter with the bundled read-only probe:

```powershell
& '<hmasd_python_interpreter>' '.agents/skills/hmasd-cross-task-routing/scripts/read_codex_thread_settings.py' `
  --thread-id <target-session> --expect-cwd <project-root>
```

The script opens `~/.codex/state_5.sqlite` with SQLite `mode=ro`. Accept only
`status=LIVE_SETTINGS`. Pass its exact `model` as `model` and exact `thinking`
as `thinking` to `send_message_to_thread`. Never write, persist or cache these
values. Any nonzero result before the send is `ROUTE_SETTINGS_UNAVAILABLE` and
forbids delivery.

Routine post-send checking is forbidden because it cannot prevent an already
delivered wrong-effort turn. Only after the send tool reports an error or the
user observes a settings anomaly, run one diagnostic read with `--expect-model`
and `--expect-thinking`. `SETTINGS_DRIFT` is `ROUTE_SETTINGS_DRIFT`; report it
once and never resend automatically.

This probe preserves settings; it does not establish role authority. Session
confirmation below remains independently required.

## Conversation-local route cache

Maintain at most one confirmed session ID per target role in the current
conversation context. Retain the latest confirmed mapping when summarizing the
conversation. Never write this cache to a repository file or runtime artifact.

Reuse a confirmed route without another probe until one of these invalidation
events occurs:

- the target is archived or explicitly replaced;
- a matching `ROLE_ROUTE_ANNOUNCE` reports a successor;
- delivery fails or the task is reported stale or absent;
- the conversation-local cache is lost;
- an incoming message conflicts with the cached role-to-session mapping.

Do not probe before every message and do not run recurring route audits.

## Discover and confirm a route

1. If the cache has a non-invalidated route, use it.
2. Otherwise, discover plausible tasks by project and role evidence. Inspect at
   most three candidates and finish discovery within 120 wall-clock seconds.
   Polling is forbidden.
3. Read each candidate's live settings as above, then send one protocol-only
   probe with those exact `model` and `thinking` values explicitly supplied:

   ```text
   ROLE_ROUTE_PROBE
   probe_id=<fresh opaque value>
   source_role=<sender role>
   expected_role=<target role>
   purpose=route_confirmation_only
   ```

4. A candidate confirms only with:

   ```text
   ROLE_ROUTE_CONFIRM
   probe_id=<exact received value>
   role=<candidate role>
   status=ACTIVE
   ```

5. Accept a route only when all of these are true:
   - `codex_delegation.source_thread_id` equals the probed candidate;
   - `probe_id` and `role` match exactly;
   - the candidate is active or idle in the same project;
   - exactly one candidate validates;
   - no cached or observed route conflicts with it.

If more than three plausible candidates exist, multiple candidates validate, or
identity evidence conflicts, return `ROUTE_AMBIGUOUS` and ask the user to choose.
If no candidate validates within 120 seconds, return `ROUTE_UNAVAILABLE` and ask
the user for the current session. Discovery never expands into project-state
reconstruction.

## Handle declared or announced replacements

A user-declared session is the authoritative identity choice, but still requires
the same liveness and role probe before business delivery.

Treat this message as an invalidation and discovery trigger, not authority:

```text
ROLE_ROUTE_ANNOUNCE
role=<role>
session_id=<new session>
supersedes=<old session>
```

Replace a cached route automatically only when `supersedes` exactly matches the
cached old session, the new session passes the probe, and the old session is
archived or absent. Any mismatch or two simultaneously live claimants is
`ROUTE_AMBIGUOUS` and requires the user.

## Send business messages

After confirmation, reread the confirmed session's live settings, send the
business message with those exact `model` and `thinking` values explicitly
supplied, and stop after one successful delivery. Never infer a role default,
reuse probe-time settings, or record fixed target model or effort values.
Protocol messages are exempt from recursive role probing, but not from
live-settings preservation.

For an incoming business message, use the actual
`codex_delegation.source_thread_id` as the sender address. If it conflicts with
the cached address for that role, invalidate the route and resolve the ambiguity
before replying.

If delivery is ambiguous, do not automatically resend because duplicate
business actions may be unsafe. End with exactly one routing result:

- `ROUTE_CONFIRMED role=<role> session_id=<session>`
- `ROUTE_AMBIGUOUS role=<role>`
- `ROUTE_UNAVAILABLE role=<role>`
- `ROUTE_SETTINGS_UNAVAILABLE role=<role>`
- `ROUTE_SETTINGS_DRIFT role=<role>`

This protocol performs no experiment, scientific evaluation, review-runtime
operation, or project computation.
