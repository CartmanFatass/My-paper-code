# Independent technical review — 2026-09-11

Reviewer: retained `review_b02_credit`, Astra/high, read-only. The DM owned all edits.
The reviewed production diff is preserved only in `repair_candidate.patch`; it was
restored out of production before closeout. No review invoked scientific work.

The initial review examined the concrete integer-ratio replacement for
`models.py::exact_binary64_mean`, `_ExactRosterMean` forward/backward, the NumPy-model
consumer, existing pooling test and repair L0/core/primitive/ABI/allocator receipts.
It found no material numerical or source-correctness defect. Finite binary64 denominators
are powers of two, so the maximum denominator is a common denominator. Integer accumulation
preserves exact cancellation and presentation-order independence; final integer division
retains the original rational-to-binary64 rounding. Validation, output dtype, empty-column
behavior and backward `gradient / n` are unchanged. Both arms use the same helper.
No RNG, checkpoint, optimizer, exposure or Engineering Scope §4 change was proposed.

Its material limit: the core and allocator failure identify the detection site, not
the corrupting writer. Primitive passes and ABI size agreement do not prove restored
readiness. The traced bridge produced no completed result. The diff is a defensible
semantics-preserving candidate workaround, not evidence that exit139 is fixed.

The further saved-evidence review examined `repair_allocator_core.json` and the
existing source path. It narrowed detection to a 32-byte CPython API-m block freed
by `_PyObject_Call_Prepend`, through `slot_tp_new`, `type_call` and Fraction division.
The trailing eight bytes contain a pointer-sized value instead of padding. A 64-element
float64 output would occupy 512 bytes, and this current mean's `np.array`, subsequent
`torch.from_numpy` and outer `torch.stack` have not run at the stopped frame. Earlier
bridge operations remain possible contributors. No compiled/native writer is attributable.

The smallest remaining gap is the exact allocation ownership and argument-write extent
in the bound CPython executable, including constructor/vectorcall callees. Required
allocation operands, writing instruction and first-change history are absent. The DM
accepts this limit and does not adopt the candidate. This is no request for a scientific
rerun and no scientific dissent against temporal credit.

Review cost: first review 5 read-only command calls, summed command wall3.6420961s;
approximately4.8s enclosing tool wall is an alternative. Further review 3 read-only
command calls, summed command wall1.0504297s; approximately1.8s enclosing tool wall is
an alternative. No edits, tests, models, native execution or scientific invocation
were performed by the reviewer. Root-reported rejected dynamic method requests are
separate tool events in `repair_tool_events.json`.

## Portfolio-conditioned candidate review

The exact-build static mapping was subsequently published in
`repair_exact_interpreter_static.json`, commit06fc94e6268072a3be02abc78738d32813b950f0.
The binary computes40 bytes for the declared call and already includes its reserved
pointer. The saved tail resolves to `_Py_FalseStruct`, expected at offset32. The saved
32-byte debug header remains inconsistent; allocation-time state and metadata origin
remain unobserved. This does not establish a missing-slot bug in the inspected binary.

The reviewer then inspected the concrete replacement, two-test draft and Portfolio
response6c32ade3216c374ecf2f5179b15d559729cd45c9 §6. No numerical or gradient defect
was found. The tests meaningfully cover exact output/rounding/order, input ownership
and removal of the helper's former Fraction path through custom autograd. They do
not establish independence from prior corruption. Prior successful checks of the old
primitive/bridge also coexist with the allocator failure. This is one material
readiness-claim finding; it is not a scientific objection to temporal credit.

DM disposition: accept the finding. Preserve the replacement and regression only as
`repair_fraction_path_candidate.patch`, with no production adoption or test execution.
No full-runtime repair, remote staging acceptance or scientific launch is implied.

Additional review costs: exact-static seven-command review4.9540463s (approximately6.7s
enclosing alternative); artifact publication6.3729295s, including its0.6437807s capture;
subsequent diff/test/Portfolio read-only review0.6660973s. The latter two sum7.0390268s.
These are additional to the earlier review account, with nested clocks excluded.
No diagnostic fixture, debugger, test or scientific code was executed by the reviewer.
