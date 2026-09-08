# VSP03 B04 technical source acceptance

Started clean at aaf36703f in the existing shared VSP03 checkout/branch. Applicable
AGENTS and compute configuration are unchanged since B03 collection. This record
covers the minimal B04 source and new payload boundary; science remains DM-owned.

Scope before writing: B04 card section6 requests none of scope-spec section4's
optional machinery. Added none. The shared run function gains one optional object_name
argument defaulting to VSP03_B03, used only in the summary object label. The new28-line
runner fixes seed6 and passes VSP03_B04; the old runner remains seed5 and unchanged.
No learner copy, B01/B02 edit, scientific loop change, RNG relabelling or extra mode.
One G still uses arm1; seed6 therefore supplies Torch40006 and the inherited addresses.

Focused static tests: scientific Python -B -m pytest -q -p no:cacheprovider
--basetemp temp/directions/vsp_03/test/b04_binding_20260908
 tests/experiments/candidates/vsp_03/vsp03_b04/:2 passed in0.11s.
They import no scientific module and check B03/default and B04/seed/object/arm binding.
No scratch was generated (the named basetemp does not exist). Prior scientific/output
review and checks are reused; no old fixture, model construction or trajectory smoke.
The exact new launch block passed remote bash -n through stdin (exit0).

The [launch boundary](VSP03_B04_LAUNCH_BOUNDARY_20260908.md) encloses the payload in
a subshell returning its status to the unmodified supervisor. It removes top-level
exec of /usr/bin/time; the inner exec remains confined to the timed child shell.
A cwd error likewise exits the subshell, allowing supervisor exit publication.

One harmless exit7 check copied the actual existing generated B03 wrapper into a
unique remote temp test directory, changed its file destinations to that directory
and replaced only its eval payload with the new subshell containing timed literal
exit7. The real inherited status/exit/footer postamble executed: numeric exit7,
status failed, footer code7. Wrapper process itself returned0 after its idle sleep,
which demonstrates why its process return must not replace the command's exit receipt.
The old B03 label remains literal inside the copied fixture log; no B03 evidence or
live supervisor path was touched. [Raw wrapper/log/exit evidence](VSP03_B04_EXIT_CHECK_20260908.json)
retains the exact check. Complete receipt span0.353791744s; scientific models/episodes/
steps0/0/0. The created remote temp directory was resolved to its exact owned absolute
path and removed in finally; scratch_removed=true. Old rejected B03 scratch was untouched.

Complete elapsed will use the existing supervisor start_time through latest required
exit/status/log publication mtime, conservatively including timestamp rounding and
startup. The narrower payload timer is separately reported. A missing numeric exit
or complete span above120s limits the corresponding acceptance; no retry or cap
expansion follows. No lower-level timer alone proves complete conformance.

Independent affected-path review, final source commit, DM source intake and Root
integration precede the sole scientific invocation. No B04 scientific run yet.

## Independent review boundary finding

The reused reviewer found one P2 issue in the proposed launch boundary: child timeout
starts after supervisor start and excludes the supervisor postamble. Receipt-span
measurement detects complete120s nonconformance but cannot enforce that hard stop
on the timeout path. CM confirmed there is no omitted existing supervisor-level
deadline and returned the concrete card section5 conflict to DM. Seed/object/status
propagation conforms; no other material finding. No watchdog, manual receipt-writing,
recursive wrapper or supervisor modification was introduced. Source acceptance of
the launch boundary remains pending this named contract resolution; no science run.
See [independent review](VSP03_B04_SOURCE_REVIEW_20260908.md).
