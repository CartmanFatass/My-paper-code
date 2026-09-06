# B01 seeds 2/3 technical launch record

The DM prospective supplement at `66a4fced6fa6558e7a8a94ad940e263bc71cbea3` selects only
seeds2 then3. Amendment `72b0bcf7f` authorizes the one-line runner repair after CM observed
accepted CLI `choices=[1]` rejects either seed. No invocation was launched for that conflict.

Exact source commit **`b77f897da7dea5df2e9230f43c8f128cc281afb3`** was committed/pushed.
The only source delta from accepted seed1 source is `choices=[1]` to `choices=[1, 2, 3]` in
`scripts/run_vsp03_b01.py`; every other source line is preserved. A standard-library AST check
compared the exact replacement and executed only the actual three argparse setup statements,
then parsed seeds1,2,3 successfully. No learner import/model/RNG/episode/optimizer state occurred.
No new source-review, smoke, profiling, replay or implementation programme. Scope:none.

Scientific acceptance, batch state ownership, information/reward/loss/RNG semantics and output
contract are unchanged from the original technical acceptance and DM supplement. Same CPU
float32, one scientific process/compute thread, complete128x128training per arm and all40ticks.
Each selected invocation includes its existing eight-case check, three endpoints and F, and
ends at completion, its1800s whole cap or an actual required-path defect. Scientific signs do
not determine whether seed3 executes. Stop after both returns; no seed4.

Per-arm projection reuses seed1's complete measured cost law: T1.037851087s, G0.568588821s,
shared0.758430249s, total2.364870157s per pair and4.729740314s summed for both. This is a
conditional projection, not a bound. Actual ordinary batch phases and full walls are retained.
Publication coverage reuses the unchanged integrated check plus actual endpoint/state readback;
no separate pilot or simulation. Each pair plans1454400ticks/256joint steps.

Remote node `wsl_4070`, SSH `hmasd-wsl-node`, configured Python `/home/wu/.venvs/hmasd/bin/python`.
Prepare detached cwd `/home/wu/hmasd-worktrees/vsp03-b01-seeds23-r01` at b77f897da above.
Host/device portability remains the original CPU contract, no cross-host bit identity or migration.

For s=2, then s=3 only, exact separate supervisor task is `vsp03-b01-seed<s>-r01-20260905`:

```text
cd /home/wu/hmasd-worktrees/vsp03-b01-seeds23-r01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vsp_03/exp/vsp03_b01_seed<s>_r01_memory.json && timeout 1800s /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b01.py --seed <s> --out temp/directions/vsp_03/exp/vsp03_b01_seed<s>_r01
```

Each command gets its own immediate actual-node memory admission, requiring physical/effective
available memory at least4GiB. Distinct output roots and receipt files are as above. Durable log,
status and exit files are under `/home/wu/.agent-tasks/vsp03-b01-seed<s>-r01-20260905/`.
Existing root tracker receives each accepted task; CM retains observation until adoption ACK.
Seed3 launch follows seed2 terminal required-path collection, not its scientific result.
Local collection is under the same relative output roots in the CM worktree. Broader study
elapsed includes control-plane gaps; report summed invocation walls separately.
