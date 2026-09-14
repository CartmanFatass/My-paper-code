# B03 Generic terminal collection and next selected arm

DM technically accepts the complete Generic arm at source
`b257dcb1d7578a057afa9b4bdd7c7ff74ad8e24f`. Supervisor
`folr-b03-781501-generic`, PID3666806, finished with exit0. The recovered
batch Monitor delivered the terminal event directly to this DM; its duplicate
native completion is one event. The preserved child-state snapshot still says
`delivery.terminal=false`; that bookkeeping field does not erase the actual
App terminal delivery or independently collected native terminal facts.

The unchanged summary binds B03, fresh training781501/evaluation1781501 and
GENERIC_RETAIN. Actual5000 training episodes/100000 ticks/4969 updates and
128 final greedy episodes/2560 ticks match the card. All5000 training and128
final returns are finite; Torch threads1/1 and FP32 checkpoint groups match
accepted execution. A single weights-only checkpoint read confirms arm,4969
updates and finite actor/mixer/target tensors; no actor construction, RNG
sampling, learning or additional evaluation was performed.

Final native return mean is4.9259375, sample SD8.014662295605376,
conditional episode SE0.7084027572678379, range[-11.67,24.26] and40/128
negative episodes. These are observations of this one fitted policy, not a
training-population estimate or a B03 pair result. Changing both training and
evaluation seeds from B02 does not isolate pure training variance. BANK's
selected invocation is unchanged by Generic's score.

Complete native invocation wall2005.71s, user1859.24s, system143.95s,
peak RSS767384KiB and exit0 come from GNU time. Runner-reported1943.733741s
and the Monitor's2061s observation uptime are different scopes. The supervisor
log records08:24:20Z to08:57:46Z; integer seconds do not replace native timing.
Collection used3.8429999999934807s measured local/SSH wall; source support,
observation, prior preparation and provider costs remain accumulated and full
totals UNKNOWN. No support or science accounting is reset.

`GENERIC_COLLECTION.json` records every raw output and supervisor member's
byte count/digest. `GENERIC_RAW.tar.gz` preserves the complete output directory,
checkpoint and supervisor records; all copied member hashes and the archive
hash were verified. `GENERIC_SUMMARY.json` is the original summary bytes.
Both remote scientific outputs and the local published archive remain retained.

Next: execute the card's one BANK fit with identical source, train/evaluation
seeds and5000/4969/128 exposure, using the exact collected Generic summary only
for publication. `EXECUTION.json` binds the native argv and summary SHA256.
Confirm the deterministic BANK handle is unused, pre-create its new output
directory and let the committed launcher perform fresh adjacent4GiB admission.
Reuse the same B03 recovery Monitor and require its direct actual adoption.
No pair polarity, scientific retry, new block or direction disposition follows
from Generic alone. This is a technical continuation of the already selected
B03 and applied Portfolio CONTINUE, not a new scientific allocation.
