# Sparse-window relay toy (SWR)

Standard-library-only Python (no numpy, no torch), every random draw seeded. It is the low-cost check
for the scenario in
`docs/Claude_docs/environment_design/SPARSE_WINDOW_RELAY_SCENARIO_DESIGN_20261002.md`: a gridworld in
which corner sites are served only through a held two- or three-UAV relay chain, one site is open at a
time in a known schedule, and a window pays +1 once the chain has been held for five ticks inside it.
Nothing else pays in the sparse variant; the decoy variant adds a small dense reward for sitting next to
the base station.

Files:

- `swr_toy.py` — environment, zero-learning references, tabular REINFORCE analogs of flat PPO,
  count-based exploration, hierarchy without discriminators and HMASD-style hierarchy with
  discriminator rewards (`λ_D = .05`, `λ_d = .02`, and a ×4 variant).
- `results_raccess1.json`, `results_raccess2.json` — outputs of the two difficulty rungs
  (access range 1 = one chain per corner, the needle; 2 = wider).
- `RESULTS.md` — the readings and what they change.

Run: `python3 swr_toy.py --r-access 1 --out results_raccess1.json` (defaults: 5,000 episodes, seeds
1–5, decoy 0 and .002, five arms; about 5 ms per episode).

Instrument check only: the learners are small analogs, not the project's PPO, Transformer coordinator
or learned low-level skills; no project host, node or fit is involved.
