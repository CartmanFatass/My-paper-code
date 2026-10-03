# Complete planning-opportunity timing comparison

This source implements the selected G2/A2/G_E/A_E comparison in the direction
notebook's `b01-source-contract-20261003` and `b01-selected-l0-20261003` entries.
It has one fixed operation: four H500 audits and sixteen common result worlds
with four H500 programs each, followed by full uncompressed reconstruction for
each four-mission group. There are no fits, retries, resumes or size switches.

G2/A2 retain the B08 exact-reuse bindings around frozen B03/B04 programs. G_E/A_E
make their second choice at50 after stay or40+first duration+10. Selection precedes
the next ordinary C/E update, so the first moved member remains active and cannot
be selected again. Each A_E candidate has its own modeled second clock. Fresh
actual replanning replaces the first plan even when the second choice declines.

The admitted entry is `run.py`. Launch it only through the current
`scripts/hmasd_launch.py` kernel on configured `local_linux`, from published
inputs with the exact direction lead and `--seed 29523000`.
It calls `require_admission` before scientific imports or output creation, sets
one numerical thread, and performs the entire selected operation once.

`worlds.json` binds the declared initial arrays. `preparation.json` records
metered preparation. `inputs.py` binds all directly used frozen/current source
files, fixed query ceilings and the20 CPUh/48wallh/10GiB operation limits.
`meter.py` reserves finalization resources and permanently stops science on
a limit. A failure preserves its prefix and closes the purchase.

`study.py` records the native trajectory, actual controller history, every
stationary bank and every modeled branch/segment. `reader.py` recomputes the
complete search without recurrence reuse, checks model bits and certificates,
and reconstructs all saved native radio, motion, views and rewards. Native
forecast discrepancies are reported empirically. The fresh reader is real work;
the old B08 zero-query result is not inherited.

After successful full reading of a mission, `evidence.py` projects saved
prefix/suffix arrays from retained complete outer branches and checks exact
payload identity before deleting redundant files. Catalog bindings and partial
deletion records survive deletion failure. The same reader can resolve the
compacted representation, but a second result replay is not authorized.

Tests mirror this directory and use synthetic arrays and fully stubbed scientific
dependencies. They cover timing, precision, counters, admission order, matched
pipeline ordering, signal-stop retention, compaction failure and censored user
gaps. They do not establish native correctness or throughput; the purchased
audits and full reading carry that work.
