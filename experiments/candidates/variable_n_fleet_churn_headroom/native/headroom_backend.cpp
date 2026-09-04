#include <memory>
#include <cstring>

// Build the registered R09 implementation unchanged into this analysis DLL.
// The adapter below only composes its public-law state and functions.
#include "../../variable_n_fleet_churn_bpcr_r09/native/bpcr_backend.cpp"

namespace vnfc_headroom {
using namespace bpcr_general;

constexpr int kPolicies = 3;
constexpr int kDepths = 3;
constexpr int kMaxCommands = 1961;

using CommandScratch = std::array<GC, kMaxCommands>;

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
    GBcrhCandidateRecord bcrh_candidate_records[6][kMaxCommands];
    std::int64_t beam_states_before[kDepths], beam_legal_commands[kDepths];
    std::int64_t beam_expansions[kDepths], beam_states_retained[kDepths];
    std::int64_t beam_native_ticks[kDepths];
    std::int64_t beam_current_nodes_high_water[kDepths];
    std::int64_t beam_next_nodes_high_water[kDepths];
    std::int64_t beam_transient_nodes_high_water[kDepths];
    std::int64_t beam_live_nodes_high_water[kDepths];
    std::int64_t beam_current_capacity_high_water[kDepths];
    std::int64_t beam_next_capacity_high_water[kDepths];
    std::int64_t beam_current_agent_capacity_high_water[kDepths];
    std::int64_t beam_next_agent_capacity_high_water[kDepths];
    std::int64_t beam_transient_agent_capacity_high_water[kDepths];
    std::int64_t beam_current_owned_bytes_high_water[kDepths];
    std::int64_t beam_next_owned_bytes_high_water[kDepths];
    std::int64_t beam_transient_owned_bytes_high_water[kDepths];
    std::int64_t beam_total_owned_bytes_high_water[kDepths];
    std::int64_t beam_replacements[kDepths];
    std::int64_t beam_enumerator_count_high_water[kDepths];
    std::int64_t beam_fixed_enumerator_scratch_bytes;
    std::int64_t beam_conservative_fixed_storage_allowance_bytes;
    std::int32_t persist_candidate_count, persist_sensitivity_agreement;
    std::int64_t persist_native_ticks, bcrh_native_ticks, terminal_completion_native_ticks;
};

struct Node {
    GS state;
    int safety_violation = 0;
    std::array<int, 12> prefix{};
    Node() { prefix.fill(G_NULL); }
};

struct SelectorInput {
    std::int64_t score;
    std::int32_t prefix[12];
};

struct SelectorItem {
    SelectorInput rank{};
    std::int32_t source_index = 0;
};

struct SelectorBetter {
    int prefix_size = 0;
    bool operator()(const SelectorItem& a, const SelectorItem& b) const {
        if (a.rank.score != b.rank.score) return a.rank.score > b.rank.score;
        return std::lexicographical_compare(
            a.rank.prefix, a.rank.prefix + prefix_size,
            b.rank.prefix, b.rank.prefix + prefix_size
        );
    }
};

enum class InsertDisposition { Added, Rejected, Replaced };

template <typename Item, typename Better>
InsertDisposition fixed_top_k_insert(
    std::vector<Item>& heap, Item&& candidate, std::size_t width,
    const Better& better, std::int64_t& replacements
) {
    if (heap.size() < width) {
        heap.push_back(std::move(candidate));
        std::push_heap(heap.begin(), heap.end(), better);
        return InsertDisposition::Added;
    }
    if (!better(candidate, heap.front())) return InsertDisposition::Rejected;
    std::pop_heap(heap.begin(), heap.end(), better);
    heap.back() = std::move(candidate);
    std::push_heap(heap.begin(), heap.end(), better);
    ++replacements;
    return InsertDisposition::Replaced;
}

template <typename Item, typename Better>
void finish_fixed_top_k(std::vector<Item>& heap, const Better& better) {
    std::sort(heap.begin(), heap.end(), better);
}

std::size_t owned_bytes(
    const std::vector<Node>& nodes, std::size_t total_agent_capacity
) {
    return nodes.capacity() * sizeof(Node) + total_agent_capacity * sizeof(GA);
}

std::size_t owned_bytes(const Node& node) {
    return sizeof(Node) + node.state.a.capacity() * sizeof(GA);
}

void record_memory(
    HeadroomOutput& output, int depth, const std::vector<Node>& current,
    std::size_t current_agent_capacity, const std::vector<Node>& next,
    std::size_t next_agent_capacity, const Node* transient
) {
    const auto transient_nodes = transient ? std::size_t{1} : std::size_t{0};
    const auto transient_agents = transient ? transient->state.a.capacity() : std::size_t{0};
    const auto current_bytes = owned_bytes(current, current_agent_capacity);
    const auto next_bytes = owned_bytes(next, next_agent_capacity);
    const auto transient_bytes = transient ? owned_bytes(*transient) : std::size_t{0};
    const auto update = [](std::int64_t& target, std::size_t value) {
        target = std::max(target, static_cast<std::int64_t>(value));
    };
    update(output.beam_current_nodes_high_water[depth], current.size());
    update(output.beam_next_nodes_high_water[depth], next.size());
    update(output.beam_transient_nodes_high_water[depth], transient_nodes);
    update(output.beam_live_nodes_high_water[depth], current.size() + next.size() + transient_nodes);
    update(output.beam_current_capacity_high_water[depth], current.capacity());
    update(output.beam_next_capacity_high_water[depth], next.capacity());
    update(output.beam_current_agent_capacity_high_water[depth], current_agent_capacity);
    update(output.beam_next_agent_capacity_high_water[depth], next_agent_capacity);
    update(output.beam_transient_agent_capacity_high_water[depth], transient_agents);
    update(output.beam_current_owned_bytes_high_water[depth], current_bytes);
    update(output.beam_next_owned_bytes_high_water[depth], next_bytes);
    update(output.beam_transient_owned_bytes_high_water[depth], transient_bytes);
    update(
        output.beam_total_owned_bytes_high_water[depth],
        current_bytes + next_bytes + transient_bytes
    );
}

bool fixed_enumerate_rec(
    const GS& state, int token, std::array<bool, 9>& used, GC& command,
    CommandScratch& scratch, std::size_t& count
) {
    if (token == 4) {
        if (count == scratch.size()) return false;
        scratch[count++] = command;
        return true;
    }
    int fixed = 0;
    if (gfixed_token(state, token, fixed)) {
        command.o[token] = fixed;
        return fixed_enumerate_rec(state, token + 1, used, command, scratch, count);
    }
    command.o[token] = G_NULL;
    if (!fixed_enumerate_rec(state, token + 1, used, command, scratch, count)) return false;
    for (const auto& agent : state.a) {
        if (!used[agent.rank] && !genroute(agent)) {
            const auto legality = gcontingency(state, agent, token);
            if (legality.second >= 0) {
                used[agent.rank] = true;
                command.o[token] = agent.rank;
                if (!fixed_enumerate_rec(
                    state, token + 1, used, command, scratch, count
                )) return false;
                used[agent.rank] = false;
            }
        }
    }
    return true;
}

bool fixed_enumerate(const GS& state, CommandScratch& scratch, std::size_t& count) {
    count = 0;
    GC command;
    command.o.fill(G_NULL);
    std::array<bool, 9> used{};
    for (int token = 0; token < 4; ++token) {
        int fixed = 0;
        if (gfixed_token(state, token, fixed)) used[fixed] = true;
    }
    if (!fixed_enumerate_rec(state, 0, used, command, scratch, count)) return false;
    std::sort(
        scratch.begin(), scratch.begin() + count,
        [](const GC& a, const GC& b) { return a.o < b.o; }
    );
    return true;
}

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
        for (int index = 0; index < facts->candidate_count; ++index) {
            all_exact = all_exact && facts->records[index].exact_match;
            output.bcrh_candidate_records[epoch][index] = facts->records[index];
        }
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
    std::vector<Node> retained;
    std::vector<Node> next;
    retained.reserve(static_cast<std::size_t>(width));
    next.reserve(static_cast<std::size_t>(width));
    retained.emplace_back();
    retained[0].state = initial;
    std::size_t retained_agent_capacity = retained[0].state.a.capacity();
    std::size_t next_agent_capacity = 0;
    CommandScratch commands{};
    output.beam_fixed_enumerator_scratch_bytes = sizeof(commands);
    output.beam_conservative_fixed_storage_allowance_bytes =
        sizeof(commands) + sizeof(Node) + sizeof(GC) + sizeof(std::array<bool, 9>);
    for (int depth = 0; depth < 3; ++depth) {
        output.beam_states_before[depth] = static_cast<std::int64_t>(retained.size());
        next.clear();
        next_agent_capacity = 0;
        record_memory(
            output, depth, retained, retained_agent_capacity,
            next, next_agent_capacity, nullptr
        );
        const auto better = [depth](const Node& a, const Node& b) {
            return a.state.af != b.state.af
                ? a.state.af > b.state.af
                : prefix_less(a, b, depth + 1);
        };
        for (const Node& parent : retained) {
            std::size_t command_count = 0;
            if (!fixed_enumerate(parent.state, commands, command_count)) return false;
            output.beam_enumerator_count_high_water[depth] = std::max(
                output.beam_enumerator_count_high_water[depth],
                static_cast<std::int64_t>(command_count)
            );
            output.beam_legal_commands[depth] += static_cast<std::int64_t>(command_count);
            for (std::size_t command_index = 0; command_index < command_count; ++command_index) {
                const GC& command = commands[command_index];
                Node child = parent;
                for (int token = 0; token < 4; ++token) child.prefix[4 * depth + token] = command.o[token];
                if (!advance(child.state, child.safety_violation, input, depth, command)) return false;
                ++output.beam_expansions[depth]; output.beam_native_ticks[depth] += 20;
                record_memory(
                    output, depth, retained, retained_agent_capacity,
                    next, next_agent_capacity, &child
                );
                const auto child_agent_capacity = child.state.a.capacity();
                if (depth == 2) {
                    const auto final_better = [](const Node& a, const Node& b) {
                        return ratio_better(a, b, 3);
                    };
                    const auto evicted_agent_capacity = next.empty()
                        ? std::size_t{0} : next.front().state.a.capacity();
                    const auto disposition = fixed_top_k_insert(
                        next, std::move(child), 1, final_better,
                        output.beam_replacements[depth]
                    );
                    if (disposition == InsertDisposition::Added)
                        next_agent_capacity += child_agent_capacity;
                    else if (disposition == InsertDisposition::Replaced)
                        next_agent_capacity = next_agent_capacity
                            - evicted_agent_capacity + child_agent_capacity;
                } else {
                    const auto evicted_agent_capacity = next.size() < static_cast<std::size_t>(width)
                        ? std::size_t{0} : next.front().state.a.capacity();
                    const auto disposition = fixed_top_k_insert(
                        next, std::move(child), static_cast<std::size_t>(width),
                        better, output.beam_replacements[depth]
                    );
                    if (disposition == InsertDisposition::Added)
                        next_agent_capacity += child_agent_capacity;
                    else if (disposition == InsertDisposition::Replaced)
                        next_agent_capacity = next_agent_capacity
                            - evicted_agent_capacity + child_agent_capacity;
                }
                record_memory(
                    output, depth, retained, retained_agent_capacity,
                    next, next_agent_capacity, nullptr
                );
            }
        }
        if (depth < 2) {
            finish_fixed_top_k(next, better);
            retained.swap(next);
            std::swap(retained_agent_capacity, next_agent_capacity);
            output.beam_states_retained[depth] = static_cast<std::int64_t>(retained.size());
        } else {
            output.beam_states_retained[depth] = next.empty() ? 0 : 1;
        }
    }
    if (next.empty()) return false;
    Node& selected = next.front();
    output.numerator[2] = selected.state.af; output.denominator[2] = selected.state.df;
    for (int index = 0; index < 12; ++index) output.commands[2][index] = selected.prefix[index];
    return complete_lexicographically(selected, input, 2, output);
}

int run(const GEpisodeInput& input, int width, HeadroomOutput& output) {
    std::memset(&output, 0, sizeof(output));
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

BPCR_EXPORT std::size_t vnfc_headroom_sizeof_selector_input() {
    return sizeof(vnfc_headroom::SelectorInput);
}

BPCR_EXPORT std::int32_t vnfc_headroom_select_top_k(
    const vnfc_headroom::SelectorInput* input, std::int32_t count,
    std::int32_t width, std::int32_t prefix_size, std::int32_t* selected_indices,
    std::int32_t* selected_count, std::int64_t* replacements
) {
    if (!input || !selected_indices || !selected_count || !replacements ||
        count <= 0 || count > vnfc_headroom::kMaxCommands || width <= 0 ||
        prefix_size <= 0 || prefix_size > 12) return 1;
    const auto keep = static_cast<std::size_t>(std::min(count, width));
    std::vector<vnfc_headroom::SelectorItem> retained;
    retained.reserve(keep);
    const vnfc_headroom::SelectorBetter better{prefix_size};
    *replacements = 0;
    for (int index = 0; index < count; ++index) {
        vnfc_headroom::SelectorItem item{};
        item.rank = input[index];
        item.source_index = index;
        vnfc_headroom::fixed_top_k_insert(
            retained, std::move(item), keep, better, *replacements
        );
    }
    vnfc_headroom::finish_fixed_top_k(retained, better);
    *selected_count = static_cast<std::int32_t>(retained.size());
    for (std::size_t index = 0; index < retained.size(); ++index)
        selected_indices[index] = retained[index].source_index;
    return 0;
}
