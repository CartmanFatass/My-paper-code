"""Closed TEST-only contracts for the r05 enabling measurement."""

from __future__ import annotations

from typing import Final

TEST_NAMESPACE: Final[str] = "TEST/VQFP-FERL-R05/NUMERIC-ANALYTIC-CERTIFICATE-MEASUREMENT/V1"
TEST_SCHEMA: Final[int] = 0x56514635
NATIVE_ABI_VERSION: Final[int] = 1
Q_E: Final[int] = 52_776_558_133_248
ANALYTIC_STATE_COUNT: Final[int] = 4_096
REGISTERED_N: Final[tuple[int, ...]] = (4, 6, 8, 12)
WIDTH_SWEEP: Final[tuple[int, ...]] = (1, 32, 96, 128, 256)
WIDTH_LABELS: Final[dict[int, str]] = {
    1: "1",
    32: "32",
    96: "96",
    128: "128",
    256: "256-linked",
}
WORKER_SWEEP: Final[tuple[int, ...]] = (1, 2, 4, 8)

NUMERIC_FUNCTIONS: Final[tuple[str, ...]] = (
    "exp",
    "log",
    "sin",
    "cos",
    "tanh",
    "sigmoid",
    "lgamma",
    "digamma",
    "trigamma",
    "sqrt",
    "gamma_cdf_inverse_shape1",
    "rn64_rational_below_tie",
    "rn64_rational_exact_tie",
    "rn64_rational_above_tie",
    "binary256s_promote",
    "binary256s_subtract",
    "binary256s_sum",
    "binary256s_divide",
    "binary256s_exp",
)

ANALYTIC_KINDS: Final[tuple[str, ...]] = (
    "ALL_ZERO_LEX_TIE",
    "POSITIVE_CURVATURE_SENSE_ENDPOINT",
    "RELAY_HINGE_EXACT",
    "NEGATIVE_CURVATURE_SENSE_ZERO",
    "SYMMETRIC_CONVEX_SPLIT",
    "RELAY_SATURATION_TIE",
    "SECOND_AGENT_SENSE_ENDPOINT",
    "OBJECTIVE_BIT_PLATEAU_LEX_TIE",
)


def require_test_namespace(value: str) -> str:
    if value != TEST_NAMESPACE:
        raise PermissionError("VQFP r05 measurement accepts only its frozen TEST namespace")
    return value

