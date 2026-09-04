#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cmath>
#include <intrin.h>
#include <numeric>
#include <stdexcept>
#include <tuple>
#include <vector>

// bpcr_general.hpp also contains dormant BCRH surfaces whose outer translation-
// unit helpers are not part of this B-only adapter.  Fail-closed definitions let
// the exact header compile without copying those unused transition/scoring laws.
namespace {
constexpr std::int32_t kAbiVersion = 1;
constexpr std::uint64_t kMagic = UINT64_C(0x564E464342504352);
[[noreturn]] void excluded_surface() {
    throw std::logic_error("B tick adapter excludes the R09 BCRH surface");
}
int state_index(int, int, int, int) { excluded_surface(); }
void decode_state(int, int&, int&, int&, int&) { excluded_surface(); }
std::uint64_t transition_num(int, int) { excluded_surface(); }
int demand_inc(int, bool, int) { excluded_surface(); }
}

// Keep every R09 export in this DLL private.  Only VNFC B tick symbols below
// are exported, so this sidecar cannot be mistaken for the registered C DLL.
#define BPCR_EXPORT extern "C"
#include "../../variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp"
#undef BPCR_EXPORT

#if defined(_WIN32)
#define VNFC_B_EXPORT extern "C" __declspec(dllexport)
#else
#define VNFC_B_EXPORT extern "C"
#endif

#ifndef VNFC_B_BUILD_FINGERPRINT
#error VNFC_B_BUILD_FINGERPRINT must be supplied by the content-addressed loader
#endif

namespace vnfc_b_tick {
constexpr std::int32_t kBAbiVersion = 1;
constexpr std::uint64_t kBBuildMagic = UINT64_C(0x564E46434254454C);
constexpr std::int32_t kMinimumBatchWidth = 8;
constexpr std::int32_t kTicksPerStep = 20;

struct TickRow {
    std::int32_t post_loss_second;
    std::int32_t tick_end_second;
    std::int32_t integrated_ticks;
    std::int32_t zone1_delivery;
    std::int32_t zone2_delivery;
    std::int32_t failed_zone_delivery;
    std::int32_t failed_executor_state_before;
    std::int32_t failed_executor_rank_before;
    std::int32_t failed_executor_acquisition_elapsed_before;
    std::int32_t failed_executor_state_after;
    std::int32_t failed_executor_rank_after;
    std::int32_t failed_executor_acquisition_elapsed_after;
    std::int32_t acquisition_transition;
};

struct StepOutput {
    bpcr_general::GInteractiveOutput interactive;
    std::int32_t tick_count;
    TickRow ticks[kTicksPerStep];
};

int step_one(
    bpcr_general::GSession& session,
    const std::int32_t* command,
    StepOutput& output
) {
    using namespace bpcr_general;
    if (session.terminal || session.epoch < 0 || session.epoch >= G_POST) return 1;
    GC candidate;
    for (int token = 0; token < G_TOKENS; ++token) candidate.o[token] = command[token];
    const int command_error = gcommand_error(session.state, candidate);
    if (command_error) return 100 + command_error;

    output = {};
    const int epoch = session.epoch;
    const int source_epoch = epoch + G_POST;
    const int q1 = session.input.demand1[source_epoch];
    const int q2 = session.input.demand2[source_epoch];
    const int h1 = session.input.blocked1[source_epoch];
    const int h2 = session.input.blocked2[source_epoch];
    gobservation(
        session.state,
        epoch,
        q1,
        q2,
        h1,
        h2,
        &session.input.post_presentation[epoch * G_MAX_AGENTS],
        output.interactive.applied_decision
    );
    for (int token = 0; token < G_TOKENS; ++token) {
        output.interactive.applied_decision.command[token] = candidate.o[token];
    }
    if (gapply(session.state, candidate)) return 2;

    const int failed_token = session.state.failed_zone == 1 ? 0 : 2;
    for (int tick = 0; tick < kTicksPerStep; ++tick) {
        TickRow& row = output.ticks[tick];
        row.post_loss_second = session.state.post_time;
        row.tick_end_second = row.post_loss_second + 1;
        const auto delivery = gdelivery(session.state, q1, q2, h1, h2);
        row.zone1_delivery = delivery[0];
        row.zone2_delivery = delivery[1];
        row.failed_zone_delivery = delivery[session.state.failed_zone - 1];
        row.failed_executor_state_before = gtoken_state(
            session.state,
            failed_token,
            row.failed_executor_acquisition_elapsed_before,
            row.failed_executor_rank_before
        );
        gtick(session.state, q1, q2, h1, h2, true, &session.accounting);
        ++session.accounting.integrated_ticks;
        row.integrated_ticks = session.accounting.integrated_ticks;
        row.failed_executor_state_after = gtoken_state(
            session.state,
            failed_token,
            row.failed_executor_acquisition_elapsed_after,
            row.failed_executor_rank_after
        );
        row.acquisition_transition =
            (row.failed_executor_state_before == 0 || row.failed_executor_state_before == 1) &&
            row.failed_executor_state_after == 2;
        ++output.tick_count;
    }
    ++session.accounting.post_decisions;
    ++session.epoch;
    session.terminal = session.epoch == G_POST;
    ginteractive_snapshot(session, output.interactive);
    if (!session.terminal) {
        const int next = session.epoch + G_POST;
        gobservation(
            session.state,
            session.epoch,
            session.input.demand1[next],
            session.input.demand2[next],
            session.input.blocked1[next],
            session.input.blocked2[next],
            &session.input.post_presentation[session.epoch * G_MAX_AGENTS],
            output.interactive.next_observation
        );
    }
    return (session.accounting.safety_violation || session.accounting.exclusivity_violation) ? 5 : 0;
}
}

VNFC_B_EXPORT std::int32_t vnfc_b_tick_abi_version() {
    return vnfc_b_tick::kBAbiVersion;
}
VNFC_B_EXPORT std::uint64_t vnfc_b_tick_build_magic() {
    return vnfc_b_tick::kBBuildMagic;
}
VNFC_B_EXPORT const char* vnfc_b_tick_build_fingerprint() {
    return VNFC_B_BUILD_FINGERPRINT;
}
VNFC_B_EXPORT std::size_t vnfc_b_tick_sizeof_episode_input() {
    return sizeof(bpcr_general::GEpisodeInput);
}
VNFC_B_EXPORT std::size_t vnfc_b_tick_sizeof_interactive_output() {
    return sizeof(bpcr_general::GInteractiveOutput);
}
VNFC_B_EXPORT std::size_t vnfc_b_tick_sizeof_tick_row() {
    return sizeof(vnfc_b_tick::TickRow);
}
VNFC_B_EXPORT std::size_t vnfc_b_tick_sizeof_step_output() {
    return sizeof(vnfc_b_tick::StepOutput);
}

VNFC_B_EXPORT std::int32_t vnfc_b_tick_reset_batch(
    const bpcr_general::GEpisodeInput* inputs,
    std::int32_t width,
    void** handles,
    bpcr_general::GInteractiveOutput* outputs
) {
    if (!inputs || !handles || !outputs || width < vnfc_b_tick::kMinimumBatchWidth) return 10;
    for (int index = 0; index < width; ++index) handles[index] = nullptr;
    std::vector<bpcr_general::GSession*> pending(static_cast<std::size_t>(width), nullptr);
    try {
        std::vector<bpcr_general::GInteractiveOutput> pending_outputs(static_cast<std::size_t>(width));
        for (int index = 0; index < width; ++index) {
            const int status = bpcr_general::ginteractive_reset(
                inputs[index], pending[index], pending_outputs[index]
            );
            if (status) {
                for (auto* session : pending) delete session;
                return 20 + status;
            }
        }
        for (int index = 0; index < width; ++index) {
            handles[index] = pending[index];
            outputs[index] = pending_outputs[index];
        }
    } catch (...) {
        for (auto* session : pending) delete session;
        return 99;
    }
    return 0;
}

VNFC_B_EXPORT std::int32_t vnfc_b_tick_step_batch(
    void** handles,
    const std::int32_t* commands,
    std::int32_t width,
    vnfc_b_tick::StepOutput* outputs
) {
    if (!handles || !commands || !outputs || width < vnfc_b_tick::kMinimumBatchWidth) return 10;
    try {
        // This pass is deliberately complete before any copied session advances.
        for (int index = 0; index < width; ++index) {
            auto* session = static_cast<bpcr_general::GSession*>(handles[index]);
            if (!session || session->terminal) return 11;
            bpcr_general::GC candidate;
            for (int token = 0; token < bpcr_general::G_TOKENS; ++token) {
                candidate.o[token] = commands[4 * index + token];
            }
            if (bpcr_general::gcommand_error(session->state, candidate)) return 12;
        }
        std::vector<bpcr_general::GSession> pending;
        pending.reserve(static_cast<std::size_t>(width));
        for (int index = 0; index < width; ++index) {
            pending.push_back(*static_cast<bpcr_general::GSession*>(handles[index]));
        }
        std::vector<vnfc_b_tick::StepOutput> pending_outputs(static_cast<std::size_t>(width));
        for (int index = 0; index < width; ++index) {
            const int status = vnfc_b_tick::step_one(
                pending[index], &commands[4 * index], pending_outputs[index]
            );
            if (status) return 20 + status;
        }
        for (int index = 0; index < width; ++index) {
            *static_cast<bpcr_general::GSession*>(handles[index]) = std::move(pending[index]);
            outputs[index] = pending_outputs[index];
        }
    } catch (...) {
        return 99;
    }
    return 0;
}

VNFC_B_EXPORT std::int32_t vnfc_b_tick_close_batch(void** handles, std::int32_t width) {
    if (!handles || width < vnfc_b_tick::kMinimumBatchWidth) return 10;
    for (int index = 0; index < width; ++index) {
        if (!handles[index]) return 11;
    }
    for (int index = 0; index < width; ++index) {
        delete static_cast<bpcr_general::GSession*>(handles[index]);
        handles[index] = nullptr;
    }
    return 0;
}
