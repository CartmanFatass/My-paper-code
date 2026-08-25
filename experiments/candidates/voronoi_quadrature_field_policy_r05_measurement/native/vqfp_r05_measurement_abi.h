#pragma once

#include <cstdint>

#ifdef _WIN32
#define VQFP_EXPORT extern "C" __declspec(dllexport)
#else
#define VQFP_EXPORT extern "C"
#endif

static constexpr std::uint32_t VQFP_TEST_SCHEMA = 0x56514635u;
static constexpr std::uint32_t VQFP_TEST_ABI = 1u;
static constexpr std::uint64_t VQFP_Q_E = 52776558133248ull;
static constexpr std::uint32_t VQFP_MAX_COORDS = 24u;

enum NumericKind : std::uint32_t {
    NUM_EXP = 0,
    NUM_LOG = 1,
    NUM_SIN = 2,
    NUM_COS = 3,
    NUM_TANH = 4,
    NUM_SIGMOID = 5,
    NUM_LGAMMA = 6,
    NUM_DIGAMMA = 7,
    NUM_TRIGAMMA = 8,
    NUM_SQRT = 9,
    NUM_GAMMA_INV_SHAPE1 = 10,
    NUM_RATIONAL_BELOW = 11,
    NUM_RATIONAL_TIE = 12,
    NUM_RATIONAL_ABOVE = 13,
    NUM_B256_PROMOTE = 14,
    NUM_B256_SUBTRACT = 15,
    NUM_B256_SUM = 16,
    NUM_B256_DIVIDE = 17,
    NUM_B256_EXP = 18,
};

struct NumericFixture {
    std::uint32_t schema;
    std::uint32_t kind;
    std::uint64_t input_bits;
    std::uint64_t expected_bits;
    std::uint64_t argument_num;
    std::uint64_t argument_den;
    std::uint64_t lower_num;
    std::uint64_t lower_den;
    std::uint64_t upper_num;
    std::uint64_t upper_den;
    std::uint32_t certificate_kind;
    std::uint32_t precision_bits;
};

struct NumericResult {
    std::uint64_t output_bits;
    std::uint32_t evaluated;
    std::uint32_t exact_match;
    std::uint64_t certificate_bytes;
};

enum AnalyticKind : std::uint32_t {
    ANA_ALL_ZERO = 0,
    ANA_SENSE_FIRST = 1,
    ANA_RELAY_HINGE = 2,
    ANA_NEGATIVE_CURVATURE = 3,
    ANA_SYMMETRIC_SPLIT = 4,
    ANA_RELAY_TIE = 5,
    ANA_SENSE_SECOND = 6,
    ANA_PLATEAU_LEX = 7,
};

struct AnalyticState {
    std::uint32_t schema;
    std::uint32_t n_agents;
    std::uint32_t kind;
    std::uint32_t variant;
    std::uint64_t q_e;
    std::uint64_t relay_threshold;
};

struct AnalyticResult {
    std::uint64_t counts[VQFP_MAX_COORDS];
    std::uint64_t objective_bits;
    std::uint64_t node_count;
    std::uint64_t certificate_bytes;
    std::uint32_t proof_kind;
    std::uint32_t solved;
};

struct CheckResult {
    std::uint32_t accepted;
    std::uint32_t exact_counts;
    std::uint32_t exact_objective;
    std::uint32_t certificate_valid;
};

