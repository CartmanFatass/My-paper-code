# Durability Kernel V1 Migration Report

```text
baseline_commit=04eb640f4090993b251b204096cff26b44350b90
schema_from=6
schema_to=7
live_acceptance=absent
```

## Schema

Additive v6→v7 adds version columns, effect references, `app_server_effects`,
`control_transitions`, and `operator_resolutions`. `mutation_intents` is
preserved. No table is dropped.

## Direct-write inventory

Before: 26 `UPDATE` sites across eight business modules.

After cutover, protected state changes go through `TransitionKernel` for
bindings, managed turns, wake batches, mailbox delivery/intake, commands, and
effects. SQLite triggers reject illegal edges and version-less state updates.

## Known remaining compatibility paths

`SessionGuard.request()` may still send mutations through the single session
owner using prepare/send/await until every remaining caller is moved onto
`submit_effect`. `MutationIntentStore.begin()` still exists for unread
legacy rows; new managed-turn and provisioning paths no longer write it.

## Live-only limitations

Live App Server, Phase 1, Stage 3, and Stage 4 acceptance remain deferred.
That absence is not a code defect.
