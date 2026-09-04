# Issue tracker: Local Markdown

Planning specs and implementation tickets live under the gitignored `.scratch/`
directory. They are local coordination artifacts, not durable project authority.

- One effort per `.scratch/<feature-slug>/`.
- The spec is `.scratch/<feature-slug>/spec.md`.
- Tickets are separate files under
  `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered blockers-first.
- Each ticket records `Status: ready-for-agent` and its exact `Blocked by` edges.
- A ticket is available when every listed blocker is complete.

When a planning skill says to publish, write to this layout. Do not create or
modify GitHub issues for HMASD planning unless the user explicitly changes this
configuration.
