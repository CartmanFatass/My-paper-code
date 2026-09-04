#include <memory>

// Build the registered R09 implementation unchanged into this analysis DLL.
// The adapter below only composes its public-law state and functions.
#include "../../variable_n_fleet_churn_bpcr_r09/native/bpcr_backend.cpp"

namespace vnfc_headroom {
using namespace bpcr_general;

constexpr int kPolicies = 3;
constexpr int kDepths = 3;

struct HeadroomOutput {
    std::int32_t status, failed_rank, beam_width;
    std::int64_t numerator[kPolicies], denominator[kPolicies];
    std::int32_t commands[kPolicies][24];
    std::int32_t terminal_completion_commands[2][12];
    std::int32_t terminal[kPolicies], safety_violation[kPolicies], exclusivity_violation[kPolicies];
    std::int32_t bcrh_candidate_count[6], bcrh_scorer_checker_equal[6];
    std::int32_t bcrh_independent_enumerator_equal[6], bcrh_all_candidate_records_exact[6];
    std::int32_t bcrh_scorer_command[6][4], bcrh_checker_command[6][4];
    std::uint64_t bcrh_candidate_digest[6], bcrh_checker_digest[6];
    std::int64_t beam_states_before[kDepths], beam_legal_commands[kDepths];
    std::int64_t beam_expansions[kDepths], beam_states_retained[kDepths];
    std::int64_t beam_native_ticks[kDepths];
    std::int32_t persist_candidate_count, persist_sensitivity_agreement;
    std::int64_t persist_native_ticks, bcrh_native_ticks, terminal_completion_native_ticks;
};

struct Node {
    GS state;
    int safety_violation = 0;
    std::array<int, 12> prefix{};
    Node() { prefix.fill(G_NULL); }
};

bool prefix_less(const Node& a, const Node& b, int commands) {
    return std::lexicographical_compare(
        a.prefix.begin(), a.prefix.begin() + 4 * commands,
        b.prefix.begin(), b.prefix.begin() + 4 * commands
    );
}

bool ratio_better(const Node& a, const Node& b, int commands) {
    const auto left = a.state.af * b.state.df;
    const auto right = b.state.af * a.state.df;
    return left != right ? left > right : prefix_less(a, b, commands);
}

bool reset_post_loss(
    const GEpisodeInput& input, GS& state, int& failed_rank,
    std::array<int, 24>& prehistory
) {
    if (input.magic != kMagic || input.abi != kAbiVersion ||
        input.failed_zone < 1 || input.failed_zone > 2 || input.active_count != 8) return false;
    state = gstate_from_episode(input);
    GEpisodeOutput accounting{};
    for (int epoch = 0; epoch < 6; ++epoch) {
        GC command = gprehistory(state, input.blocked1[epoch], input.blocked2[epoch]);
        for (int token = 0; token < 4; ++token) prehistory[4 * epoch + token] = command.o[token];
        if (gapply(state, command)) return false;
        for (int second = 0; second < 20; ++second)
            gtick(state, input.demand1[epoch], input.demand2[epoch],
                  input.blocked1[epoch], input.blocked2[epoch], false, &accounting);
    }
    const int failed_token = input.failed_zone == 1 ? 0 : 2;
    for (auto it = state.a.begin(); it != state.a.end(); ++it) {
        if (it->token == failed_token && it->state == 2) {
            failed_rank = it->rank;
            state.a.erase(it);
            break;
        }
    }
    if (!failed_rank) return false;
    state.clear[failed_token] = 20;
    state.post_time = 0;
    return true;
}

bool advance(
    GS& state, int& safety_violation, const GEpisodeInput& input,
    int epoch, const GC& command
) {
    if (gapply(state, command)) return false;
    for (int second = 0; second < 20; ++second) {
        gtick(state, input.demand1[epoch + 6], input.demand2[epoch + 6],
              input.blocked1[epoch + 6], input.blocked2[epoch + 6], true);
        for (const auto& agent : state.a)
            if (agent.energy < 100) safety_violation = 1;
    }
    return true;
}

GBcrhInput bcrh_input(const GS& state, const GEpisodeInput& input, int epoch) {
    GBcrhInput out{};
    out.magic = kMagic; out.abi = kAbiVersion; out.epoch = epoch;
    out.failed_zone = state.failed_zone; out.active_count = static_cast<int>(state.a.size());
    for (int index = 0; index < out.active_count; ++index) {
        const auto& a = state.a[index];
        out.agents[index] = GAgentIn{a.rank, a.opaque, a.fast, a.radio, a.node,
            a.edge_from, a.edge_to, a.edge_remaining, a.dest, a.token,
            a.state, a.elapsed, a.energy};
    }
    for (int token = 0; token < 4; ++token) out.clearance[token] = state.clear[token];
    out.accrued_fail_delivered = state.af; out.accrued_fail_demand = state.df;
    out.accrued_total_delivered = state.at; out.accrued_total_demand = state.dt;
    out.demand1 = input.demand1[epoch + 6]; out.demand2 = input.demand2[epoch + 6];
    out.blocked1 = input.blocked1[epoch + 6]; out.blocked2 = input.blocked2[epoch + 6];
    return out;
}

bool complete_lexicographically(
    Node& node, const GEpisodeInput& input, int policy,
    HeadroomOutput& output
) {
    for (int epoch = 3; epoch < 6; ++epoch) {
        auto commands = genum(node.state);
        std::sort(commands.begin(), commands.end(), [](const GC& a, const GC& b) { return a.o < b.o; });
        if (commands.empty()) return false;
        const GC command = commands.front();
        for (int token = 0; token < 4; ++token) {
            output.commands[policy][4 * epoch + token] = command.o[token];
            output.terminal_completion_commands[policy - 1][4 * (epoch - 3) + token] = command.o[token];
        }
        if (!advance(node.state, node.safety_violation, input, epoch, command)) return false;
        output.terminal_completion_native_ticks += 20;
    }
    output.terminal[policy] = 1;
    output.safety_violation[policy] = node.safety_violation;
    output.exclusivity_violation[policy] = 0;
    return true;
}

bool run_bcrh(const GEpisodeInput& input, const GS& initial, HeadroomOutput& output) {
    Node node; node.state = initial;
    for (int epoch = 0; epoch < 6; ++epoch) {
        auto native_input = bcrh_input(node.state, input, epoch);
        auto facts = std::make_unique<GBcrhOutput>();
        if (grun_bcrh(native_input, *facts)) return false;
        output.bcrh_candidate_count[epoch] = facts->candidate_count;
        output.bcrh_scorer_checker_equal[epoch] = facts->scorer_checker_equal;
        output.bcrh_independent_enumerator_equal[epoch] = facts->independent_enumerator_equal;
        output.bcrh_candidate_digest[epoch] = facts->candidate_digest;
        output.bcrh_checker_digest[epoch] = facts->checker_digest;
        bool all_exact = true;
        for (int index = 0; index < facts->candidate_count; ++index)
            all_exact = all_exact && facts->records[index].exact_match;
        output.bcrh_all_candidate_records_exact[epoch] = all_exact;
        GC command;
        for (int token = 0; token < 4; ++token) {
            command.o[token] = facts->scorer_command[token];
            output.commands[0][4 * epoch + token] = command.o[token];
            output.bcrh_scorer_command[epoch][token] = facts->scorer_command[token];
            output.bcrh_checker_command[epoch][token] = facts->checker_command[token];
        }
        if (!advance(node.state, node.safety_violation, input, epoch, command)) return false;
        output.bcrh_native_ticks += 20;
        if (epoch == 2) {
            output.numerator[0] = node.state.af;
            output.denominator[0] = node.state.df;
        }
    }
    output.terminal[0] = 1;
    output.safety_violation[0] = node.safety_violation;
    output.exclusivity_violation[0] = 0;
    return true;
}

GC released_persistent_command(const GS& state, const GC& initial, std::array<bool, 4>& released) {
    GC command = initial;
    for (int token = 0; token < 4; ++token) {
        if (released[token]) { command.o[token] = G_NULL; continue; }
        const int rank = command.o[token], index = gfind(state, rank);
        if (rank != G_NULL && index >= 0 && !genroute(state.a[index]) &&
            gcontingency(state, state.a[index], token).second < 0) {
            command.o[token] = G_NULL;
            released[token] = true;
        }
    }
    return command;
}

bool run_persistent(const GEpisodeInput& input, const GS& initial, HeadroomOutput& output) {
    auto candidates = genum(initial);
    std::sort(candidates.begin(), candidates.end(), [](const GC& a, const GC& b) { return a.o < b.o; });
    if (candidates.empty()) return false;
    output.persist_candidate_count = static_cast<int>(candidates.size());
    Node best; bool have_best = false; GC best_initial;
    for (const GC& initial_command : candidates) {
        Node node; node.state = initial;
        std::array<bool, 4> released{};
        for (int epoch = 0; epoch < 3; ++epoch) {
            const GC command = epoch == 0 ? initial_command :
                released_persistent_command(node.state, initial_command, released);
            for (int token = 0; token < 4; ++token) node.prefix[4 * epoch + token] = command.o[token];
            if (!advance(node.state, node.safety_violation, input, epoch, command)) return false;
            output.persist_native_ticks += 20;
        }
        if (!have_best || node.state.af * best.state.df > best.state.af * node.state.df ||
            (node.state.af * best.state.df == best.state.af * node.state.df && initial_command.o < best_initial.o)) {
            best = std::move(node); best_initial = initial_command; have_best = true;
        }
    }
    GSensitivityInput sensitivity{};
    sensitivity.current = bcrh_input(initial, input, 0);
    for (int epoch = 0; epoch < 3; ++epoch) {
        sensitivity.demand1[epoch] = input.demand1[epoch + 6];
        sensitivity.demand2[epoch] = input.demand2[epoch + 6];
        sensitivity.blocked1[epoch] = input.blocked1[epoch + 6];
        sensitivity.blocked2[epoch] = input.blocked2[epoch + 6];
    }
    GSensitivityOutput reference{};
    if (grun_sensitivity(sensitivity, reference)) return false;
    output.persist_sensitivity_agreement = reference.candidate_count == output.persist_candidate_count &&
        reference.max_c60 == best.state.af &&
        std::equal(best_initial.o.begin(), best_initial.o.end(), reference.max_command);
    output.numerator[1] = best.state.af; output.denominator[1] = best.state.df;
    for (int index = 0; index < 12; ++index) output.commands[1][index] = best.prefix[index];
    return complete_lexicographically(best, input, 1, output);
}

bool run_beam(const GEpisodeInput& input, const GS& initial, int width, HeadroomOutput& output) {
    std::vector<Node> retained(1); retained[0].state = initial;
    Node selected; bool selected_set = false;
    for (int depth = 0; depth < 3; ++depth) {
        output.beam_states_before[depth] = static_cast<std::int64_t>(retained.size());
        std::vector<Node> expanded;
        if (depth < 2) expanded.reserve(retained.size() * 256);
        for (const Node& parent : retained) {
            auto commands = genum(parent.state);
            std::sort(commands.begin(), commands.end(), [](const GC& a, const GC& b) { return a.o < b.o; });
            output.beam_legal_commands[depth] += static_cast<std::int64_t>(commands.size());
            for (const GC& command : commands) {
                Node child = parent;
                for (int token = 0; token < 4; ++token) child.prefix[4 * depth + token] = command.o[token];
                if (!advance(child.state, child.safety_violation, input, depth, command)) return false;
                ++output.beam_expansions[depth]; output.beam_native_ticks[depth] += 20;
                if (depth == 2) {
                    if (!selected_set || ratio_better(child, selected, 3)) {
                        selected = std::move(child); selected_set = true;
                    }
                } else {
                    expanded.push_back(std::move(child));
                }
            }
        }
        if (depth < 2) {
            auto better = [depth](const Node& a, const Node& b) {
                return a.state.af != b.state.af ? a.state.af > b.state.af : prefix_less(a, b, depth + 1);
            };
            const std::size_t keep = std::min<std::size_t>(width, expanded.size());
            if (keep < expanded.size()) std::nth_element(expanded.begin(), expanded.begin() + keep, expanded.end(), better);
            expanded.resize(keep); std::sort(expanded.begin(), expanded.end(), better);
            retained = std::move(expanded);
            output.beam_states_retained[depth] = static_cast<std::int64_t>(retained.size());
        } else {
            output.beam_states_retained[depth] = selected_set ? 1 : 0;
        }
    }
    if (!selected_set) return false;
    output.numerator[2] = selected.state.af; output.denominator[2] = selected.state.df;
    for (int index = 0; index < 12; ++index) output.commands[2][index] = selected.prefix[index];
    return complete_lexicographically(selected, input, 2, output);
}

int run(const GEpisodeInput& input, int width, HeadroomOutput& output) {
    output = {};
    output.beam_width = width;
    for (int policy = 0; policy < kPolicies; ++policy)
        for (int index = 0; index < 24; ++index) output.commands[policy][index] = G_NULL;
    for (int policy = 0; policy < 2; ++policy)
        for (int index = 0; index < 12; ++index) output.terminal_completion_commands[policy][index] = G_NULL;
    if (width <= 0) return 1;
    GS initial; int failed_rank = 0; std::array<int, 24> prehistory{};
    if (!reset_post_loss(input, initial, failed_rank, prehistory)) return 2;
    output.failed_rank = failed_rank;
    if (!run_bcrh(input, initial, output)) return 3;
    if (!run_persistent(input, initial, output)) return 4;
    if (!run_beam(input, initial, width, output)) return 5;
    for (int policy = 0; policy < kPolicies; ++policy)
        if (!output.terminal[policy] || output.denominator[policy] <= 0) return 6;
    return 0;
}
}  // namespace vnfc_headroom

BPCR_EXPORT std::size_t vnfc_headroom_sizeof_output() { return sizeof(vnfc_headroom::HeadroomOutput); }
BPCR_EXPORT std::int32_t vnfc_headroom_run(
    const bpcr_general::GEpisodeInput* input, std::int32_t beam_width,
    vnfc_headroom::HeadroomOutput* output
) {
    if (!input || !output) return 10;
    try {
        const int status = vnfc_headroom::run(*input, beam_width, *output);
        output->status = status;
        return status ? 20 + status : 0;
    } catch (...) {
        output->status = 99;
        return 99;
    }
}
