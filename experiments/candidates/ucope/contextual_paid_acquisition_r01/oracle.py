"""Exact rational BELIEF oracle and frozen action-flip certificate."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import comb
from typing import Iterable

from .contract import K_TEST, K_TRAIN, LINKAGES, RELIABILITIES, TOTAL_COSTS, contexts, context_id


def tail_q(regime: str, period: int) -> Fraction:
    if regime not in ("SHORT", "LONG"):
        raise ValueError("regime must be SHORT or LONG")
    if type(period) is not int or not 1 <= period <= 9:
        raise ValueError("period must be an integer in 1..9")
    center = 2 if regime == "SHORT" else 8
    return Fraction(95, 100) - Fraction((period - center) ** 2, 100)


def tail_time(period: int) -> Fraction:
    if type(period) is not int or not 1 <= period <= 9:
        raise ValueError("period must be an integer in 1..9")
    return -Fraction(period, 100)


def tail_energy(period: int) -> Fraction:
    if type(period) is not int or not 1 <= period <= 9:
        raise ValueError("period must be an integer in 1..9")
    return -Fraction(period * period, 1000)


def tail_return(regime: str, period: int) -> Fraction:
    return tail_q(regime, period) + tail_time(period) + tail_energy(period)


def joint_count_probability(regime: str, reliability: Fraction, short_count: int) -> Fraction:
    if regime not in ("SHORT", "LONG"):
        raise ValueError("regime must be SHORT or LONG")
    if reliability not in RELIABILITIES:
        raise ValueError("reliability outside frozen population")
    if type(short_count) is not int or not 0 <= short_count <= 6:
        raise ValueError("short count outside 0..6")
    short_probability = reliability if regime == "SHORT" else 1 - reliability
    return Fraction(1, 2) * comb(6, short_count) * short_probability**short_count * (1 - short_probability) ** (6 - short_count)


def posterior_short(reliability: Fraction, short_count: int) -> Fraction:
    short_joint = joint_count_probability("SHORT", reliability, short_count)
    long_joint = joint_count_probability("LONG", reliability, short_count)
    return short_joint / (short_joint + long_joint)


def expected_tail_value(period: int, belief_short: Fraction) -> Fraction:
    return belief_short * tail_return("SHORT", period) + (1 - belief_short) * tail_return("LONG", period)


def optimal_tail(periods: Iterable[int], belief_short: Fraction) -> tuple[int, Fraction]:
    candidates = [(expected_tail_value(period, belief_short), -period, period) for period in periods]
    value, _, period = max(candidates)
    return period, value


def baseline(periods: Iterable[int]) -> tuple[int, Fraction]:
    return optimal_tail(periods, Fraction(1, 2))


def informed_value(reliability: Fraction, periods: Iterable[int]) -> Fraction:
    value = Fraction(0)
    for count in range(7):
        short_joint = joint_count_probability("SHORT", reliability, count)
        long_joint = joint_count_probability("LONG", reliability, count)
        mass = short_joint + long_joint
        _, conditional_value = optimal_tail(periods, short_joint / mass)
        value += mass * conditional_value
    return value


def information_gain(reliability: Fraction, periods: Iterable[int]) -> Fraction:
    return informed_value(reliability, periods) - baseline(periods)[1]


def direct_probe_value(total_cost: Fraction) -> Fraction:
    if total_cost not in TOTAL_COSTS:
        raise ValueError("cost outside frozen population")
    return Fraction(1, 25) - total_cost


def gamma(link: str, reliability: Fraction, total_cost: Fraction, periods: Iterable[int]) -> Fraction:
    if link not in LINKAGES:
        raise ValueError("link outside frozen population")
    information = information_gain(reliability, periods) if link == "LINKED" else Fraction(0)
    return information + direct_probe_value(total_cost)


@dataclass(frozen=True)
class FlipCell:
    context_id: str
    B_train: Fraction
    B_test: Fraction
    A0_train: Fraction
    A0_test: Fraction
    A_train: Fraction
    A_test: Fraction
    I_train: Fraction
    I_test: Fraction
    D: Fraction
    train_gamma: Fraction
    test_gamma: Fraction
    train_action: str
    test_action: str
    train_root_values: dict[str, Fraction]
    test_root_values: dict[str, Fraction]
    train_tail_values: dict[str, dict[str, Fraction]]
    test_tail_values: dict[str, dict[str, Fraction]]
    train_tail_optima: dict[str, int]
    test_tail_optima: dict[str, int]


@dataclass(frozen=True)
class FlipCertificate:
    baseline_train_period: int
    baseline_train_value: Fraction
    baseline_test_period: int
    baseline_test_value: Fraction
    information: dict[str, dict[str, Fraction]]
    cells: tuple[FlipCell, ...]

    def validate(self) -> "FlipCertificate":
        if (self.baseline_train_period, self.baseline_train_value) != (5, Fraction(785, 1000)):
            raise ValueError("train baseline drift")
        if (self.baseline_test_period, self.baseline_test_value) != (4, Fraction(794, 1000)):
            raise ValueError("held-out baseline drift")
        expected = {
            Fraction(13, 20): (Fraction(57309249, 1600000000), Fraction(23936761, 800000000)),
            Fraction(17, 20): (Fraction(26928171, 320000000), Fraction(57149681, 800000000)),
        }
        for reliability, (train_expected, test_expected) in expected.items():
            key = str(reliability)
            if self.information[key]["train"] != train_expected or self.information[key]["test"] != test_expected:
                raise ValueError("information-gain drift")
        expected_cell_ids = {context_id(context) for context in contexts()}
        if {cell.context_id for cell in self.cells} != expected_cell_ids or len(self.cells) != 8:
            raise ValueError("flip certificate population drift")
        for cell in self.cells:
            if cell.B_train != self.baseline_train_value or cell.B_test != self.baseline_test_value:
                raise ValueError("cell baseline decomposition drift")
            if cell.A0_train - cell.B_train != cell.D or cell.A0_test - cell.B_test != cell.D:
                raise ValueError("D=A0-B decomposition drift")
            if cell.A_train - cell.A0_train != cell.I_train or cell.A_test - cell.A0_test != cell.I_test:
                raise ValueError("A=A0+I decomposition drift")
            if cell.train_gamma != cell.I_train + cell.D or cell.test_gamma != cell.I_test + cell.D:
                raise ValueError("Gamma=I+D decomposition drift")
            if cell.D >= 0:
                raise ValueError("direct probe component must be negative")
            for periods, values, optima in (
                (K_TRAIN, cell.train_tail_values, cell.train_tail_optima),
                (K_TEST, cell.test_tail_values, cell.test_tail_optima),
            ):
                if set(values) != {str(count) for count in range(7)} or set(optima) != set(values):
                    raise ValueError("tail count-vector inventory drift")
                for count in range(7):
                    vector = values[str(count)]
                    if set(vector) != {str(period) for period in periods}:
                        raise ValueError("tail action-vector inventory drift")
                    ranked = sorted((value, -int(period), int(period)) for period, value in vector.items())
                    if len(ranked) < 2 or ranked[-1][0] == ranked[-2][0] or optima[str(count)] != ranked[-1][2]:
                        raise ValueError("tail optimum is absent or nonunique")
            for periods, root_values, action in (
                (K_TRAIN, cell.train_root_values, cell.train_action),
                (K_TEST, cell.test_root_values, cell.test_action),
            ):
                if set(root_values) != {"PROBE", *(f"IMMEDIATE:{period}" for period in periods)}:
                    raise ValueError("root action-vector inventory drift")
                ranked = sorted((value, label) for label, value in root_values.items())
                if ranked[-1][0] == ranked[-2][0]:
                    raise ValueError("root optimum must be unique")
                expected_action = "PROBE" if ranked[-1][1] == "PROBE" else "IMMEDIATE"
                if action != expected_action:
                    raise ValueError("root action/value mismatch")
            if cell.context_id.startswith("SEVERED-"):
                if cell.I_train != 0 or cell.I_test != 0:
                    raise ValueError("SEVERED information must be exactly zero")
                if set(cell.train_tail_optima.values()) != {5} or set(cell.test_tail_optima.values()) != {4}:
                    raise ValueError("SEVERED tail policy must equal the immediate optimum")
        positives_train = [cell.context_id for cell in self.cells if cell.train_gamma > 0]
        positives_test = [cell.context_id for cell in self.cells if cell.test_gamma > 0]
        target = "LINKED-p17_20-c9_100"
        if positives_train != [target] or positives_test != [target]:
            raise ValueError("the exact unique action flip is absent")
        if any(direct_probe_value(cost) >= 0 for cost in TOTAL_COSTS):
            raise ValueError("direct probe value must be strictly negative")
        if any(cell.train_gamma == 0 or cell.test_gamma == 0 for cell in self.cells):
            raise ValueError("oracle action must be unique in every cell")
        heldout = [optimal_tail(K_TEST, posterior_short(Fraction(17, 20), n))[0] for n in range(7)]
        if heldout != [6, 6, 6, 4, 2, 2, 2]:
            raise ValueError("held-out count policy drift")
        return self


def construct_flip_certificate() -> FlipCertificate:
    train_period, train_base = baseline(K_TRAIN)
    test_period, test_base = baseline(K_TEST)
    information = {
        str(p): {"train": information_gain(p, K_TRAIN), "test": information_gain(p, K_TEST)}
        for p in RELIABILITIES
    }
    cells = []
    for context in contexts():
        p = context["reliability"]
        cost = context["total_cost"]
        train_gamma = gamma(context["link"], p, cost, K_TRAIN)
        test_gamma = gamma(context["link"], p, cost, K_TEST)
        link_information_train = information_gain(p, K_TRAIN) if context["link"] == "LINKED" else Fraction(0)
        link_information_test = information_gain(p, K_TEST) if context["link"] == "LINKED" else Fraction(0)
        D = direct_probe_value(cost)

        def tail_vectors(periods):
            vectors = {}
            optima = {}
            for count in range(7):
                belief = posterior_short(p, count) if context["link"] == "LINKED" else Fraction(1, 2)
                vector = {str(period): expected_tail_value(period, belief) for period in periods}
                vectors[str(count)] = vector
                optima[str(count)] = max((value, -period, period) for period, value in ((k, vector[str(k)]) for k in periods))[2]
            return vectors, optima

        train_tail_values, train_tail_optima = tail_vectors(K_TRAIN)
        test_tail_values, test_tail_optima = tail_vectors(K_TEST)
        train_root_values = {f"IMMEDIATE:{k}": expected_tail_value(k, Fraction(1, 2)) for k in K_TRAIN}
        test_root_values = {f"IMMEDIATE:{k}": expected_tail_value(k, Fraction(1, 2)) for k in K_TEST}
        train_root_values["PROBE"] = train_base + link_information_train + D
        test_root_values["PROBE"] = test_base + link_information_test + D
        cells.append(
            FlipCell(
                context_id(context),
                train_base,
                test_base,
                train_base + D,
                test_base + D,
                train_base + D + link_information_train,
                test_base + D + link_information_test,
                link_information_train,
                link_information_test,
                D,
                train_gamma,
                test_gamma,
                "PROBE" if train_gamma > 0 else "IMMEDIATE",
                "PROBE" if test_gamma > 0 else "IMMEDIATE",
                train_root_values,
                test_root_values,
                train_tail_values,
                test_tail_values,
                train_tail_optima,
                test_tail_optima,
            )
        )
    return FlipCertificate(train_period, train_base, test_period, test_base, information, tuple(cells)).validate()


build_flip_certificate = construct_flip_certificate
