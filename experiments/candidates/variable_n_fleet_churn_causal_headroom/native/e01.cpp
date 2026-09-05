#include <thread>
#include "../../variable_n_fleet_churn_headroom/native/headroom_backend.cpp"

namespace vnfc_e01 {
using namespace bpcr_general;

using WeightKey = std::tuple<int, int, int, int, int, int, std::int64_t, std::int64_t>;

WeightKey weight_key(const GBcrhInput& in) {
    // Raw public values, including both demands even after the fail horizon.
    return {in.epoch, in.failed_zone, in.demand1, in.demand2, in.blocked1,
            in.blocked2, in.accrued_total_demand, in.accrued_fail_demand};
}

int full_call(const GBcrhInput& in, const GW& weights, GBcrhOutput& out) {
    // Only orchestration is local. Every numerical/physical helper is unchanged.
    if (in.magic != kMagic || in.abi != kAbiVersion || in.epoch < 0 ||
        in.epoch > 5 || in.failed_zone < 1 || in.failed_zone > 2 ||
        in.active_count < 1 || in.active_count > 7) return 1;
    GS state = gstate_from_bcrh(in);
    auto commands = genum(state);
    std::sort(commands.begin(), commands.end(), [](const auto& a, const auto& b) {
        return a.o < b.o;
    });
    auto checker_state = independent_checker::build(in);
    auto checker_commands = independent_checker::enumerate(checker_state);
    if (commands.empty() || commands.size() > 1961 ||
        checker_commands.size() > 1961 || commands.size() != checker_commands.size()) return 2;
    for (std::size_t i = 0; i < commands.size(); ++i)
        if (commands[i].o != checker_commands[i].o) return 2;

    std::vector<GScore> scores;
    for (const auto& command : commands)
        scores.push_back(gscore(in, state, command, weights, false));
    std::size_t selected = 0;
    for (std::size_t i = 1; i < commands.size(); ++i)
        if (gbetter(scores[i], scores[selected])) selected = i;
    // The checker builds its own state, weights, schedules and exact scores.
    const auto checker = independent_checker::evaluate(in);
    if (checker.records.size() != commands.size() || checker.records.empty()) return 2;
    const auto& checked = checker.records[checker.selected];
    const auto& score = scores[selected];
    out = {};
    out.candidate_count = static_cast<int>(commands.size());
    out.independent_enumerator_equal = 1;
    for (int token = 0; token < 4; ++token) {
        out.scorer_command[token] = commands[selected].o[token];
        out.checker_command[token] = checked.command.o[token];
    }
    out.scorer_checker_equal = commands[selected].o == checked.command.o &&
        score.fn == checked.score.fn && score.fd == checked.score.fd &&
        score.obj.x == checked.score.objective.x;
    out.post60_reduced = in.epoch >= 3;
    out.floor_num = score.fn;
    out.floor_den = score.fd;
    out.releases = score.releases;
    out.event_records = 18 * in.active_count;
    out.reward_records = 288;
    for (int limb = 0; limb < 4; ++limb) {
        out.objective_limbs[limb] = score.obj.x[limb];
        out.checker_objective_limbs[limb] = checked.score.objective.x[limb];
    }
    out.candidate_digest = gdigest(commands, scores);
    out.checker_digest = checker.digest;
    for (std::size_t i = 0; i < commands.size(); ++i) {
        auto& record = out.records[i];
        const auto& reference = checker.records[i];
        for (int token = 0; token < 4; ++token) record.command[token] = commands[i].o[token];
        record.floor_num = scores[i].fn;
        record.floor_den = scores[i].fd;
        record.releases = scores[i].releases;
        record.checker_floor_num = reference.score.fn;
        record.checker_floor_den = reference.score.fd;
        record.checker_releases = reference.score.releases;
        for (int limb = 0; limb < 4; ++limb) {
            record.objective_limbs[limb] = scores[i].obj.x[limb];
            record.checker_objective_limbs[limb] = reference.score.objective.x[limb];
        }
        record.exact_match = commands[i].o == reference.command.o &&
            scores[i].fn == reference.score.fn && scores[i].fd == reference.score.fd &&
            scores[i].releases == reference.score.releases &&
            scores[i].obj.x == reference.score.objective.x;
    }
    return 0;
}

int batch(const GBcrhInput* inputs, int count, GBcrhOutput* outputs, int& unique_weights) {
    // Capacity is fixed at eight; a tail contains only its actual logical items.
    std::vector<WeightKey> keys;
    std::vector<GW> prepared;
    std::array<std::size_t, 8> index{};
    for (int i = 0; i < count; ++i) {
        const auto key = weight_key(inputs[i]);
        auto found = std::find(keys.begin(), keys.end(), key);
        index[i] = static_cast<std::size_t>(found - keys.begin());
        if (found == keys.end()) {
            keys.push_back(key);
            prepared.push_back(gweights(inputs[i]));
        }
    }
    unique_weights = static_cast<int>(prepared.size());
    const auto& immutable = prepared;
    auto lane = [&](int participant) {
        for (int i = participant; i < count; i += 4) {
            try {
                outputs[i].status = full_call(inputs[i], immutable[index[i]], outputs[i]);
            } catch (...) {
                outputs[i].status = 99;
            }
        }
    };
    {
        // No dispatcher, queue, nested team, or second scientific process.
        std::jthread one(lane, 1), two(lane, 2), three(lane, 3);
        lane(0);
    } // All three join before logical-order error/record consumption.
    for (int i = 0; i < count; ++i)
        if (outputs[i].status) return 1000 + i;
    return 0;
}
} // namespace vnfc_e01

BPCR_EXPORT int vnfc_e01_batch(const bpcr_general::GBcrhInput* inputs, int count,
                              bpcr_general::GBcrhOutput* outputs, int* unique_weights) {
    if (count < 1 || count > 8) return 10;
    try {
        return vnfc_e01::batch(inputs, count, outputs, *unique_weights);
    } catch (...) {
        return 99;
    }
}

BPCR_EXPORT void vnfc_e01_session_input(void* handle, bpcr_general::GBcrhInput* out,
                                      std::int64_t* zone_totals) {
    const auto& session = *static_cast<bpcr_general::GSession*>(handle);
    // The terminal state uses the last public tape entry; no future entry is read.
    *out = vnfc_headroom::bcrh_input(session.state, session.input,
                                   std::min(session.epoch, 5));
    for (int zone = 0; zone < 2; ++zone) {
        zone_totals[zone] = session.state.za[zone];
        zone_totals[zone + 2] = session.state.zd[zone];
    }
    zone_totals[4] = session.state.post_time;
}
