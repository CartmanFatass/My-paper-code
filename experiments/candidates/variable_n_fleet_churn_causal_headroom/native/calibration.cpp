#include <chrono>
#include "../../variable_n_fleet_churn_headroom/native/headroom_backend.cpp"

namespace vnfc_causal_cost {
using namespace bpcr_general;
using Clock = std::chrono::steady_clock;
struct ScoreTiming {
    double seconds;
    std::int32_t count, scorer_checker, enumerator, records;
};
struct UnitTiming { double seconds; std::int32_t count; };
struct Calibration {
    ScoreTiming scores[6];
    UnitTiming ticks[4];
    UnitTiming prehistory;
};
volatile std::int64_t sink = 0;
double elapsed(Clock::time_point start) {
    return std::chrono::duration<double>(Clock::now() - start).count();
}

// Same seven depot agents as deterministic_maximum_bcrh; no panel or RNG access.
GBcrhInput synthetic_input(int epoch) {
    GBcrhInput in{};
    in.magic = kMagic;
    in.abi = kAbiVersion;
    in.epoch = epoch;
    in.failed_zone = 1;
    in.active_count = 7;
    for (int rank = 1; rank <= 7; ++rank)
        in.agents[rank - 1] = GAgentIn{
            rank, rank, rank % 2, 1 + rank % 2,
            0, -1, -1, 0, 0, -1, 0, 0, 800};
    in.accrued_fail_delivered = 200;
    in.accrued_fail_demand = 240;
    in.accrued_total_delivered = 400;
    in.accrued_total_demand = 480;
    in.demand1 = in.demand2 = 2;
    in.blocked1 = in.blocked2 = 1;
    return in;
}

int calibrate(Calibration& out) {
    out = {};
    auto facts = std::make_unique<GBcrhOutput>();
    for (int epoch = 0; epoch < 6; ++epoch) {
        const auto in = synthetic_input(epoch);
        auto start = Clock::now();
        int status = grun_bcrh(in, *facts);
        out.scores[epoch].seconds = elapsed(start);
        if (status) return status;
        auto& row = out.scores[epoch];
        row.count = facts->candidate_count;
        row.scorer_checker = facts->scorer_checker_equal;
        row.enumerator = facts->independent_enumerator_equal;
        row.records = 1;
        for (int i = 0; i < row.count; ++i)
            row.records &= facts->records[i].exact_match;
    }

    // Moving, acquiring, serving, then eight-agent pre-loss transition work.
    // Each measured copy includes accounting; state/command values never leave here.
    for (int kind = 0; kind < 4; ++kind) {
        GS initial = gstate_from_bcrh(synthetic_input(0));
        if (kind == 3) {
            initial.a.push_back(GA{8, 8, 0, 1, 0, -1, -1, 0, 0, -1, 0, 0, 800});
            initial.post_time = -120;
        }
        for (int token = 0; token < 4; ++token) {
            auto& a = initial.a[token];
            a.token = token;
            a.state = kind == 2 ? 2 : 1;
            a.elapsed = kind == 2 ? gacq(token) : 0;
            if (kind == 1 || kind == 2) a.node = gtoken_node(token);
            gstart_route(a, gtoken_node(token));
        }
        auto start = Clock::now();
        for (int copy = 0; copy < 128; ++copy) {
            GS state = initial;
            GEpisodeOutput accounting{};
            for (int tick = 0; tick < 20; ++tick) {
                gtick(state, 2, 2, 1, 1, kind != 3, &accounting);
                ++accounting.integrated_ticks;
            }
            std::int64_t value = state.at + state.post_time + accounting.event_count;
            for (const auto& a : state.a) value += a.energy + a.node + a.elapsed;
            sink = value;
        }
        out.ticks[kind] = {elapsed(start), 128 * 20};
    }

    // Six independent maximum-support eight-agent synthetic pre-loss decisions.
    auto start = Clock::now();
    for (int epoch = 0; epoch < 6; ++epoch) {
        GS state = gstate_from_bcrh(synthetic_input(0));
        state.a.push_back(GA{8, 8, 0, 1, 0, -1, -1, 0, 0, -1, 0, 0, 800});
        state.post_time = -120 + 20 * epoch;
        GC command = gprehistory(state, 1, 1);
        int status = gapply(state, command);
        if (status) return status;
        sink = command.o[0] + state.a[0].edge_remaining;
    }
    out.prehistory = {elapsed(start), 6};
    return 0;
}
} // namespace vnfc_causal_cost

BPCR_EXPORT int vnfc_causal_calibrate(vnfc_causal_cost::Calibration* out) {
    return vnfc_causal_cost::calibrate(*out);
}
