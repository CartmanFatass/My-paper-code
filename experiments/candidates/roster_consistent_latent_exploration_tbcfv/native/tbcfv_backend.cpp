#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <new>
#include <unordered_set>
#include <vector>

#if defined(_WIN32)
#define TBCFV_EXPORT extern "C" __declspec(dllexport)
#else
#define TBCFV_EXPORT extern "C"
#endif

namespace {

constexpr std::uint64_t MAGIC = UINT64_C(0x52434c4554424347);
constexpr std::int32_t ABI = 2;
constexpr int SECTORS = 120;
constexpr int BEACONS = 6;
constexpr int MAX_AGENTS = 12;
constexpr int MIN_AGENTS = 6;
constexpr int HORIZON = 64;
constexpr int EVENT_TICK = 24;
constexpr int CLAIM_PERIOD = 4;
constexpr int ACTIVE_CONTINUATION = 0;
constexpr int NEW_EPOCH = 1;
constexpr int EVENT_POSITION = -2;

struct FixtureInput {
    std::uint64_t magic;
    std::int32_t abi;
    std::int32_t initial_n;
    std::int32_t after_n;
    std::int32_t event_condition;
    std::int32_t omega_plus;
    std::int32_t kappa_plus;
    std::int32_t initial_keys[MAX_AGENTS];
    std::int32_t initial_positions[MAX_AGENTS];
    std::int32_t after_keys[MAX_AGENTS];
    std::int32_t after_positions[MAX_AGENTS];
};

struct StepInput {
    std::uint64_t magic;
    std::int32_t abi;
    std::int32_t claim_count;
    std::int32_t claims[MAX_AGENTS];
};

struct EventInput {
    std::uint64_t magic;
    std::int32_t abi;
    std::int32_t newcomer_count;
    std::int32_t newcomer_positions[MAX_AGENTS];
};

struct Snapshot {
    std::int32_t status;
    std::int32_t terminal;
    std::int32_t tick;
    std::int32_t agent_count;
    std::int32_t event_input_required;
    std::int32_t claim_required;
    std::int32_t roster_event;
    std::int32_t new_epoch;
    std::int32_t positions[MAX_AGENTS];
    // Runtime row-linkage metadata only.  It is never an actor/model feature.
    std::int32_t transport_keys[MAX_AGENTS];
    std::int32_t angular_ranks[MAX_AGENTS];
    std::int32_t previous_displacements[MAX_AGENTS];
    std::int32_t newcomers[MAX_AGENTS];
    std::int32_t current_claims[MAX_AGENTS];
    std::int32_t beacon_positions[BEACONS];
    std::int32_t demands[BEACONS];
    std::int32_t last_coverage[BEACONS];
    std::int32_t tau;
    double last_u;
    double last_fragmentation;
    double accumulated_u;
    double accumulated_post_u;
    double accumulated_fragmentation;
    double endpoint_u;
    double endpoint_f;
    double endpoint_y;
};

struct Agent {
    int key = -1;
    int position = -1;
    int previous_displacement = 0;
    bool newcomer = false;
    int claim = -1;
    int entry_order = -1;
};

struct Host {
    FixtureInput fixture{};
    int tick = 0;
    bool terminal = false;
    int omega = 0;
    int kappa = 0;
    bool roster_event = false;
    bool new_epoch = false;
    bool event_input_required = false;
    std::vector<Agent> agents;
    double sum_u = 0.0;
    double sum_post_u = 0.0;
    double sum_fragmentation = 0.0;
    int post_claim_count = 0;
    int zero_run = 0;
    int tau = -1;
    double last_u = -1.0;
    double last_fragmentation = -1.0;
    std::array<int, BEACONS> last_coverage{};
};

std::mutex registry_mutex;
std::unordered_set<Host*> live_hosts;

bool supported_width(int width) {
    return width == 1 || width == 8 || width == 32;
}

bool contains(const int* values, int count, int needle) {
    for (int index = 0; index < count; ++index) {
        if (values[index] == needle) return true;
    }
    return false;
}

int validate_fixture(const FixtureInput& input) {
    if (input.magic != MAGIC || input.abi != ABI) return -10;
    if (input.initial_n < MIN_AGENTS || input.initial_n > MAX_AGENTS ||
        input.after_n < MIN_AGENTS || input.after_n > MAX_AGENTS) return -11;
    if (input.event_condition == ACTIVE_CONTINUATION) {
        if (input.omega_plus != 0 || input.kappa_plus != 0) return -12;
    } else if (input.event_condition == NEW_EPOCH) {
        if (!(input.omega_plus == 5 || input.omega_plus == 10 || input.omega_plus == 15) ||
            input.kappa_plus < 1 || input.kappa_plus > 5) return -12;
    } else {
        return -12;
    }
    for (int index = 0; index < MAX_AGENTS; ++index) {
        const bool initial_live = index < input.initial_n;
        const bool after_live = index < input.after_n;
        if (!initial_live && (input.initial_keys[index] != -1 || input.initial_positions[index] != -1)) return -13;
        if (!after_live && (input.after_keys[index] != -1 || input.after_positions[index] != -1)) return -13;
        if (initial_live) {
            if (input.initial_keys[index] < 0 || input.initial_positions[index] < 0 || input.initial_positions[index] >= SECTORS) return -14;
            for (int prior = 0; prior < index; ++prior) {
                if (input.initial_keys[prior] == input.initial_keys[index] ||
                    input.initial_positions[prior] == input.initial_positions[index]) return -15;
            }
        }
        if (after_live) {
            if (input.after_keys[index] < 0) return -14;
            for (int prior = 0; prior < index; ++prior) {
                if (input.after_keys[prior] == input.after_keys[index]) return -15;
            }
            const bool survivor = contains(input.initial_keys, input.initial_n, input.after_keys[index]);
            if (survivor) {
                if (input.after_positions[index] != -1) return -16;
            } else {
                if (input.after_positions[index] != EVENT_POSITION) return -16;
            }
        }
    }
    if (input.after_n > input.initial_n) {
        for (int index = 0; index < input.initial_n; ++index) {
            if (!contains(input.after_keys, input.after_n, input.initial_keys[index])) return -17;
        }
    } else if (input.after_n < input.initial_n) {
        for (int index = 0; index < input.after_n; ++index) {
            if (!contains(input.initial_keys, input.initial_n, input.after_keys[index])) return -17;
        }
    } else {
        for (int index = 0; index < input.initial_n; ++index) {
            if (input.initial_keys[index] != input.after_keys[index]) return -17;
        }
    }
    return 0;
}

std::vector<int> order(const Host& host) {
    std::vector<int> result(host.agents.size());
    for (std::size_t index = 0; index < host.agents.size(); ++index) result[index] = static_cast<int>(index);
    std::sort(result.begin(), result.end(), [&](int left, int right) {
        const Agent& a = host.agents[static_cast<std::size_t>(left)];
        const Agent& b = host.agents[static_cast<std::size_t>(right)];
        if (a.position != b.position) return a.position < b.position;
        return a.entry_order < b.entry_order;
    });
    return result;
}

std::array<int, BEACONS> beacons(const Host& host, int requested_tick = -1) {
    const int tick = requested_tick >= 0 ? requested_tick : std::min(host.tick, HORIZON - 1);
    std::array<int, BEACONS> result{};
    for (int index = 0; index < BEACONS; ++index) result[index] = (20 * index + tick / 4 + host.omega) % SECTORS;
    return result;
}

std::array<int, BEACONS> demands(const Host& host, int requested_tick = -1) {
    const int tick = requested_tick >= 0 ? requested_tick : std::min(host.tick, HORIZON - 1);
    const int n = static_cast<int>(host.agents.size());
    const int base = n / BEACONS;
    const int remainder = n % BEACONS;
    const int phase = (tick / 8 + host.kappa) % BEACONS;
    std::array<int, BEACONS> result{};
    result.fill(base);
    for (int offset = 0; offset < remainder; ++offset) result[(phase + offset) % BEACONS] += 1;
    return result;
}

Snapshot snapshot(const Host& host) {
    Snapshot output{};
    output.status = 0;
    output.terminal = host.terminal ? 1 : 0;
    output.tick = host.tick;
    output.agent_count = static_cast<int>(host.agents.size());
    output.event_input_required = (!host.terminal && host.event_input_required) ? 1 : 0;
    output.claim_required = (!host.terminal && !host.event_input_required && host.tick % CLAIM_PERIOD == 0) ? 1 : 0;
    output.roster_event = (!host.terminal && host.roster_event) ? 1 : 0;
    output.new_epoch = (!host.terminal && host.new_epoch) ? 1 : 0;
    std::fill(std::begin(output.positions), std::end(output.positions), -1);
    std::fill(std::begin(output.transport_keys), std::end(output.transport_keys), -1);
    std::fill(std::begin(output.angular_ranks), std::end(output.angular_ranks), -1);
    std::fill(std::begin(output.previous_displacements), std::end(output.previous_displacements), 0);
    std::fill(std::begin(output.newcomers), std::end(output.newcomers), 0);
    std::fill(std::begin(output.current_claims), std::end(output.current_claims), -1);
    const std::vector<int> sorted = order(host);
    for (std::size_t rank = 0; rank < sorted.size(); ++rank) {
        const Agent& agent = host.agents[static_cast<std::size_t>(sorted[rank])];
        output.positions[rank] = agent.position;
        output.transport_keys[rank] = agent.key;
        output.angular_ranks[rank] = static_cast<int>(rank);
        output.previous_displacements[rank] = agent.previous_displacement;
        output.newcomers[rank] = agent.newcomer ? 1 : 0;
        output.current_claims[rank] = agent.claim;
    }
    const auto q = beacons(host);
    const auto d = demands(host);
    for (int index = 0; index < BEACONS; ++index) {
        output.beacon_positions[index] = q[index];
        output.demands[index] = d[index];
        output.last_coverage[index] = host.last_coverage[static_cast<std::size_t>(index)];
    }
    output.tau = host.terminal ? host.tau : -1;
    output.last_u = host.last_u;
    output.last_fragmentation = host.last_fragmentation;
    output.accumulated_u = host.sum_u;
    output.accumulated_post_u = host.sum_post_u;
    output.accumulated_fragmentation = host.sum_fragmentation;
    output.endpoint_u = host.terminal ? host.sum_post_u / 40.0 : -1.0;
    output.endpoint_f = host.terminal ? host.sum_fragmentation / 10.0 : -1.0;
    output.endpoint_y = host.terminal ? 1.0 - host.sum_u / 64.0 : -1.0;
    return output;
}

int validate_action(const Host& host, const StepInput& input) {
    if (input.magic != MAGIC || input.abi != ABI) return -20;
    if (host.terminal) return -21;
    if (host.event_input_required) return -26;
    const int expected = host.tick % CLAIM_PERIOD == 0 ? static_cast<int>(host.agents.size()) : 0;
    if (input.claim_count != expected) return -22;
    for (int index = 0; index < MAX_AGENTS; ++index) {
        if (index < expected) {
            if (input.claims[index] < 0 || input.claims[index] >= BEACONS) return -23;
        } else if (input.claims[index] != -1) {
            return -23;
        }
    }
    return 0;
}

int expected_newcomers(const Host& host) {
    int result = 0;
    for (int row = 0; row < host.fixture.after_n; ++row) {
        if (!contains(host.fixture.initial_keys, host.fixture.initial_n, host.fixture.after_keys[row])) result += 1;
    }
    return result;
}

int validate_event(const Host& host, const EventInput& input) {
    if (input.magic != MAGIC || input.abi != ABI) return -30;
    if (host.terminal || host.tick != EVENT_TICK || !host.event_input_required) return -31;
    const int expected = expected_newcomers(host);
    if (input.newcomer_count != expected) return -32;
    for (int index = 0; index < MAX_AGENTS; ++index) {
        if (index < expected) {
            const int position = input.newcomer_positions[index];
            if (position < 0 || position >= SECTORS) return -33;
            for (int prior = 0; prior < index; ++prior) {
                if (input.newcomer_positions[prior] == position) return -33;
            }
            for (const Agent& agent : host.agents) {
                if (contains(host.fixture.after_keys, host.fixture.after_n, agent.key) && agent.position == position) return -33;
            }
        } else if (input.newcomer_positions[index] != -1) {
            return -33;
        }
    }
    return 0;
}

int install_boundary(Host& host, const EventInput& input) {
    const FixtureInput& fixture = host.fixture;
    std::vector<Agent> replacement;
    replacement.reserve(static_cast<std::size_t>(fixture.after_n));
    int next_entry = 0;
    int newcomer_index = 0;
    for (const Agent& agent : host.agents) next_entry = std::max(next_entry, agent.entry_order + 1);
    for (int row = 0; row < fixture.after_n; ++row) {
        const int key = fixture.after_keys[row];
        auto survivor = std::find_if(host.agents.begin(), host.agents.end(), [&](const Agent& agent) { return agent.key == key; });
        if (survivor != host.agents.end()) {
            Agent retained = *survivor;
            retained.newcomer = false;
            replacement.push_back(retained);
        } else {
            replacement.push_back(Agent{key, input.newcomer_positions[newcomer_index++], 0, true, -1, next_entry++});
        }
    }
    for (std::size_t left = 0; left < replacement.size(); ++left) {
        const bool left_new = !contains(fixture.initial_keys, fixture.initial_n, replacement[left].key);
        if (!left_new) continue;
        for (std::size_t right = 0; right < replacement.size(); ++right) {
            if (left == right) continue;
            if (replacement[left].position == replacement[right].position) return -24;
        }
    }
    host.agents = std::move(replacement);
    host.roster_event = fixture.initial_n != fixture.after_n;
    host.new_epoch = fixture.event_condition == NEW_EPOCH;
    if (host.new_epoch) {
        host.omega = fixture.omega_plus;
        host.kappa = fixture.kappa_plus;
    }
    host.event_input_required = false;
    return 0;
}

int prepare_tick(Host& host) {
    host.roster_event = false;
    host.new_epoch = false;
    for (Agent& agent : host.agents) agent.newcomer = false;
    if (host.tick == EVENT_TICK) host.event_input_required = true;
    return 0;
}

int movement(int position, int target) {
    const int clockwise = (target - position + SECTORS) % SECTORS;
    if (clockwise <= SECTORS / 2) return std::min(3, clockwise);
    return -std::min(3, SECTORS - clockwise);
}

int step_one(Host& host, const StepInput& input) {
    const int action_status = validate_action(host, input);
    if (action_status != 0) return action_status;
    const bool claim_required = host.tick % CLAIM_PERIOD == 0;
    const std::vector<int> sorted = order(host);
    if (claim_required) {
        for (std::size_t rank = 0; rank < sorted.size(); ++rank) {
            host.agents[static_cast<std::size_t>(sorted[rank])].claim = input.claims[rank];
        }
    }
    const auto q = beacons(host, host.tick);
    const auto d = demands(host, host.tick);
    for (Agent& agent : host.agents) {
        if (agent.claim < 0 || agent.claim >= BEACONS) return -25;
        const int displacement = movement(agent.position, q[static_cast<std::size_t>(agent.claim)]);
        agent.position = (agent.position + displacement + SECTORS) % SECTORS;
        agent.previous_displacement = displacement;
    }
    std::array<int, BEACONS> coverage{};
    for (int beacon = 0; beacon < BEACONS; ++beacon) {
        for (const Agent& agent : host.agents) {
            const int raw = std::abs(agent.position - q[static_cast<std::size_t>(beacon)]);
            if (std::min(raw, SECTORS - raw) <= 2) coverage[static_cast<std::size_t>(beacon)] += 1;
        }
    }
    int unserved_units = 0;
    for (int beacon = 0; beacon < BEACONS; ++beacon) {
        unserved_units += std::max(d[static_cast<std::size_t>(beacon)] - coverage[static_cast<std::size_t>(beacon)], 0);
    }
    const double u = static_cast<double>(unserved_units) / static_cast<double>(host.agents.size());
    host.sum_u += u;
    host.last_u = u;
    host.last_coverage = coverage;
    host.last_fragmentation = -1.0;
    if (host.tick >= EVENT_TICK) {
        host.sum_post_u += u;
        if (u == 0.0) {
            host.zero_run += 1;
            if (host.zero_run == 4 && host.tau < 0) {
                const int start = host.tick - 3 - EVENT_TICK;
                if (start >= 0 && start <= 36) host.tau = start;
            }
        } else {
            host.zero_run = 0;
        }
        if (claim_required) {
            std::array<int, BEACONS> counts{};
            for (const Agent& agent : host.agents) counts[static_cast<std::size_t>(agent.claim)] += 1;
            int shortfall = 0;
            for (int beacon = 0; beacon < BEACONS; ++beacon) {
                shortfall += std::max(d[static_cast<std::size_t>(beacon)] - counts[static_cast<std::size_t>(beacon)], 0);
            }
            host.last_fragmentation = static_cast<double>(shortfall) / static_cast<double>(host.agents.size());
            host.sum_fragmentation += host.last_fragmentation;
            host.post_claim_count += 1;
        }
    }
    host.tick += 1;
    if (host.tick == HORIZON) {
        host.terminal = true;
        if (host.tau < 0) host.tau = 40;
    } else {
        const int status = prepare_tick(host);
        if (status != 0) return status;
    }
    return 0;
}

std::unique_ptr<Host> make_host(const FixtureInput& fixture) {
    auto host = std::make_unique<Host>();
    host->fixture = fixture;
    host->agents.reserve(static_cast<std::size_t>(fixture.initial_n));
    for (int index = 0; index < fixture.initial_n; ++index) {
        host->agents.push_back(Agent{fixture.initial_keys[index], fixture.initial_positions[index], 0, false, -1, index});
    }
    return host;
}

}  // namespace

TBCFV_EXPORT std::int32_t rcle_tbcfv_abi_version() { return ABI; }
TBCFV_EXPORT std::uint64_t rcle_tbcfv_fixture_magic() { return MAGIC; }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_fixture_input() { return sizeof(FixtureInput); }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_step_input() { return sizeof(StepInput); }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_event_input() { return sizeof(EventInput); }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_snapshot() { return sizeof(Snapshot); }

TBCFV_EXPORT std::int32_t rcle_tbcfv_reset_batch(
    const FixtureInput* inputs, std::int32_t width, void** handles, Snapshot* outputs) {
    if (!supported_width(width)) return -1;
    if (inputs == nullptr || handles == nullptr || outputs == nullptr) return -2;
    for (int index = 0; index < width; ++index) {
        if (handles[index] != nullptr) return -3;
        const int status = validate_fixture(inputs[index]);
        if (status != 0) return status;
    }
    try {
        std::vector<std::unique_ptr<Host>> pending;
        pending.reserve(static_cast<std::size_t>(width));
        std::vector<Snapshot> snapshots;
        snapshots.reserve(static_cast<std::size_t>(width));
        for (int index = 0; index < width; ++index) {
            pending.push_back(make_host(inputs[index]));
            snapshots.push_back(snapshot(*pending.back()));
        }
        std::lock_guard<std::mutex> lock(registry_mutex);
        for (int index = 0; index < width; ++index) {
            Host* host = pending[static_cast<std::size_t>(index)].release();
            live_hosts.insert(host);
            handles[index] = host;
            outputs[index] = snapshots[static_cast<std::size_t>(index)];
        }
    } catch (const std::bad_alloc&) {
        return -9;
    }
    return 0;
}

TBCFV_EXPORT std::int32_t rcle_tbcfv_step_batch(
    void** handles, const StepInput* inputs, std::int32_t width, Snapshot* outputs) {
    if (!supported_width(width)) return -1;
    if (handles == nullptr || inputs == nullptr || outputs == nullptr) return -2;
    std::lock_guard<std::mutex> lock(registry_mutex);
    std::unordered_set<Host*> seen;
    std::vector<Host> trials;
    trials.reserve(static_cast<std::size_t>(width));
    for (int index = 0; index < width; ++index) {
        Host* host = static_cast<Host*>(handles[index]);
        if (host == nullptr || live_hosts.find(host) == live_hosts.end() || !seen.insert(host).second) return -4;
        const int status = validate_action(*host, inputs[index]);
        if (status != 0) return status;
        trials.push_back(*host);
    }
    std::vector<Snapshot> snapshots;
    snapshots.reserve(static_cast<std::size_t>(width));
    for (int index = 0; index < width; ++index) {
        const int status = step_one(trials[static_cast<std::size_t>(index)], inputs[index]);
        if (status != 0) return status;
        snapshots.push_back(snapshot(trials[static_cast<std::size_t>(index)]));
    }
    for (int index = 0; index < width; ++index) {
        *static_cast<Host*>(handles[index]) = std::move(trials[static_cast<std::size_t>(index)]);
        outputs[index] = snapshots[static_cast<std::size_t>(index)];
    }
    return 0;
}

TBCFV_EXPORT std::int32_t rcle_tbcfv_apply_event_batch(
    void** handles, const EventInput* inputs, std::int32_t width, Snapshot* outputs) {
    if (!supported_width(width)) return -1;
    if (handles == nullptr || inputs == nullptr || outputs == nullptr) return -2;
    std::lock_guard<std::mutex> lock(registry_mutex);
    std::unordered_set<Host*> seen;
    std::vector<Host> trials;
    trials.reserve(static_cast<std::size_t>(width));
    for (int index = 0; index < width; ++index) {
        Host* host = static_cast<Host*>(handles[index]);
        if (host == nullptr || live_hosts.find(host) == live_hosts.end() || !seen.insert(host).second) return -4;
        const int status = validate_event(*host, inputs[index]);
        if (status != 0) return status;
        trials.push_back(*host);
    }
    std::vector<Snapshot> snapshots;
    snapshots.reserve(static_cast<std::size_t>(width));
    for (int index = 0; index < width; ++index) {
        const int status = install_boundary(trials[static_cast<std::size_t>(index)], inputs[index]);
        if (status != 0) return status;
        snapshots.push_back(snapshot(trials[static_cast<std::size_t>(index)]));
    }
    for (int index = 0; index < width; ++index) {
        *static_cast<Host*>(handles[index]) = std::move(trials[static_cast<std::size_t>(index)]);
        outputs[index] = snapshots[static_cast<std::size_t>(index)];
    }
    return 0;
}

TBCFV_EXPORT std::int32_t rcle_tbcfv_close_batch(void** handles, std::int32_t width) {
    if (!supported_width(width)) return -1;
    if (handles == nullptr) return -2;
    std::lock_guard<std::mutex> lock(registry_mutex);
    std::unordered_set<Host*> seen;
    for (int index = 0; index < width; ++index) {
        Host* host = static_cast<Host*>(handles[index]);
        if (host == nullptr || live_hosts.find(host) == live_hosts.end() || !seen.insert(host).second) return -4;
    }
    for (int index = 0; index < width; ++index) {
        Host* host = static_cast<Host*>(handles[index]);
        live_hosts.erase(host);
        delete host;
        handles[index] = nullptr;
    }
    return 0;
}
