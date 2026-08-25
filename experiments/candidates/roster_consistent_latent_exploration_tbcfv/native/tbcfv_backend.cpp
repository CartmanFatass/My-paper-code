#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <functional>
#include <memory>
#include <mutex>
#include <new>
#include <string>
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

const char* CELL_NAMES[16] = {
    "6_to_6.ACTIVE_CONTINUATION", "6_to_6.NEW_EPOCH",
    "10_to_10.ACTIVE_CONTINUATION", "10_to_10.NEW_EPOCH",
    "6_to_10.ACTIVE_CONTINUATION", "6_to_10.NEW_EPOCH",
    "10_to_6.ACTIVE_CONTINUATION", "10_to_6.NEW_EPOCH",
    "8_to_8.ACTIVE_CONTINUATION", "8_to_8.NEW_EPOCH",
    "12_to_12.ACTIVE_CONTINUATION", "12_to_12.NEW_EPOCH",
    "8_to_12.ACTIVE_CONTINUATION", "8_to_12.NEW_EPOCH",
    "12_to_8.ACTIVE_CONTINUATION", "12_to_8.NEW_EPOCH"};
constexpr int CELL_BEFORE[16] = {6,6,10,10,6,6,10,10,8,8,12,12,8,8,12,12};
constexpr int CELL_AFTER[16] = {6,6,10,10,10,10,6,6,8,8,12,12,12,12,8,8};

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

// Candidate-local semantic-address acceleration.  This structure contains
// only the exact public semantic address fields; it never contains a model,
// coordinate root, result value, or mutable host state.  The two tagged fields
// preserve the frozen JSON distinction between an integer and a string.
struct SemanticAddressInput {
    std::int64_t run_block;
    const char* parameter_entry;
    const char* arm_only_variable;
    const char* cell;
    std::int64_t update_or_scenario;
    std::int64_t physical_tick;
    std::int64_t roster_event_integer;
    const char* roster_event_string;
    std::int32_t roster_event_is_integer;
    std::int64_t physical_agent_integer;
    const char* physical_agent_string;
    std::int32_t physical_agent_is_integer;
    const char* draw_kind;
    std::int64_t draw_index;
};

struct Sha256 {
    std::uint32_t state[8] = {
        UINT32_C(0x6a09e667), UINT32_C(0xbb67ae85), UINT32_C(0x3c6ef372), UINT32_C(0xa54ff53a),
        UINT32_C(0x510e527f), UINT32_C(0x9b05688c), UINT32_C(0x1f83d9ab), UINT32_C(0x5be0cd19)};
    std::uint8_t block[64]{};
    std::size_t used = 0;
    std::uint64_t bytes = 0;
};

constexpr std::uint32_t SHA256_K[64] = {
    0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
    0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
    0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
    0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
    0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
    0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
    0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
    0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u};

std::uint32_t rotate_right(std::uint32_t value, int bits) {
    return (value >> bits) | (value << (32 - bits));
}

void sha256_transform(Sha256& sha, const std::uint8_t* input) {
    std::uint32_t words[64]{};
    for (int index = 0; index < 16; ++index) {
        const int offset = index * 4;
        words[index] = (static_cast<std::uint32_t>(input[offset]) << 24) |
                       (static_cast<std::uint32_t>(input[offset + 1]) << 16) |
                       (static_cast<std::uint32_t>(input[offset + 2]) << 8) |
                       static_cast<std::uint32_t>(input[offset + 3]);
    }
    for (int index = 16; index < 64; ++index) {
        const std::uint32_t s0 = rotate_right(words[index - 15], 7) ^
                                 rotate_right(words[index - 15], 18) ^
                                 (words[index - 15] >> 3);
        const std::uint32_t s1 = rotate_right(words[index - 2], 17) ^
                                 rotate_right(words[index - 2], 19) ^
                                 (words[index - 2] >> 10);
        words[index] = words[index - 16] + s0 + words[index - 7] + s1;
    }
    std::uint32_t a = sha.state[0], b = sha.state[1], c = sha.state[2], d = sha.state[3];
    std::uint32_t e = sha.state[4], f = sha.state[5], g = sha.state[6], h = sha.state[7];
    for (int index = 0; index < 64; ++index) {
        const std::uint32_t s1 = rotate_right(e, 6) ^ rotate_right(e, 11) ^ rotate_right(e, 25);
        const std::uint32_t choice = (e & f) ^ ((~e) & g);
        const std::uint32_t temp1 = h + s1 + choice + SHA256_K[index] + words[index];
        const std::uint32_t s0 = rotate_right(a, 2) ^ rotate_right(a, 13) ^ rotate_right(a, 22);
        const std::uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        const std::uint32_t temp2 = s0 + majority;
        h = g; g = f; f = e; e = d + temp1; d = c; c = b; b = a; a = temp1 + temp2;
    }
    sha.state[0] += a; sha.state[1] += b; sha.state[2] += c; sha.state[3] += d;
    sha.state[4] += e; sha.state[5] += f; sha.state[6] += g; sha.state[7] += h;
}

void sha256_update(Sha256& sha, const std::uint8_t* input, std::size_t size) {
    sha.bytes += size;
    while (size > 0) {
        const std::size_t amount = std::min(size, sizeof(sha.block) - sha.used);
        std::memcpy(sha.block + sha.used, input, amount);
        sha.used += amount; input += amount; size -= amount;
        if (sha.used == sizeof(sha.block)) {
            sha256_transform(sha, sha.block);
            sha.used = 0;
        }
    }
}

void sha256_finish(Sha256& sha, std::uint8_t output[32]) {
    const std::uint64_t bit_count = sha.bytes * 8;
    sha.block[sha.used++] = 0x80;
    if (sha.used > 56) {
        while (sha.used < 64) sha.block[sha.used++] = 0;
        sha256_transform(sha, sha.block);
        sha.used = 0;
    }
    while (sha.used < 56) sha.block[sha.used++] = 0;
    for (int shift = 56; shift >= 0; shift -= 8) {
        sha.block[sha.used++] = static_cast<std::uint8_t>(bit_count >> shift);
    }
    sha256_transform(sha, sha.block);
    for (int index = 0; index < 8; ++index) {
        output[index * 4] = static_cast<std::uint8_t>(sha.state[index] >> 24);
        output[index * 4 + 1] = static_cast<std::uint8_t>(sha.state[index] >> 16);
        output[index * 4 + 2] = static_cast<std::uint8_t>(sha.state[index] >> 8);
        output[index * 4 + 3] = static_cast<std::uint8_t>(sha.state[index]);
    }
}

void hmac_sha256(const std::uint8_t key[32], const std::string& payload, std::uint8_t output[32]) {
    std::uint8_t inner_pad[64], outer_pad[64], inner_digest[32];
    for (int index = 0; index < 64; ++index) {
        const std::uint8_t value = index < 32 ? key[index] : 0;
        inner_pad[index] = static_cast<std::uint8_t>(value ^ 0x36);
        outer_pad[index] = static_cast<std::uint8_t>(value ^ 0x5c);
    }
    Sha256 inner;
    sha256_update(inner, inner_pad, sizeof(inner_pad));
    sha256_update(inner, reinterpret_cast<const std::uint8_t*>(payload.data()), payload.size());
    sha256_finish(inner, inner_digest);
    Sha256 outer;
    sha256_update(outer, outer_pad, sizeof(outer_pad));
    sha256_update(outer, inner_digest, sizeof(inner_digest));
    sha256_finish(outer, output);
}

bool safe_json_string(const char* value) {
    if (value == nullptr) return false;
    for (const unsigned char* cursor = reinterpret_cast<const unsigned char*>(value); *cursor; ++cursor) {
        if (*cursor < 0x20 || *cursor >= 0x7f || *cursor == '"' || *cursor == '\\') return false;
    }
    return true;
}

void append_json_string(std::string& output, const char* value) {
    output.push_back('"'); output.append(value); output.push_back('"');
}

bool semantic_payload(const SemanticAddressInput& input, std::string& output) {
    if (!safe_json_string(input.parameter_entry) || !safe_json_string(input.arm_only_variable) ||
        !safe_json_string(input.cell) || !safe_json_string(input.draw_kind)) return false;
    if ((!input.roster_event_is_integer && !safe_json_string(input.roster_event_string)) ||
        (!input.physical_agent_is_integer && !safe_json_string(input.physical_agent_string))) return false;
    output.clear();
    output.reserve(384);
    output.append("{\"arm_only_variable\":"); append_json_string(output, input.arm_only_variable);
    output.append(",\"cell\":"); append_json_string(output, input.cell);
    output.append(",\"domain\":\"RCLE-TBCFV-R04/semantic-uniform/v1\"");
    output.append(",\"draw_index\":").append(std::to_string(input.draw_index));
    output.append(",\"draw_kind\":"); append_json_string(output, input.draw_kind);
    output.append(",\"parameter_entry\":"); append_json_string(output, input.parameter_entry);
    output.append(",\"physical_agent\":");
    if (input.physical_agent_is_integer) output.append(std::to_string(input.physical_agent_integer));
    else append_json_string(output, input.physical_agent_string);
    output.append(",\"physical_tick\":").append(std::to_string(input.physical_tick));
    output.append(",\"roster_event\":");
    if (input.roster_event_is_integer) output.append(std::to_string(input.roster_event_integer));
    else append_json_string(output, input.roster_event_string);
    output.append(",\"run_block\":").append(std::to_string(input.run_block));
    output.append(",\"update_or_scenario\":").append(std::to_string(input.update_or_scenario));
    output.append("}\n");
    return true;
}

std::uint64_t semantic_word(
    const std::uint8_t key[32], const SemanticAddressInput& address, std::string& payload) {
    std::uint8_t digest[32];
    if (!semantic_payload(address, payload)) return UINT64_MAX;
    hmac_sha256(key, payload, digest);
    std::uint64_t word = 0;
    for (int byte = 0; byte < 8; ++byte) word = (word << 8) | digest[byte];
    return word;
}

double semantic_uniform(
    const std::uint8_t key[32], const SemanticAddressInput& address, std::string& payload) {
    constexpr double WORD_SCALE = 1.0 / 18446744073709551616.0;
    return (static_cast<double>(semantic_word(key, address, payload)) + 0.5) * WORD_SCALE;
}

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

int circular_distance(int left, int right) {
    const int delta = std::abs(left - right) % SECTORS;
    return std::min(delta, SECTORS - delta);
}

struct Assignment {
    bool valid = false;
    int distance = 0;
    int changes = 0;
    std::vector<int> slots;
};

bool assignment_less(const Assignment& left, const Assignment& right) {
    if (!right.valid) return true;
    if (left.distance != right.distance) return left.distance < right.distance;
    if (left.changes != right.changes) return left.changes < right.changes;
    return left.slots < right.slots;
}

int coherent_actions(
    const Snapshot& snapshot_row,
    const std::int32_t* previous,
    const std::uint8_t* survivor,
    bool first_or_epoch,
    std::int32_t* output) {
    const int n = snapshot_row.agent_count;
    if (n < 1 || n > MAX_AGENTS) return -40;
    std::vector<int> angular(static_cast<std::size_t>(n));
    for (int index = 0; index < n; ++index) angular[static_cast<std::size_t>(index)] = index;
    std::sort(angular.begin(), angular.end(), [&](int left, int right) {
        if (snapshot_row.positions[left] != snapshot_row.positions[right])
            return snapshot_row.positions[left] < snapshot_row.positions[right];
        return snapshot_row.transport_keys[left] < snapshot_row.transport_keys[right];
    });
    std::vector<int> slots;
    slots.reserve(static_cast<std::size_t>(n));
    for (int beacon = 0; beacon < BEACONS; ++beacon) {
        if (snapshot_row.demands[beacon] < 0) return -41;
        for (int count = 0; count < snapshot_row.demands[beacon]; ++count) slots.push_back(beacon);
    }
    if (static_cast<int>(slots.size()) != n) return -41;
    const int mask_count = 1 << n;
    std::vector<Assignment> memo(static_cast<std::size_t>((n + 1) * mask_count));
    std::vector<std::uint8_t> seen(static_cast<std::size_t>((n + 1) * mask_count), 0);
    std::function<const Assignment&(int,int)> solve = [&](int rank, int mask) -> const Assignment& {
        const std::size_t memo_index = static_cast<std::size_t>(rank * mask_count + mask);
        if (seen[memo_index]) return memo[memo_index];
        seen[memo_index] = 1;
        Assignment& best = memo[memo_index];
        if (rank == n) { best.valid = true; return best; }
        const int agent = angular[static_cast<std::size_t>(rank)];
        for (int slot_index = 0; slot_index < n; ++slot_index) {
            if (mask & (1 << slot_index)) continue;
            const Assignment& tail = solve(rank + 1, mask | (1 << slot_index));
            if (!tail.valid) continue;
            Assignment candidate;
            candidate.valid = true;
            candidate.distance = circular_distance(
                snapshot_row.positions[agent], snapshot_row.beacon_positions[slots[static_cast<std::size_t>(slot_index)]]) + tail.distance;
            candidate.changes =
                ((!first_or_epoch && survivor[agent] && previous[agent] >= 0 &&
                  previous[agent] != slots[static_cast<std::size_t>(slot_index)]) ? 1 : 0) + tail.changes;
            candidate.slots.reserve(static_cast<std::size_t>(n - rank));
            candidate.slots.push_back(slot_index);
            candidate.slots.insert(candidate.slots.end(), tail.slots.begin(), tail.slots.end());
            if (assignment_less(candidate, best)) best = std::move(candidate);
        }
        return best;
    };
    const Assignment& chosen = solve(0, 0);
    if (!chosen.valid || static_cast<int>(chosen.slots.size()) != n) return -42;
    for (int rank = 0; rank < n; ++rank) {
        const int agent = angular[static_cast<std::size_t>(rank)];
        output[agent] = slots[static_cast<std::size_t>(chosen.slots[static_cast<std::size_t>(rank)])];
    }
    return 0;
}

}  // namespace

TBCFV_EXPORT std::int32_t rcle_tbcfv_abi_version() { return ABI; }
TBCFV_EXPORT std::uint64_t rcle_tbcfv_fixture_magic() { return MAGIC; }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_fixture_input() { return sizeof(FixtureInput); }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_step_input() { return sizeof(StepInput); }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_event_input() { return sizeof(EventInput); }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_snapshot() { return sizeof(Snapshot); }
TBCFV_EXPORT std::size_t rcle_tbcfv_sizeof_semantic_address_input() { return sizeof(SemanticAddressInput); }

TBCFV_EXPORT std::int32_t rcle_tbcfv_semantic_uniform_words(
    const std::uint8_t* key,
    const SemanticAddressInput* inputs,
    std::int32_t count,
    std::uint64_t* outputs) {
    if (key == nullptr || inputs == nullptr || outputs == nullptr || count < 1 || count > 65536) return -30;
    std::string payload;
    std::uint8_t digest[32];
    for (int index = 0; index < count; ++index) {
        if (!semantic_payload(inputs[index], payload)) return -31;
        hmac_sha256(key, payload, digest);
        std::uint64_t word = 0;
        for (int byte = 0; byte < 8; ++byte) word = (word << 8) | digest[byte];
        outputs[index] = word;
    }
    return 0;
}

TBCFV_EXPORT std::int32_t rcle_tbcfv_semantic_claims(
    const std::uint8_t* key,
    const SemanticAddressInput* inputs,
    const double* probabilities,
    std::int32_t count,
    std::int32_t* outputs) {
    if (key == nullptr || inputs == nullptr || probabilities == nullptr || outputs == nullptr ||
        count < 1 || count > 65536) return -32;
    std::vector<std::uint64_t> words(static_cast<std::size_t>(count));
    const int status = rcle_tbcfv_semantic_uniform_words(key, inputs, count, words.data());
    if (status != 0) return status;
    constexpr double WORD_SCALE = 1.0 / 18446744073709551616.0;
    for (int row = 0; row < count; ++row) {
        const double uniform = (static_cast<double>(words[static_cast<std::size_t>(row)]) + 0.5) * WORD_SCALE;
        double cumulative = 0.0;
        int selected = BEACONS - 1;
        for (int candidate = 0; candidate < BEACONS; ++candidate) {
            const double probability = probabilities[static_cast<std::size_t>(row) * BEACONS + candidate];
            if (!std::isfinite(probability) || probability < 0.0 || probability > 1.0) return -33;
            cumulative += probability;
            if (uniform < cumulative) { selected = candidate; break; }
        }
        outputs[row] = selected;
    }
    return 0;
}

TBCFV_EXPORT std::int32_t rcle_tbcfv_semantic_claims_compact(
    const std::uint8_t* key,
    std::int64_t run_block,
    const std::int32_t* cell_codes,
    const std::int64_t* update_or_scenarios,
    const std::int64_t* roster_events,
    const std::int64_t* physical_agents,
    const std::int64_t* physical_ticks,
    const double* probabilities,
    std::int32_t count,
    std::int32_t* outputs) {
    if (key == nullptr || cell_codes == nullptr || update_or_scenarios == nullptr ||
        roster_events == nullptr || physical_agents == nullptr || physical_ticks == nullptr ||
        probabilities == nullptr || outputs == nullptr || count < 1 || count > 65536) return -34;
    std::string payload;
    std::uint8_t digest[32];
    constexpr double WORD_SCALE = 1.0 / 18446744073709551616.0;
    for (int row = 0; row < count; ++row) {
        if (cell_codes[row] < 0 || cell_codes[row] >= 16) return -35;
        const SemanticAddressInput address{
            run_block, "", "", CELL_NAMES[cell_codes[row]], update_or_scenarios[row], physical_ticks[row],
            roster_events[row], "", 1, physical_agents[row], "", 1, "actor-claim", 0};
        if (!semantic_payload(address, payload)) return -31;
        hmac_sha256(key, payload, digest);
        std::uint64_t word = 0;
        for (int byte = 0; byte < 8; ++byte) word = (word << 8) | digest[byte];
        const double uniform = (static_cast<double>(word) + 0.5) * WORD_SCALE;
        double cumulative = 0.0;
        int selected = BEACONS - 1;
        for (int candidate = 0; candidate < BEACONS; ++candidate) {
            const double probability = probabilities[static_cast<std::size_t>(row) * BEACONS + candidate];
            if (!std::isfinite(probability) || probability < 0.0 || probability > 1.0) return -33;
            cumulative += probability;
            if (uniform < cumulative) { selected = candidate; break; }
        }
        outputs[row] = selected;
    }
    return 0;
}

TBCFV_EXPORT std::int32_t rcle_tbcfv_materialize_fixtures(
    const std::uint8_t* key,
    std::int64_t run_block,
    const std::int32_t* cell_codes,
    const std::int64_t* update_or_scenarios,
    const std::int64_t* episode_rows,
    std::int32_t width,
    FixtureInput* outputs) {
    if (key == nullptr || cell_codes == nullptr || update_or_scenarios == nullptr ||
        episode_rows == nullptr || outputs == nullptr || !supported_width(width)) return -50;
    std::string payload;
    for (int lane = 0; lane < width; ++lane) {
        const int cell = cell_codes[lane];
        if (cell < 0 || cell >= 16) return -51;
        const int before = CELL_BEFORE[cell];
        const int after = CELL_AFTER[cell];
        FixtureInput fixture{};
        fixture.magic = MAGIC;
        fixture.abi = ABI;
        fixture.initial_n = before;
        fixture.after_n = after;
        fixture.event_condition = (cell % 2 == 1) ? NEW_EPOCH : ACTIVE_CONTINUATION;
        fixture.omega_plus = 0;
        fixture.kappa_plus = 0;
        std::fill(std::begin(fixture.initial_keys), std::end(fixture.initial_keys), -1);
        std::fill(std::begin(fixture.initial_positions), std::end(fixture.initial_positions), -1);
        std::fill(std::begin(fixture.after_keys), std::end(fixture.after_keys), -1);
        std::fill(std::begin(fixture.after_positions), std::end(fixture.after_positions), -1);

        std::vector<std::pair<double,int>> ranked_positions;
        ranked_positions.reserve(SECTORS);
        for (int sector = 0; sector < SECTORS; ++sector) {
            const SemanticAddressInput address{
                run_block, "", "", CELL_NAMES[cell], update_or_scenarios[lane], 0,
                0, "", 0, episode_rows[lane], "", 1,
                "initial-position-permutation", sector};
            ranked_positions.emplace_back(semantic_uniform(key, address, payload), sector);
        }
        std::sort(ranked_positions.begin(), ranked_positions.end());
        for (int index = 0; index < before; ++index) {
            fixture.initial_keys[index] = index;
            fixture.initial_positions[index] = ranked_positions[static_cast<std::size_t>(index)].second;
        }
        std::vector<int> after_keys;
        if (after < before) {
            std::vector<std::pair<double,int>> survivors;
            survivors.reserve(static_cast<std::size_t>(before));
            for (int agent = 0; agent < before; ++agent) {
                const SemanticAddressInput address{
                    run_block, "", "", CELL_NAMES[cell], update_or_scenarios[lane], 0,
                    0, "contraction", 0, episode_rows[lane], "", 1,
                    "survivor-subset", agent};
                survivors.emplace_back(semantic_uniform(key, address, payload), agent);
            }
            std::sort(survivors.begin(), survivors.end());
            for (int index = 0; index < after; ++index)
                after_keys.push_back(survivors[static_cast<std::size_t>(index)].second);
            std::sort(after_keys.begin(), after_keys.end());
        } else {
            for (int agent = 0; agent < after; ++agent) after_keys.push_back(agent);
        }
        for (int index = 0; index < after; ++index) {
            fixture.after_keys[index] = after_keys[static_cast<std::size_t>(index)];
            fixture.after_positions[index] = after_keys[static_cast<std::size_t>(index)] < before
                ? -1 : EVENT_POSITION;
        }
        if (fixture.event_condition == NEW_EPOCH) {
            const SemanticAddressInput omega_address{
                run_block, "", "", CELL_NAMES[cell], update_or_scenarios[lane], 0,
                0, "new_epoch", 0, episode_rows[lane], "", 1, "omega-plus", 0};
            const SemanticAddressInput kappa_address{
                run_block, "", "", CELL_NAMES[cell], update_or_scenarios[lane], 0,
                0, "new_epoch", 0, episode_rows[lane], "", 1, "kappa-plus", 0};
            const double omega = semantic_uniform(key, omega_address, payload);
            const double kappa = semantic_uniform(key, kappa_address, payload);
            fixture.omega_plus = std::array<int,3>{5,10,15}[static_cast<std::size_t>(std::min(static_cast<int>(omega * 3.0), 2))];
            fixture.kappa_plus = std::min(static_cast<int>(kappa * 5.0), 4) + 1;
        }
        const int status = validate_fixture(fixture);
        if (status != 0) return status;
        outputs[lane] = fixture;
    }
    return 0;
}

TBCFV_EXPORT std::int32_t rcle_tbcfv_materialize_events(
    const std::uint8_t* key,
    std::int64_t run_block,
    const std::int32_t* cell_codes,
    const std::int64_t* update_or_scenarios,
    const std::int64_t* episode_rows,
    const Snapshot* snapshots,
    const FixtureInput* fixtures,
    std::int32_t width,
    EventInput* outputs) {
    if (key == nullptr || cell_codes == nullptr || update_or_scenarios == nullptr ||
        episode_rows == nullptr || snapshots == nullptr || fixtures == nullptr ||
        outputs == nullptr || !supported_width(width)) return -52;
    std::string payload;
    for (int lane = 0; lane < width; ++lane) {
        const int cell = cell_codes[lane];
        if (cell < 0 || cell >= 16 || snapshots[lane].status != 0 ||
            !snapshots[lane].event_input_required || snapshots[lane].tick != EVENT_TICK) return -53;
        const FixtureInput& fixture = fixtures[lane];
        const int status = validate_fixture(fixture);
        if (status != 0) return status;
        std::vector<int> newcomer_keys;
        for (int index = 0; index < fixture.after_n; ++index) {
            const int candidate = fixture.after_keys[index];
            if (!contains(fixture.initial_keys, fixture.initial_n, candidate)) newcomer_keys.push_back(candidate);
        }
        std::array<bool,SECTORS> occupied{};
        for (int index = 0; index < snapshots[lane].agent_count; ++index) {
            const int physical_key = snapshots[lane].transport_keys[index];
            if (contains(fixture.after_keys, fixture.after_n, physical_key) &&
                contains(fixture.initial_keys, fixture.initial_n, physical_key))
                occupied[static_cast<std::size_t>(snapshots[lane].positions[index])] = true;
        }
        std::vector<std::pair<double,int>> ranked;
        ranked.reserve(SECTORS);
        for (int sector = 0; sector < SECTORS; ++sector) {
            if (occupied[static_cast<std::size_t>(sector)]) continue;
            const SemanticAddressInput address{
                run_block, "", "", CELL_NAMES[cell], update_or_scenarios[lane], EVENT_TICK,
                0, "newcomer-entry", 0, episode_rows[lane], "", 1,
                "newcomer-position-permutation", sector};
            ranked.emplace_back(semantic_uniform(key, address, payload), sector);
        }
        std::sort(ranked.begin(), ranked.end());
        EventInput event{};
        event.magic = MAGIC;
        event.abi = ABI;
        event.newcomer_count = static_cast<int>(newcomer_keys.size());
        std::fill(std::begin(event.newcomer_positions), std::end(event.newcomer_positions), -1);
        for (int index = 0; index < event.newcomer_count; ++index)
            event.newcomer_positions[index] = ranked[static_cast<std::size_t>(index)].second;
        outputs[lane] = event;
    }
    return 0;
}

TBCFV_EXPORT std::int32_t rcle_tbcfv_scripted_actions(
    const Snapshot* snapshots,
    std::int32_t width,
    std::int32_t package_code,
    const std::int32_t* previous_claims,
    const std::uint8_t* survivors,
    const std::uint8_t* first_or_epoch,
    const std::uint8_t* active_churn,
    const std::int32_t* post_event_claim_index,
    StepInput* outputs) {
    if (!supported_width(width) || snapshots == nullptr || previous_claims == nullptr ||
        survivors == nullptr || first_or_epoch == nullptr || active_churn == nullptr ||
        post_event_claim_index == nullptr || outputs == nullptr || package_code < 0 || package_code > 2) return -43;
    for (int lane = 0; lane < width; ++lane) {
        const Snapshot& row = snapshots[lane];
        if (row.status != 0 || row.terminal || !row.claim_required || row.agent_count < 1 || row.agent_count > MAX_AGENTS) return -44;
        StepInput action{};
        action.magic = MAGIC;
        action.abi = ABI;
        action.claim_count = row.agent_count;
        std::fill(std::begin(action.claims), std::end(action.claims), -1);
        if (package_code == 2) {
            for (int agent = 0; agent < row.agent_count; ++agent) {
                int selected = 0;
                int best = circular_distance(row.positions[agent], row.beacon_positions[0]);
                for (int beacon = 1; beacon < BEACONS; ++beacon) {
                    const int distance = circular_distance(row.positions[agent], row.beacon_positions[beacon]);
                    if (distance < best) { best = distance; selected = beacon; }
                }
                action.claims[agent] = selected;
            }
        } else {
            const int status = coherent_actions(
                row,
                previous_claims + static_cast<std::size_t>(lane) * MAX_AGENTS,
                survivors + static_cast<std::size_t>(lane) * MAX_AGENTS,
                first_or_epoch[lane] != 0,
                action.claims);
            if (status != 0) return status;
            if (package_code == 1 && active_churn[lane] &&
                (post_event_claim_index[lane] == 0 || post_event_claim_index[lane] == 1)) {
                std::vector<int> angular(static_cast<std::size_t>(row.agent_count));
                for (int index = 0; index < row.agent_count; ++index) angular[static_cast<std::size_t>(index)] = index;
                std::sort(angular.begin(), angular.end(), [&](int left, int right) {
                    if (row.positions[left] != row.positions[right]) return row.positions[left] < row.positions[right];
                    return row.transport_keys[left] < row.transport_keys[right];
                });
                for (int lower : {0, 2, 4}) {
                    const int source = lower + 1;
                    auto found = std::find_if(angular.begin(), angular.end(), [&](int agent) {
                        return action.claims[agent] == source;
                    });
                    if (found == angular.end()) return -45;
                    action.claims[*found] = lower;
                }
            }
        }
        outputs[lane] = action;
    }
    return 0;
}

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
