"""Exact arithmetic for the temporary temporal-alignment identification question.

One eligible decision, fixed predecision population, KEEP value subtracted from
both choices. These identities are not estimators of a full UAV episode effect.
No simulator, random sampling, learned parameter or scientific-run entry exists.
"""
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class GateCell:
    retained: int
    new_observation: int
    probability: Fraction
    end_probability: Fraction
    advantage: Fraction


def _rational(value):
    if not isinstance(value, (int, Fraction)) or isinstance(value, bool):
        raise TypeError("use exact integer or Fraction inputs, not floating-point probabilities")
    return Fraction(value)


def decision_values(cells):
    """Expected net returns for online, independent and retained-only gates.

    The retained-only gate uses E[p(END | C,S) | C] under this fixed population.
    It is an ideal conditional intervention, not a fitted native comparator.
    """
    cells = tuple(GateCell(c.retained, c.new_observation, _rational(c.probability),
                           _rational(c.end_probability), _rational(c.advantage)) for c in cells)
    if not cells or sum(c.probability for c in cells) != 1:
        raise ValueError("cell probabilities must sum exactly to one")
    if any(c.probability <= 0 or not 0 <= c.end_probability <= 1 for c in cells):
        raise ValueError("cell masses must be positive and gate probabilities lie in [0,1]")
    mass, end_mass = {}, {}
    for cell in cells:
        key = cell.retained
        mass[key] = mass.get(key, Fraction(0)) + cell.probability
        end_mass[key] = end_mass.get(key, Fraction(0)) + cell.probability * cell.end_probability
    conditional_rate = {key: end_mass[key] / mass[key] for key in mass}
    end_rate = sum(c.probability * c.end_probability for c in cells)
    online = sum(c.probability * c.end_probability * c.advantage for c in cells)
    independent = sum(c.probability * end_rate * c.advantage for c in cells)
    retained = sum(c.probability * conditional_rate[c.retained] * c.advantage for c in cells)
    return dict(end_rate=end_rate, online=online, independent_calendar=independent,
                retained_only=retained, total_gap=online - independent,
                new_observation_component=online - retained,
                retained_component=retained - independent)


def canonical_examples():
    """Four equally likely C,S cells; all four examples have END rate 1/2."""
    examples = {name: [] for name in ("new_observation", "previous_command", "mixed", "cancellation")}
    for c in (-1, 1):
        for s in (-1, 1):
            specs = {
                "new_observation": (Fraction(s + 1, 2), Fraction(s)),
                "previous_command": (Fraction(c + 1, 2), Fraction(c)),
                "mixed": (Fraction(1, 2) + Fraction(c + s, 4), Fraction(c + s)),
                "cancellation": (Fraction(1, 2) + Fraction(c + s, 4), Fraction(s - c)),
            }
            for name, (p, advantage) in specs.items():
                examples[name].append(GateCell(c, s, Fraction(1, 4), p, advantage))
    return {name: tuple(cells) for name, cells in examples.items()}


def ar1_delayed_reward_gradient(rho):
    """At mu=(0,0), terminal reward a0 has true mean gradient (1,0).

    Cov(a0,a1) = rho and each variance is one. A joint Gaussian score uses
    covariance^{-1}(a-mu); independent marginal scores incorrectly use a-mu.
    With reward a0, their exact expectations require only second moments.
    """
    rho = _rational(rho)
    if abs(rho) >= 1:
        raise ValueError("rho must lie strictly between -1 and 1")
    denominator = 1 - rho * rho
    covariance_row = (Fraction(1), rho)
    precision_rows = ((Fraction(1), -rho), (-rho, Fraction(1)))
    correct = tuple(sum(coefficient * moment for coefficient, moment
                        in zip(row, covariance_row)) / denominator for row in precision_rows)
    return dict(correct=correct, independent_marginal=covariance_row)
