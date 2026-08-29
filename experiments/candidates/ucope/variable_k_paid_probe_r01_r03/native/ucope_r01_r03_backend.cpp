#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <unordered_map>
#include <utility>
#include <vector>

#if defined(_WIN32)
#define UCOPE_EXPORT extern "C" __declspec(dllexport)
#else
#define UCOPE_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {

constexpr std::uint32_t M0 = 0xD2511F53u;
constexpr std::uint32_t M1 = 0xCD9E8D57u;
constexpr std::uint32_t W0 = 0x9E3779B9u;
constexpr std::uint32_t W1 = 0xBB67AE85u;
constexpr std::uint32_t KEY_SALT0 = 0x55434F50u;
constexpr std::uint32_t KEY_SALT1 = 0x52303133u;
constexpr std::uint32_t REVISION_SALT = 0x20260823u;
constexpr int WIDTHS[4] = {8, 32, 256, 768};
constexpr int K_TRAIN[5] = {1, 3, 5, 7, 9};

struct Words {
    std::uint32_t v0;
    std::uint32_t v1;
    std::uint32_t v2;
    std::uint32_t v3;
};

inline std::uint32_t hi32(std::uint32_t a, std::uint32_t b) {
    return static_cast<std::uint32_t>((static_cast<std::uint64_t>(a) * b) >> 32u);
}

inline Words philox(
    std::uint64_t seed,
    std::uint32_t tag,
    std::uint32_t panel,
    std::uint32_t arm,
    std::uint32_t network,
    std::uint32_t a,
    std::uint32_t b) {
    std::uint32_t k0 = static_cast<std::uint32_t>(seed) ^ KEY_SALT0;
    std::uint32_t k1 = static_cast<std::uint32_t>(seed >> 32u) ^ KEY_SALT1;
    Words c{a, b, tag | (panel << 8u) | (arm << 16u) | (network << 24u), REVISION_SALT};
    for (int round = 0; round < 10; ++round) {
        const std::uint32_t lo0 = M0 * c.v0;
        const std::uint32_t lo1 = M1 * c.v2;
        const std::uint32_t h0 = hi32(M0, c.v0);
        const std::uint32_t h1 = hi32(M1, c.v2);
        c = Words{h1 ^ c.v1 ^ k0, lo1, h0 ^ c.v3 ^ k1, lo0};
        k0 += W0;
        k1 += W1;
    }
    return c;
}

inline float uniform01(const Words& words) {
    return static_cast<float>(words.v0 >> 8u) * 0x1.0p-24f;
}

inline bool supported_width(int width) {
    for (int value : WIDTHS) {
        if (width == value) return true;
    }
    return false;
}

struct RegimeTriple {
    int probe;
    int tail;
    int display;
};

std::vector<RegimeTriple> regime_roster(std::uint64_t seed, int panel, int batch) {
    struct Entry {
        std::uint32_t key;
        int slot;
        RegimeTriple value;
    };
    std::vector<Entry> entries;
    entries.reserve(256);
    for (int slot = 0; slot < 256; ++slot) {
        RegimeTriple value{};
        if (panel == 0) {
            value.probe = slot < 128 ? 0 : 1;
            value.tail = value.probe;
            value.display = value.probe;
        } else {
            const int pair = slot / 64;
            const int first = pair / 2;
            const int second = pair % 2;
            if (panel == 1) {
                value.probe = first;
                value.tail = second;
                value.display = first;
            } else {
                value.probe = first;
                value.tail = first;
                value.display = second;
            }
        }
        const Words random = philox(seed, 1u, static_cast<std::uint32_t>(panel), 255u, 0u,
                                    static_cast<std::uint32_t>(batch), static_cast<std::uint32_t>(slot));
        entries.push_back(Entry{random.v0, slot, value});
    }
    std::stable_sort(entries.begin(), entries.end(), [](const Entry& left, const Entry& right) {
        if (left.key != right.key) return left.key < right.key;
        return left.slot < right.slot;
    });
    std::vector<RegimeTriple> result;
    result.reserve(256);
    for (const Entry& entry : entries) result.push_back(entry.value);
    return result;
}

inline void candidate(float* output, const float* channel, bool root, bool probe, int k) {
    for (int i = 0; i < 13; ++i) output[i] = 0.0f;
    for (int i = 0; i < 6; ++i) output[i] = channel[i];
    output[6] = root ? 1.0f : 0.0f;
    output[7] = root ? 0.0f : 1.0f;
    output[8] = probe ? 1.0f : 0.0f;
    output[9] = probe ? 0.0f : 1.0f;
    if (!probe) {
        const float scaled = static_cast<float>(k) / 9.0f;
        output[10] = scaled;
        output[11] = scaled * scaled;
    }
    output[12] = root ? 1.0f : (10.0f / 12.0f);
}

inline void baseline(float* output, const float* channel, bool root) {
    for (int i = 0; i < 6; ++i) output[i] = channel[i];
    output[6] = root ? 1.0f : 0.0f;
    output[7] = root ? 0.0f : 1.0f;
    output[8] = root ? 1.0f : (10.0f / 12.0f);
}

inline float probe_probability(int regime) {
    return regime == 0 ? 0.85f : 0.15f;
}

inline float tail_probability(int regime, int k) {
    const int anchor = regime == 0 ? 2 : 8;
    const int delta = k - anchor;
    return 0.95f - static_cast<float>(delta * delta) / 100.0f;
}

struct Lane {
    std::uint64_t seed;
    std::uint64_t episode;
    int panel;
    int arm;
    int probe_regime;
    int tail_regime;
    int display_regime;
    int status;
    float components[6];
    int actual[6];
    int displayed[6];
};

std::atomic<std::uint64_t> next_handle{1u};
std::unordered_map<std::uint64_t, Lane> lanes;
std::mutex lane_mutex;

inline void tail_components(Lane& lane, int k) {
    const Words random = philox(lane.seed, 4u, static_cast<std::uint32_t>(lane.panel), 255u, 0u,
                                static_cast<std::uint32_t>(lane.episode), static_cast<std::uint32_t>(k));
    lane.components[0] = uniform01(random) < tail_probability(lane.tail_regime, k) ? 1.0f : 0.0f;
    lane.components[1] = -0.01f * static_cast<float>(k);
    lane.components[2] = -0.001f * static_cast<float>(k * k);
}

inline int lookup(std::uint64_t handle, Lane*& lane) {
    const auto found = lanes.find(handle);
    if (found == lanes.end()) return -20;
    lane = &found->second;
    return 0;
}

}  // namespace

UCOPE_EXPORT int ucope_r01_r03_abi_version() { return 1; }
UCOPE_EXPORT int ucope_r01_r03_max_width() { return 768; }
UCOPE_EXPORT int ucope_r01_r03_supported_width(int width) { return supported_width(width) ? 1 : 0; }

UCOPE_EXPORT std::uint32_t ucope_r01_r03_philox_word0(
    std::uint64_t seed, int tag, int panel, int arm, int network, std::uint32_t a, std::uint32_t b) {
    return philox(seed, static_cast<std::uint32_t>(tag), static_cast<std::uint32_t>(panel),
                  static_cast<std::uint32_t>(arm), static_cast<std::uint32_t>(network), a, b).v0;
}

UCOPE_EXPORT int ucope_r01_r03_init_uniforms(
    std::uint64_t seed, int panel, int network, int count, float* output) {
    if (panel < 0 || panel > 2 || network < 0 || network > 1 || count < 0 || output == nullptr) return -1;
    for (int coordinate = 0; coordinate < count; ++coordinate) {
        output[coordinate] = uniform01(philox(
            seed, 6u, static_cast<std::uint32_t>(panel), 255u,
            static_cast<std::uint32_t>(network), static_cast<std::uint32_t>(coordinate),
            static_cast<std::uint32_t>(network)));
    }
    return 0;
}

UCOPE_EXPORT int ucope_r01_r03_reset_batch(
    std::uint64_t seed, int panel, int batch, int width, const std::int32_t* arms,
    std::uint64_t* handles, std::int64_t* episodes, std::int32_t* regimes,
    float* root_features, float* root_baselines) {
    if (!supported_width(width) || panel < 0 || panel > 2 || batch < 0 || arms == nullptr ||
        handles == nullptr || episodes == nullptr || regimes == nullptr || root_features == nullptr ||
        root_baselines == nullptr) return -1;
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        if (arms[lane_index] < 0 || arms[lane_index] > 2) return -2;
    }
    const std::vector<RegimeTriple> roster = regime_roster(seed, panel, batch);
    const float empty[6] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    std::lock_guard<std::mutex> guard(lane_mutex);
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        const int slot = lane_index % 256;
        const std::uint64_t episode = static_cast<std::uint64_t>(batch) * 256u + static_cast<std::uint64_t>(slot);
        const RegimeTriple value = roster[slot];
        Lane lane{};
        lane.seed = seed;
        lane.episode = episode;
        lane.panel = panel;
        lane.arm = arms[lane_index];
        lane.probe_regime = value.probe;
        lane.tail_regime = value.tail;
        lane.display_regime = value.display;
        lane.status = 0;
        const std::uint64_t handle = next_handle.fetch_add(1u);
        lanes.emplace(handle, lane);
        handles[lane_index] = handle;
        episodes[lane_index] = static_cast<std::int64_t>(episode);
        regimes[lane_index * 3 + 0] = value.probe;
        regimes[lane_index * 3 + 1] = value.tail;
        regimes[lane_index * 3 + 2] = value.display;
        float* feature = root_features + lane_index * 6 * 13;
        candidate(feature, empty, true, true, 0);
        for (int action = 0; action < 5; ++action) {
            candidate(feature + (action + 1) * 13, empty, true, false, K_TRAIN[action]);
        }
        baseline(root_baselines + lane_index * 9, empty, true);
    }
    return 0;
}

UCOPE_EXPORT int ucope_r01_r03_sample_actions(
    std::uint64_t seed, int panel, int batch, int width, const std::int32_t* arms,
    int decision_code, const float* probabilities, int maximum_actions,
    const std::int32_t* legal_counts, std::int32_t* actions) {
    if (!supported_width(width) || panel < 0 || panel > 2 || batch < 0 ||
        (decision_code != 0 && decision_code != 1) || maximum_actions < 1 || maximum_actions > 6 ||
        arms == nullptr || probabilities == nullptr || legal_counts == nullptr || actions == nullptr) return -1;
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        const int count = legal_counts[lane_index];
        if (arms[lane_index] < 0 || arms[lane_index] > 2 || count < 0 || count > maximum_actions) return -2;
        if (count == 0) {
            actions[lane_index] = -1;
            continue;
        }
        const std::uint32_t episode = static_cast<std::uint32_t>(batch * 256 + lane_index % 256);
        const float draw = uniform01(philox(seed, 5u, static_cast<std::uint32_t>(panel),
                                            static_cast<std::uint32_t>(arms[lane_index]), 0u,
                                            episode, static_cast<std::uint32_t>(decision_code)));
        float cumulative = 0.0f;
        int selected = count - 1;
        for (int action = 0; action < count; ++action) {
            const float probability = probabilities[lane_index * maximum_actions + action];
            if (!std::isfinite(probability) || probability < 0.0f) return -3;
            cumulative += probability;
            if (draw < cumulative) {
                selected = action;
                break;
            }
        }
        actions[lane_index] = selected;
    }
    return 0;
}

UCOPE_EXPORT int ucope_r01_r03_root_step_batch(
    const std::uint64_t* handles, const std::int32_t* actions, int width,
    std::int32_t* actual_marks, std::int32_t* displayed_marks, float* probe_components,
    float* tail_features, float* tail_baselines, std::int32_t* terminal_flags,
    float* immediate_tail_components) {
    if (!supported_width(width) || handles == nullptr || actions == nullptr || actual_marks == nullptr ||
        displayed_marks == nullptr || probe_components == nullptr || tail_features == nullptr ||
        tail_baselines == nullptr || terminal_flags == nullptr || immediate_tail_components == nullptr) return -1;
    std::lock_guard<std::mutex> guard(lane_mutex);
    int expected_panel = -1;
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        Lane* lane = nullptr;
        int code = lookup(handles[lane_index], lane);
        if (code != 0) return code;
        if (expected_panel < 0) expected_panel = lane->panel;
        if (lane->panel != expected_panel) return -24;
        if (lane->status != 0 || actions[lane_index] < 0 || actions[lane_index] > 5) return -21;
    }
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        Lane* lane = nullptr;
        lookup(handles[lane_index], lane);
        for (int i = 0; i < 6; ++i) {
            actual_marks[lane_index * 6 + i] = 0;
            displayed_marks[lane_index * 6 + i] = 0;
        }
        for (int i = 0; i < 3; ++i) {
            probe_components[lane_index * 3 + i] = 0.0f;
            immediate_tail_components[lane_index * 3 + i] = 0.0f;
        }
        terminal_flags[lane_index] = 0;
        if (actions[lane_index] != 0) {
            tail_components(*lane, K_TRAIN[actions[lane_index] - 1]);
            lane->status = 2;
            terminal_flags[lane_index] = 1;
            for (int i = 0; i < 3; ++i) immediate_tail_components[lane_index * 3 + i] = lane->components[i];
            continue;
        }
        int actual_count = 0;
        int displayed_count = 0;
        for (int micro = 0; micro < 6; ++micro) {
            const Words actual_random = philox(lane->seed, 2u, static_cast<std::uint32_t>(lane->panel), 255u, 0u,
                                               static_cast<std::uint32_t>(lane->episode), static_cast<std::uint32_t>(micro));
            lane->actual[micro] = uniform01(actual_random) < probe_probability(lane->probe_regime) ? 1 : 0;
            if (lane->panel == 2) {
                const Words display_random = philox(lane->seed, 3u, static_cast<std::uint32_t>(lane->panel), 255u, 0u,
                                                    static_cast<std::uint32_t>(lane->episode), static_cast<std::uint32_t>(micro));
                lane->displayed[micro] = uniform01(display_random) < probe_probability(lane->display_regime) ? 1 : 0;
            } else {
                lane->displayed[micro] = lane->actual[micro];
            }
            actual_marks[lane_index * 6 + micro] = lane->actual[micro];
            displayed_marks[lane_index * 6 + micro] = lane->displayed[micro];
            actual_count += lane->actual[micro];
            displayed_count += lane->displayed[micro];
        }
        lane->components[3] = 0.08f * (static_cast<float>(actual_count) / 6.0f);
        lane->components[4] = -0.03f;
        lane->components[5] = -0.03f;
        probe_components[lane_index * 3 + 0] = lane->components[3];
        probe_components[lane_index * 3 + 1] = lane->components[4];
        probe_components[lane_index * 3 + 2] = lane->components[5];
        float channel[6] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
        if (lane->arm == 0) {
            channel[0] = static_cast<float>(displayed_count) / 6.0f;
            channel[1] = 1.0f;
            channel[2] = (static_cast<float>(displayed_count) - 3.0f) / 6.0f;
            channel[3] = 1.0f;
        } else if (lane->arm == 1) {
            for (int i = 0; i < 6; ++i) channel[i] = static_cast<float>(lane->displayed[i]);
        } else {
            float rho = 0.5f;
            if (lane->panel == 0) {
                float short_weight = 1.0f;
                float long_weight = 1.0f;
                for (int i = 0; i < displayed_count; ++i) {
                    short_weight *= 0.85f;
                    long_weight *= 0.15f;
                }
                for (int i = displayed_count; i < 6; ++i) {
                    short_weight *= 0.15f;
                    long_weight *= 0.85f;
                }
                rho = short_weight / (short_weight + long_weight);
            }
            channel[0] = rho;
            channel[1] = 1.0f - rho;
            channel[2] = 1.0f;
        }
        float* feature = tail_features + lane_index * 5 * 13;
        for (int action = 0; action < 5; ++action) candidate(feature + action * 13, channel, false, false, K_TRAIN[action]);
        baseline(tail_baselines + lane_index * 9, channel, false);
        lane->status = 1;
    }
    return 0;
}

UCOPE_EXPORT int ucope_r01_r03_tail_step_batch(
    const std::uint64_t* handles, const std::int32_t* actions, int width, float* tail_output) {
    if (!supported_width(width) || handles == nullptr || actions == nullptr || tail_output == nullptr) return -1;
    std::lock_guard<std::mutex> guard(lane_mutex);
    int expected_panel = -1;
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        Lane* lane = nullptr;
        int code = lookup(handles[lane_index], lane);
        if (code != 0) return code;
        if (expected_panel < 0) expected_panel = lane->panel;
        if (lane->panel != expected_panel) return -24;
        const bool probed = lane->status == 1 && actions[lane_index] >= 0 && actions[lane_index] <= 4;
        const bool immediate = lane->status == 2 && actions[lane_index] == -1;
        if (!probed && !immediate) return -22;
    }
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        Lane* lane = nullptr;
        lookup(handles[lane_index], lane);
        if (lane->status == 1) {
            tail_components(*lane, K_TRAIN[actions[lane_index]]);
            lane->status = 2;
            for (int i = 0; i < 3; ++i) tail_output[lane_index * 3 + i] = lane->components[i];
        } else {
            for (int i = 0; i < 3; ++i) tail_output[lane_index * 3 + i] = 0.0f;
        }
    }
    return 0;
}

UCOPE_EXPORT int ucope_r01_r03_terminal_batch(
    const std::uint64_t* handles, int width, float* components, float* totals) {
    if (!supported_width(width) || handles == nullptr || components == nullptr || totals == nullptr) return -1;
    std::lock_guard<std::mutex> guard(lane_mutex);
    int expected_panel = -1;
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        Lane* lane = nullptr;
        int code = lookup(handles[lane_index], lane);
        if (code != 0) return code;
        if (expected_panel < 0) expected_panel = lane->panel;
        if (lane->panel != expected_panel) return -24;
        if (lane->status != 2) return -23;
    }
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        Lane* lane = nullptr;
        lookup(handles[lane_index], lane);
        float total = 0.0f;
        for (int i = 0; i < 6; ++i) {
            components[lane_index * 6 + i] = lane->components[i];
            total += lane->components[i];
        }
        totals[lane_index] = total;
    }
    return 0;
}

UCOPE_EXPORT int ucope_r01_r03_close_batch(const std::uint64_t* handles, int width) {
    if (!supported_width(width) || handles == nullptr) return -1;
    std::lock_guard<std::mutex> guard(lane_mutex);
    int expected_panel = -1;
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        Lane* lane = nullptr;
        int code = lookup(handles[lane_index], lane);
        if (code != 0) return code;
        if (expected_panel < 0) expected_panel = lane->panel;
        if (lane->panel != expected_panel) return -24;
    }
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        lanes.erase(handles[lane_index]);
    }
    return 0;
}

UCOPE_EXPORT int ucope_r01_r03_counter_fill(
    std::uint64_t seed, int width, int iterations, std::uint64_t* output) {
    if (!supported_width(width) || iterations < 1 || output == nullptr) return -1;
    for (int lane = 0; lane < width; ++lane) {
        std::uint64_t digest = 0u;
        for (int index = 0; index < iterations; ++index) {
            for (std::uint32_t tag = 1u; tag <= 6u; ++tag) {
                const std::uint32_t arm = tag == 5u ? static_cast<std::uint32_t>(lane % 3) : 255u;
                const std::uint32_t network = tag == 6u ? static_cast<std::uint32_t>(lane % 2) : 0u;
                const Words value = philox(
                    seed, tag, static_cast<std::uint32_t>(lane % 3), arm, network,
                    static_cast<std::uint32_t>(index), static_cast<std::uint32_t>(lane));
                digest ^= (static_cast<std::uint64_t>(value.v0) << 32u) | value.v1;
                digest = (digest << 7u) | (digest >> 57u);
            }
        }
        output[lane] = digest;
    }
    return 0;
}

UCOPE_EXPORT int ucope_r01_r03_population_batch(
    std::uint64_t seed, int panel, int batch, int width, std::int32_t* regimes,
    std::int32_t* actual_marks, std::int32_t* displayed_marks, std::int32_t* potential_tail) {
    if (!supported_width(width) || panel < 0 || panel > 2 || batch < 0 || regimes == nullptr ||
        actual_marks == nullptr || displayed_marks == nullptr || potential_tail == nullptr) return -1;
    const std::vector<RegimeTriple> roster = regime_roster(seed, panel, batch);
    for (int lane_index = 0; lane_index < width; ++lane_index) {
        const int slot = lane_index % 256;
        const std::uint32_t episode = static_cast<std::uint32_t>(batch * 256 + slot);
        const RegimeTriple value = roster[slot];
        regimes[lane_index * 3 + 0] = value.probe;
        regimes[lane_index * 3 + 1] = value.tail;
        regimes[lane_index * 3 + 2] = value.display;
        for (int micro = 0; micro < 6; ++micro) {
            const int actual = uniform01(philox(
                seed, 2u, static_cast<std::uint32_t>(panel), 255u, 0u, episode,
                static_cast<std::uint32_t>(micro))) < probe_probability(value.probe) ? 1 : 0;
            const int displayed = panel == 2
                ? (uniform01(philox(
                    seed, 3u, static_cast<std::uint32_t>(panel), 255u, 0u, episode,
                    static_cast<std::uint32_t>(micro))) < probe_probability(value.display) ? 1 : 0)
                : actual;
            actual_marks[lane_index * 6 + micro] = actual;
            displayed_marks[lane_index * 6 + micro] = displayed;
        }
        for (int action = 0; action < 5; ++action) {
            const int k = K_TRAIN[action];
            potential_tail[lane_index * 5 + action] = uniform01(philox(
                seed, 4u, static_cast<std::uint32_t>(panel), 255u, 0u, episode,
                static_cast<std::uint32_t>(k))) < tail_probability(value.tail, k) ? 1 : 0;
        }
    }
    return 0;
}

inline float expected_tail(float rho, int k) {
    return rho * tail_probability(0, k) + (1.0f - rho) * tail_probability(1, k)
        - 0.01f * static_cast<float>(k) - 0.001f * static_cast<float>(k * k);
}

inline int first_best_period(float rho, const std::int32_t* periods, int count, float* best_value) {
    int selected = 0;
    float best = expected_tail(rho, periods[0]);
    for (int index = 1; index < count; ++index) {
        const float candidate_value = expected_tail(rho, periods[index]);
        if (candidate_value > best + 1.0e-6f) {
            best = candidate_value;
            selected = index;
        }
    }
    *best_value = best;
    return selected;
}

inline float history_probability(int theta, int history) {
    float probability = 1.0f;
    const float hit = theta == 0 ? 0.85f : 0.15f;
    const float miss = theta == 0 ? 0.15f : 0.85f;
    for (int micro = 0; micro < 6; ++micro) {
        probability *= ((history >> (5 - micro)) & 1) != 0 ? hit : miss;
    }
    return probability;
}

inline float posterior_from_count(int count) {
    float short_weight = 1.0f;
    float long_weight = 1.0f;
    for (int index = 0; index < count; ++index) {
        short_weight *= 0.85f;
        long_weight *= 0.15f;
    }
    for (int index = count; index < 6; ++index) {
        short_weight *= 0.15f;
        long_weight *= 0.85f;
    }
    return short_weight / (short_weight + long_weight);
}

UCOPE_EXPORT int ucope_r01_r03_nonlearned_actions(
    int panel, int displayed_count, const std::int32_t* periods, int period_count,
    std::int32_t* actions) {
    if (panel < 0 || panel > 2 || displayed_count < 0 || displayed_count > 6 ||
        periods == nullptr || actions == nullptr || period_count < 1 || period_count > 5) return -1;
    for (int index = 0; index < period_count; ++index) {
        if (periods[index] < 1 || periods[index] > 9) return -2;
        if (index > 0 && periods[index] <= periods[index - 1]) return -3;
    }
    float immediate_value = 0.0f;
    const int immediate_period = first_best_period(0.5f, periods, period_count, &immediate_value);
    float rho = panel == 0 ? posterior_from_count(displayed_count) : 0.5f;
    float tail_value = 0.0f;
    const int belief_tail_period = first_best_period(rho, periods, period_count, &tail_value);
    float probe_value = immediate_value - 0.02f;
    if (panel == 0) {
        probe_value = 0.0f;
        for (int theta = 0; theta < 2; ++theta) {
            for (int history = 0; history < 64; ++history) {
                int count = 0;
                for (int micro = 0; micro < 6; ++micro) count += (history >> micro) & 1;
                float history_tail = 0.0f;
                first_best_period(posterior_from_count(count), periods, period_count, &history_tail);
                const float direct = 0.08f * (static_cast<float>(count) / 6.0f) - 0.06f;
                probe_value += 0.5f * history_probability(theta, history) * (history_tail + direct);
            }
        }
    }
    const int belief_root = probe_value + 1.0e-6f >= immediate_value ? 0 : immediate_period + 1;
    actions[0] = belief_root;
    actions[1] = belief_tail_period;
    actions[2] = immediate_period + 1;
    actions[3] = 0;
    actions[4] = immediate_period;
    return 0;
}
