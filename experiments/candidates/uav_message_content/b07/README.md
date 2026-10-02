B07 is one admitted, non-resumable package. From the immutable launch snapshot run
`experiments/candidates/uav_message_content/b07/run.py` with absolute `--out`,
`--input-manifest`, `--d-checkpoint`, `--b-checkpoint` and their respective
`--input-manifest-sha256`, `--d-checkpoint-sha256`, `--b-checkpoint-sha256`, plus
`--launch-sha` and `--seed 19811`. The seed argument binds the fixed three-seed
package; dimensions, fits and endpoints have no sweep flags. Launch through the
native admission launcher. Output may contain launcher records, but existing B07
scientific output is refused. There is no retry/resume mode.

The input manifest schema is the selected version1 `UAV-MESSAGE-CONTENT-B07-INPUTS`:
`parent_d`/`parent_b` contain absolute path, SHA256 and bytes. `teacher_data` contains
the original summary SHA256, ordered inventory SHA256, total bytes and exactly32
episode records with absolute path, SHA256, bytes, episode, split (`fit` for0–23,
`development` for24–31), and embedded `original_row`. Historical original paths are
provenance and are never dereferenced. Exact checkpoint/data bindings precede model
construction. All teacher targets remain the stored composed means.

The header is a little-endian16-bit word: sender bits0–2, tick bits3–10, valid bit11,
zero reserved bits12–15. Compressed messages append one index byte; lossless
references append six little-endian FP32 values. The public beacon is tick byte then
GOOD/BAD bit0 in a byte whose other bits are zero. Inflight queues contain bytes.
Delivery reconstructs zero field5 and the three zero forecast fields. An installed
book has256 shared FP32 rows and six metric scales:6168 B/device. Packet plus beacon
is5 B/compressed tick and28 B/lossless tick, with unchanged native fee and delay.

`summary.json` retains all12 fit histories/development losses, initialization/final
dictionary movement, selected books, all256 native rows and exposure/resource
ledgers. `progress.json` records the current non-resumable frontier.
`fit-updates.jsonl` flushes every Lloyd pass and Adam update. One active dictionary
is overwritten per update and removed only after its completed artifact is saved;
exceptions retain it or the incomplete native trace with identity in the summary.
Final dictionaries and native traces live under `dictionaries/` and `raw/` with
absolute canonical paths, sizes and hashes. `reading.json` holds independent byte/
cache/action/density/physical reconstruction, frozen neural replay from weights,
all individual service readings, signed comparisons and both uncertainty scopes.

Offline four-episode minibatches unroll256 sequential steps with20 actor rows per
step. Binding/development/native/reader use five rows per step; this may produce
batch-dependent FP32 roundoff. The one purchased uncompressed binding replay
reports discrepancies without subtracting KL or changing labels. Search counts
retain exactly475004928 direct six-coordinate center visits. Native and reader use
separate generators for five three-vector innovations per tick; constructor and
fit RNGs are isolated. No critic/planner or extra actor diagnostic is executed.

The reader rebuilds actor inputs from the saved legal raw observations, previous
executed commands and independently reconstructed transport. It checks physical
positions/clock against those raw observations and independently computes every
post-action user's radio assignment and service from saved FP64 native geometry.
It does not acquire new native worlds. Receiver tensor identity is checked before
and after the whole package. Scientific dimensions/seed validity, complete counters
and artifact identities are required for `COMPLETE`; a technical failure preserves
the actual frontier and returns `INCOMPLETE` without repeating effects.

Telemetry separates worker and waited-for child CPU and peak RSS. Child wall time
is explicitly unmeasured. Main-entry wall excludes interpreter startup; the native
supervisor records external lifetime. Peak RSS fields are lifetime high-water marks,
not summed simultaneous memory. Output bytes are sampled at summary boundaries.
