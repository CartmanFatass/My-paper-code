"""Frozen-table adapter and exact publication calculations for the R03 upper."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from hashlib import sha512
from math import lcm
import json

from experiments.candidates.acvc.history_upper_prefix_assessment_r03.arithmetic import structural_counts

DUAL = (F(38, 235), F(0))
BUDGETS = (F(12557, 375000), F(26677, 75000))
REFERENCES = {"J_D": F(2088, 625), "J_L": F(18916861, 5625000), "J_U_R02": F(13365083, 3671875)}
PRIOR = (F(1, 2), F(1, 2))
CELLS = tuple(f"{r}|b={b}|q={q}|d={d}" for r in ("CALIBRATED", "UNINFORMATIVE")
              for b in range(2) for q in ("7/10", "9/10") for d in range(3))


def fraction(field):
    return F(field["numerator"], field["denominator"])


def profile(inputs):
    atoms, contexts, scores, dual, budgets = inputs
    families = {"atoms": [x for row in atoms for x in row],
                "marginals": [x for row in contexts for x in row],
                "scores": [x for row in scores for cell in row for x in cell],
                "multipliers": list(dual), "budgets": list(budgets), "priors": list(PRIOR)}
    ranges = {}
    denominator = 1
    for name, values in families.items():
        numerators = [abs(x.numerator).bit_length() for x in values]
        denominators = [x.denominator.bit_length() for x in values]
        ranges[name] = {"count": len(values), "numerator_bits": [min(numerators), max(numerators)],
                        "denominator_bits": [min(denominators), max(denominators)]}
        for value in values:
            denominator = lcm(denominator, value.denominator)
    return {"families": ranges, "fraction_count": sum(len(v) for v in families.values()),
            "D_star": denominator, "D_star_bits": denominator.bit_length(),
            "within_actual_range": denominator.bit_length() <= 512 and all(
                max(row["numerator_bits"] + row["denominator_bits"]) <= 64 for row in ranges.values())}


def load_inputs(path, check=lambda: None):
    check()
    source = json.loads(path.read_text(encoding="utf-8"))
    envelope = source["REGIME-ORACLE-ENVELOPE"]
    table = envelope["coefficient_table"]
    by_cell = {row["cell"]: row for row in table}
    atoms, contexts, scores = [], [], []
    native_match = True
    probability_match = True
    for regime in range(2):
        atom_row, context_row, score_row = [], [], []
        for key in CELLS[12*regime:12*(regime+1)]:
            cell = by_cell[key]
            w, p = fraction(cell["weight"]), fraction(cell["unsafe_probability"])
            probability_match &= w > 0 and 0 <= p <= 1
            context_row.append(2*w)
            atom_row.extend((2*w*(1-p), 2*w*p))
            action_row = []
            expected = (("EXECUTE", 1-5*p, p, F(0)),
                        ("PROBE", F(2, 5)-p, F(0), F(3, 5)*(1-p)),
                        ("VETO", F(0), F(0), 1-p))
            native_match &= len(cell["actions"]) == 3
            for action, (name, gain, unsafe, loss) in zip(cell["actions"], expected):
                values = tuple(fraction(action[field]) for field in
                               ("gain", "unsafe_numerator", "clean_loss_numerator"))
                native_match &= action["action"] == name and values == (gain, unsafe, loss)
                action_row.append(values[0] - DUAL[0]*values[1] - DUAL[1]*values[2])
            score_row.append(tuple(action_row))
            check()
        atoms.append(tuple(atom_row)); contexts.append(tuple(context_row)); scores.append(tuple(score_row))
    inputs = (tuple(atoms), tuple(contexts), tuple(scores), DUAL, BUDGETS)
    facts = {"cell_mapping": [{"source_index": next(i for i, row in enumerate(table) if row["cell"] == key),
                               "cell": key, "atom_order": [0, 1]} for key in CELLS],
             "dimensions_match": len(table) == len(by_cell) == 24,
             "native_coefficients_match": native_match, "probabilities_valid": probability_match,
             "normalized": all(sum(row) == 1 for row in atoms + contexts),
             "dual_match": tuple(fraction(envelope["dual"][k]) for k in
                                  ("unsafe_multiplier", "clean_loss_multiplier")) == DUAL,
             "budgets_match": tuple(fraction(envelope["primal"][k]) for k in
                                     ("unsafe_cap", "clean_loss_cap")) == BUDGETS,
             "references_match": all(fraction(source["primary"][old]) == REFERENCES[new]
                                     for old, new in (("J_D", "J_D"), ("J_L", "J_L"), ("J_U", "J_U_R02")))}
    facts["source_facts_match"] = all(value for value in facts.values() if isinstance(value, bool))
    facts["profile"] = profile(inputs)
    check()
    return inputs, facts


def synthetic_inputs(denominator, contexts=12, check=lambda: None):
    def integer(label):
        return int.from_bytes(sha512(f"synthetic-prefix-actual-profile-r03/{label}".encode("utf-8")).digest(), "big")
    def positive(label):
        return F(1 + integer(label) % (denominator-1), denominator)
    k = 2 * contexts
    b = denominator // k
    radius = b // (8*k)
    atoms, marginals, scores = [], [], []
    check()
    for regime in range(2):
        numerators = [b + integer(f"atom/{regime}/{j}") % (2*radius+1) - radius for j in range(k-1)]
        numerators.append(denominator - sum(numerators))
        row = tuple(F(n, denominator) for n in numerators)
        atoms.append(row)
        marginals.append(tuple(row[2*c] + row[2*c+1] for c in range(contexts)))
        score_row = []
        for c in range(contexts):
            score_row.append(tuple((1 if integer(f"score/{regime}/{c}/{a}/sign") % 2 == 0 else -1)
                                   * positive(f"score/{regime}/{c}/{a}") for a in range(3)))
            check()
        scores.append(tuple(score_row))
    return (tuple(atoms), tuple(marginals), tuple(scores),
            tuple(positive(f"multiplier/{i}") for i in range(2)),
            tuple(positive(f"budget/{i}") for i in range(2)))


def branch(bound, references=REFERENCES):
    if not references["J_D"] <= references["J_L"] <= bound <= references["J_U_R02"]:
        return "INTEGRITY_DISCREPANCY"
    return "HC-C / MATERIAL_COMPATIBLE_HEADROOM_CERTIFIED_IMPOSSIBLE" if bound-references["J_D"] < F(1, 4) else "HC-D / CERTIFICATE_INTERVAL_UNRESOLVED"


def result_payload(bound, inputs, facts, *, synthetic=False, contexts=12, prefix=4):
    dual, budgets = inputs[3:]
    references = {key: F(0) for key in REFERENCES} if synthetic else REFERENCES
    return {"complete": True, "synthetic": synthetic,
            "primary": {"B4": bound, "Delta4": bound-references["J_D"],
                        "tightening": references["J_U_R02"]-bound, **references},
            "fixed_dual": dual, "numerator_budgets": budgets, "input_facts": facts,
            "inequalities": {} if synthetic else {"J_D_le_J_L": REFERENCES["J_D"] <= REFERENCES["J_L"],
                "J_L_le_B4": REFERENCES["J_L"] <= bound, "B4_le_old_upper": bound <= REFERENCES["J_U_R02"]},
            "branch": "SYNTHETIC_SERIALIZATION_ONLY" if synthetic else branch(bound),
            "claim_ceiling": "A/RECON finite-host compatible legal-history upper; no learner evidence",
            "information_relaxation": "Past complete atoms for opportunities 1-4; current frame only; regime revealed at 5-12. Certificate only.",
            "static_counts": structural_counts(2*contexts, contexts, 3, prefix),
            "learner_exposure": {"trainable_parameters": 0, "gradient_updates": 0, "training_episodes": 0,
                                 "optimizer_transitions": 0, "checkpoints": 0, "selection_exposure": 0}}


def encode_fraction(value):
    with localcontext() as context:
        context.prec = 30
        return {"numerator": value.numerator, "denominator": value.denominator,
                "decimal": str(Decimal(value.numerator) / Decimal(value.denominator))}


def serialize(payload):
    return json.dumps(payload, default=encode_fraction, indent=2) + "\n"
