# Overcooked V2 navigation

`overcooked.py` contains the fixed-shape Flax state, reset/step, and optional per-episode ingredient
permutations. `layouts.py` constructs layouts and, when recipes are unspecified, enumerates unique
three-ingredient combinations in Python during construction.

Performance reading: separate layout/recipe construction from steady-state `reset`/`step` timing.
The state can carry an ingredient permutation per agent; this is a semantic observation mapping,
not a free batch dimension. Follow the wrapper selected by `env.name` before comparing rewards or
episode metrics.

Use explicit key splits for per-agent permutation sampling and environment randomness. Host-side
combination enumeration is a startup/configuration cost and must not be converted into a training
speed claim. No benchmark was run for this overlay.
