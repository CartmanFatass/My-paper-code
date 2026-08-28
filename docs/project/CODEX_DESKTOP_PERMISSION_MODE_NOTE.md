# Codex Desktop permission mode note

Status: current operational note  
Observed at: 2026-08-28  
Applies to: HMASD local tasks on Windows Codex Desktop

## Observation

Earlier Codex Desktop builds exposed a composer option named `Custom (config.toml)`. That option
allowed HMASD to rely on project and custom-agent configuration without selecting a parent live
permission override. On 2026-08-28 the option was no longer visible in the current UI, including
after a full Desktop restart.

Permission smoke task `01a04984-1dff-7f83-ac4a-412f686a385c` observed both sides of the current
behavior:

- the fresh top-level HMASD task created and removed an out-of-workspace sentinel without a
  per-command approval;
- its `HMASDCMScout` loaded the agent profile that declares `sandbox_mode = "read-only"` and
  `approval_policy = "never"`, but the Scout could still create a sentinel outside the project;
- both sentinels were removed and the repository remained clean.

The test therefore proves neither that all custom-agent configuration was ignored nor that a
specific internal override caused the result. It proves only that the child `read-only` declaration
was not an effective runtime isolation boundary in that execution.

## Current decision

The user keeps the Desktop composer at `Approve for me`. HMASD does not change user, project, or
agent permission configuration as part of this decision.

Scout, Reviewer, Verifier, and Critic remain intended read-only roles. Their existing read-only
profile is retained. Until the product behavior changes or a later protocol decision is explicitly
accepted, this note records the observed limitation without changing the active workflow authority,
role skills, or permission configuration.

If Codex Desktop restores the Custom option or adds a per-spawn permission control that
demonstrably preserves child isolation, Root may run a new bounded smoke test and revise this note.
