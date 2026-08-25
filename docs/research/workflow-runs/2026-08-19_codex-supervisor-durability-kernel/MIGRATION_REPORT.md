# Durability Kernel V1 Migration Report

```text
baseline_commit=04eb640f4090993b251b204096cff26b44350b90
schema_from=6
schema_to=7
live_acceptance=absent
```

## Schema

Additive v6→v7 adds version columns, effect references, `app_server_effects`,
`control_transitions`, `operator_resolutions`, and `transport_seq` on effects.
`mutation_intents` is preserved. No table is dropped.

`initialize_database` conservatively migrates unmatched `mutation_intents`
rows by creating a non-PREPARED `app_server_effects` row and setting
`superseded_by_effect_id`. Existing rows remain queryable as legacy evidence.

## Direct-write inventory

Protected state changes go through `TransitionKernel`, including
`CommandGateway`. SQLite triggers reject illegal edges, version-less state
updates, and operator-only exits whose resolution disposition does not match
the target state.

`MutationIntentStore.begin()` and all legacy state writes are disabled.
`AppServerSessionOwner.request()` and `SessionGuard.request()` reject every
mutating method. `WakeRecovery.resume_once()` uses `submit_effect` and later
read-only classify/reconcile.

## Remaining synthetic limits

Live App Server, Phase 1, Stage 3, and Stage 4 acceptance remain deferred.
That absence is not a code defect.
