#include "vqfp_r05_measurement_abi.h"

#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#ifdef _MSC_VER
#include <intrin.h>
#endif

namespace {

struct UInt128 {
    std::uint64_t hi;
    std::uint64_t lo;
};

UInt128 mul64(std::uint64_t a, std::uint64_t b) {
#ifdef _MSC_VER
    UInt128 result{};
    result.lo = _umul128(a, b, &result.hi);
    return result;
#else
    const unsigned __int128 value = static_cast<unsigned __int128>(a) * b;
    return {static_cast<std::uint64_t>(value >> 64), static_cast<std::uint64_t>(value)};
#endif
}

UInt128 shift_left(std::uint64_t value, unsigned shift) {
    if (shift == 0) return {0, value};
    if (shift < 64) return {value >> (64 - shift), value << shift};
    if (shift < 128) return {value << (shift - 64), 0};
    return {std::numeric_limits<std::uint64_t>::max(), std::numeric_limits<std::uint64_t>::max()};
}

int compare(UInt128 a, UInt128 b) {
    if (a.hi != b.hi) return a.hi < b.hi ? -1 : 1;
    if (a.lo != b.lo) return a.lo < b.lo ? -1 : 1;
    return 0;
}

struct Dyadic {
    std::uint64_t mantissa;
    int exponent;
};

Dyadic positive_normal(std::uint64_t bits) {
    const std::uint64_t exp_field = (bits >> 52) & 0x7ffu;
    const std::uint64_t fraction = bits & ((1ull << 52) - 1u);
    if (exp_field == 0 || exp_field == 0x7ffu || (bits >> 63) != 0) return {0, 0};
    return {(1ull << 52) | fraction, static_cast<int>(exp_field) - 1023 - 52};
}

Dyadic midpoint(std::uint64_t a_bits, std::uint64_t b_bits) {
    const Dyadic a = positive_normal(a_bits);
    const Dyadic b = positive_normal(b_bits);
    const int common = a.exponent < b.exponent ? a.exponent : b.exponent;
    const unsigned sa = static_cast<unsigned>(a.exponent - common);
    const unsigned sb = static_cast<unsigned>(b.exponent - common);
    return {(a.mantissa << sa) + (b.mantissa << sb), common - 1};
}

bool rational_greater(std::uint64_t num, std::uint64_t den, Dyadic boundary) {
    if (den == 0 || boundary.mantissa == 0 || boundary.exponent >= 0) return false;
    const unsigned shift = static_cast<unsigned>(-boundary.exponent);
    if (shift >= 128) return false;
    return compare(shift_left(num, shift), mul64(den, boundary.mantissa)) > 0;
}

bool rational_less(std::uint64_t num, std::uint64_t den, Dyadic boundary) {
    if (den == 0 || boundary.mantissa == 0 || boundary.exponent >= 0) return false;
    const unsigned shift = static_cast<unsigned>(-boundary.exponent);
    if (shift >= 128) return false;
    return compare(shift_left(num, shift), mul64(den, boundary.mantissa)) < 0;
}

bool numeric_certificate(const NumericFixture& fixture, const NumericResult& result) {
    if (fixture.schema != VQFP_TEST_SCHEMA || !result.evaluated || !result.exact_match ||
        result.output_bits != fixture.expected_bits) return false;
    if (fixture.certificate_kind == 0) {
        return fixture.kind >= NUM_RATIONAL_BELOW;
    }
    if (fixture.certificate_kind != 1 || fixture.expected_bits == 0 ||
        fixture.lower_den == 0 || fixture.upper_den == 0) return false;
    const std::uint64_t previous = fixture.expected_bits - 1u;
    const std::uint64_t next = fixture.expected_bits + 1u;
    const Dyadic lower_mid = midpoint(previous, fixture.expected_bits);
    const Dyadic upper_mid = midpoint(fixture.expected_bits, next);
    return rational_greater(fixture.lower_num, fixture.lower_den, lower_mid) &&
           rational_less(fixture.upper_num, fixture.upper_den, upper_mid) &&
           compare(mul64(fixture.lower_num, fixture.upper_den),
                   mul64(fixture.upper_num, fixture.lower_den)) <= 0;
}

bool expected_counts(const AnalyticState& state, const AnalyticResult& result) {
    if (state.schema != VQFP_TEST_SCHEMA || state.q_e != VQFP_Q_E || !result.solved ||
        result.proof_kind != state.kind || state.kind > ANA_PLATEAU_LEX) return false;
    std::uint64_t expected[VQFP_MAX_COORDS]{};
    std::uint64_t objective = 0;
    const std::uint64_t q = state.q_e;
    switch (state.kind) {
        case ANA_ALL_ZERO:
        case ANA_PLATEAU_LEX:
            expected[0] = q;
            break;
        case ANA_SENSE_FIRST:
            expected[0] = q;
            objective = 0x3fdcc1ce4581db89ull;
            break;
        case ANA_RELAY_HINGE:
        case ANA_RELAY_TIE:
            if (state.relay_threshold > q) return false;
            expected[0] = q - state.relay_threshold;
            expected[1] = state.relay_threshold;
            break;
        case ANA_NEGATIVE_CURVATURE:
            expected[1] = q;
            break;
        case ANA_SYMMETRIC_SPLIT:
            expected[0] = q / 2;
            expected[2] = q - q / 2;
            objective = 0x3fe57343067270eeull;
            break;
        case ANA_SENSE_SECOND:
            expected[2] = q;
            objective = 0x3fdcc1ce4581db89ull;
            break;
        default:
            return false;
    }
    if (result.objective_bits != objective) return false;
    std::uint64_t sum = 0;
    for (std::uint32_t i = 0; i < VQFP_MAX_COORDS; ++i) {
        if (result.counts[i] != expected[i]) return false;
        if (i < 2u * state.n_agents) sum += result.counts[i];
        else if (result.counts[i] != 0) return false;
    }
    return sum == q && result.node_count >= 1 && result.certificate_bytes >= 112;
}

} // namespace

VQFP_EXPORT std::uint32_t vqfp_r05_checker_abi_version() {
    return VQFP_TEST_ABI;
}

VQFP_EXPORT std::int32_t vqfp_r05_check_numeric_batch(
    const NumericFixture* fixtures,
    const NumericResult* results,
    std::uint32_t width,
    CheckResult* checks
) {
    if (!fixtures || !results || !checks || width == 0 || width > 256) return -1;
    for (std::uint32_t i = 0; i < width; ++i) {
        CheckResult check{};
        const bool valid = numeric_certificate(fixtures[i], results[i]);
        check.accepted = valid ? 1u : 0u;
        check.exact_counts = 1u;
        check.exact_objective = results[i].output_bits == fixtures[i].expected_bits ? 1u : 0u;
        check.certificate_valid = valid ? 1u : 0u;
        checks[i] = check;
    }
    return 0;
}

VQFP_EXPORT std::int32_t vqfp_r05_check_analytic_batch(
    const AnalyticState* states,
    const AnalyticResult* results,
    std::uint32_t width,
    CheckResult* checks
) {
    if (!states || !results || !checks || width == 0 || width > 256) return -1;
    for (std::uint32_t i = 0; i < width; ++i) {
        CheckResult check{};
        const bool valid = expected_counts(states[i], results[i]);
        check.accepted = valid ? 1u : 0u;
        check.exact_counts = valid ? 1u : 0u;
        check.exact_objective = valid ? 1u : 0u;
        check.certificate_valid = valid ? 1u : 0u;
        checks[i] = check;
    }
    return 0;
}

