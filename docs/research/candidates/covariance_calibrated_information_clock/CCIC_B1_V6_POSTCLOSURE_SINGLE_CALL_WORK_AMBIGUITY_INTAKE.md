# CCIC B1 revision-06 post-closure single-call/work ambiguity intake

```text
direction=covariance_calibrated_information_clock
affected_revision=CCIC-B1-SCIENCE-20260813-06
source=same-direction CM static technical acceptance
scientific_activity_started=false
question_relevant_data_produced=false
em_disposition=exact_v6_ends_preactivity_definition_inconsistent
successor_revision=CCIC-B1-SCIENCE-20260813-07
provider_action=none_yet
cm_activity=static_only
production_authorization=none
```

## Conclusion

Exact revision 06 cannot enter scientific activity despite its valid
mathematical-closure history. Static construction exposed a conflict among
three frozen requirements: one fusion call per agent per decision, distinct
observed-batch and zero-valued-next-template evaluations for `RI-STRONG-v2`
and `INFO-FLEX`, and a work formula that counts only one row/head evaluation.
Because RI-v2's second output can depend on represented value `z`, its
observed-batch `J` is not generally its zero-template `J`; INFO-FLEX has the
same two-context problem. Two network evaluations violate the work/exposure
object, while reusing the observed value violates the future-information
template and permits value leakage. Calling two evaluations one nominal call
does not resolve the causal or work mismatch.

This is a prospective definition fact found before any learned update,
stochastic evaluation, endpoint, or efficacy result. It is not evidence for
or against CCIC, RI, the variable axes, or task value. The EM ends exact v6
and freezes complete successor revision 07. V7 changes only the functional
factorization needed to return observed evidence update and prospective
information in one actual fusion call. It preserves the DGP, CCIC treatment,
actor, variable `N/k` axes, tapes, seeds, endpoints, inference, thresholds,
work tolerance, strongest-alternative class, claim ceiling, second-surface
trigger, and activity boundary.

## Alternatives adjudicated

1. **Reuse observed-batch `J`: rejected.** RI-v2 and INFO-FLEX could encode
   represented value into the actor's purported expected-next-information
   channel. That defeats the zero-valued-template boundary and leaves a value
   shortcut.
2. **Evaluate the same network twice: rejected.** This doubles
   output-relevant learned work for the affected arms and invalidates the
   frozen one-call exposure and RI work formulas.
3. **Batch two contexts and call them once: rejected.** Nominal API call count
   does not erase the second functional network evaluation or its work.
4. **Relax the work gate or add CCIC padding: rejected.** Either leaves the
   useful-compute alternative or introduces inert work.
5. **Causally factor the outputs inside one call: accepted.** Evidence update
   may depend on actual `z`; prospective information is computed from the
   public zero-valued next-SENSE metadata and cannot depend on realized `z`.
   Both are returned by one declared fusion invocation with literal functional
   work accounting.

## Revision-07 RI comparator

`RI-STRONG-v3` remains a flexible replication-safe set comparator with 83
trainable scalars. One logical fusion call receives the actual newly
assimilable unique-origin batch and the public metadata-only template for one
additional `SENSE` block. The template carries public regime, expected unique
lineage pattern, overlap, quality, roster-derived `M`, current physical time,
and `k`; it contains no realized future value.

For each unique template row define

```text
x_i = (z_i,o_i,s_i,log M,t/30,k/5)       # actual row, only when new evidence exists
m_i = (o_i,s_i,log M,t/30,k/5)           # public next-SENSE metadata
e_i = SiLU(W_e x_i+b_e),       W_e: 6 -> 5
c_i = SiLU(W_c m_i+b_c),       W_c: 5 -> 5
r_ell_i = w_ell^[T] [e_i;c_i]+b_ell+gamma_z*z_i
r_J_i = w_J^[T] c_i+b_J
h_ell_i = r_ell_i+tanh(r_ell_i)
h_J_i = r_J_i+tanh(r_J_i)
g_ell = mean_i h_ell_i
g_J = mean_i h_J_i
Delta ell_hat = 8*sinh(g_ell)
J_next_hat = 1e-4+softplus(g_J)
```

The two row sets have identical public `(o,s,M,t,k)` metadata whenever the
current actual batch contains new Stage-1 `SENSE` evidence. They are aligned
in ascending unique-row order, so `c_i` is evaluated exactly once and serves
both outputs. When the current table contains no new evidence (initial,
`RELAY`, null, or already-assimilated copy), the observed increment is exactly
zero and only the template metadata branch is evaluated. At terminal states
where another `SENSE` is illegal, `J_next_hat=0` and it cannot affect the
commit-only support. A mismatch in the declared alignment, cardinality, or
metadata fails closed.

The parameter count is exactly:

```text
evidence hidden 6 -> 5:  6*5+5 = 35
metadata hidden 5 -> 5:  5*5+5 = 30
Delta-ell head on width 10: 10+1 = 11
direct gamma_z skip:                 1
J head on width 5:             5+1 = 6
total:                              83
```

The evidence output can use all value/count/time/metadata interactions and a
direct learned value skip. The prospective `J` output is flexible in all
public next-batch metadata but structurally cannot see actual or future `z`.
Lineage quotienting occurs first; literal copies cannot alter either unique
set, while a distinct equal-valued origin changes `M` and the unique set.

Training uses the same 9,216 snapshots, 1,500 updates, optimizer, initialization
family, targets, decodes, and no search. The `Delta ell` loss targets
`asinh(Delta ell/8)` from the observed batch; the `J` loss targets the same
normalized exact prospective GLS information from the public template. Both
branches and the direct skip are trained and used at execution.

## Exact RI-v3 work identity

Under the unchanged expanded scalar grammar, the full fresh-SENSE path costs
per unique row:

```text
6 -> 5 linear                       125
width-five SiLU                      25
5 -> 5 metadata linear              105
width-five SiLU                      25
Delta-ell width-ten linear head      41
gamma_z*z_i direct multiply/add       2
J width-five linear head             21
two r+tanh(r) transforms               8
per-row subtotal                    352
two-channel mean pool             4M+2
two decodes                           10
```

Therefore the prior numeric work object is preserved exactly, with only the
comparator name changed:

```text
C(N,M) = 14N+M-5
W_CCIC(N,M) = 14N+392M+8
W_RI_v3(N,M) = 14N+357M+7
P_CCIC(M) = 22+6M
P_RI_v3(M) = 24+6M.
```

The maximum operation ratio remains `1.094793` and the maximum peak ratio
remains `30/28=1.071429`. The preactivity certificate must execute and
instrument this exact single-call fresh-SENSE path, materialize all 27 cells,
match every replay tuple to the literal formulas, and require aggregate
`passed=true`. A second row-network evaluation, ignored output, dummy work,
counter-only increment, metadata/cardinality mismatch, or nonstreaming peak
fails before activity.

## Revision-07 INFO-FLEX call

`INFO-FLEX-v2` retains exactly 79 additional trainable scalars but replaces its
shared two-context head with two causally separated branches inside one fusion
call:

```text
g_ell = MLP_4->8->1(ell_minus,q_hat,J_hat,k/5)
ell_posterior_hat = 8*sinh(g_ell)

g_J = MLP_2->7->1(J_hat_template,k/5) + gamma_J*J_hat_template
J_next_hat = 1e-4+softplus(g_J)
```

The observed-posterior branch has `4*8+8+8+1=49` parameters. The prospective
information branch has `2*7+7+7+1=29`, and `gamma_J` adds one, totaling 79.
`J_hat_template` comes from the frozen CCIC metadata-only covariance estimator
on the public zero-valued next-SENSE template. The prospective branch cannot
see `q_hat`, the observed posterior, or any realized `z`; the actor separately
receives belief. Both branches train on the same snapshots and unchanged
posterior/information targets and execute once inside one fusion invocation.
INFO-FLEX-v2 remains an intentionally capacity-advantaged diagnostic, not a
primary work-matched arm.

## Authority and evidence boundary

Revision 06 retains its historical Pro closure but is no longer eligible for
activity because its one-call and work/exposure definitions cannot be jointly
implemented. Revision 07 is a new science-bearing composite and requires
literal `CLOSED` in the existing dedicated Pro conversation plus this EM's
intake before CM static acceptance can resume.

This intake authorizes no provider send before Root publication, no CM tests,
training, evaluation, scientific compute, production, Gemini turn, second
surface, or UAV claim.
