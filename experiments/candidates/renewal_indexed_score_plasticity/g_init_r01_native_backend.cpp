#include <cstddef>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <unordered_map>

#ifdef _WIN32
#define RISP_EXPORT extern "C" __declspec(dllexport)
#else
#define RISP_EXPORT extern "C"
#endif

namespace {
constexpr std::int32_t ABI_VERSION = 1;
constexpr std::uint64_t FIXTURE_MAGIC = 0x5253504752314E31ULL;
constexpr std::int32_t MAX_WIDTH = 32;

struct ResetInput {
    std::uint64_t magic;
    std::int32_t abi_version;
    std::int32_t schedule_id;
    std::int32_t prefix_bits;
    std::uint64_t init_event_token;
    std::uint64_t init_prefix[16];
};

struct StepInput {
    std::int32_t action;
    std::int32_t prefix_bits;
    std::uint64_t action_event_token;
    std::uint64_t motion_event_token;
    std::uint64_t ack_event_token;
    std::uint64_t motion_prefix[2];
    std::uint64_t ack_prefix[2];
};

struct ExtendedStepInput {
    std::int32_t action;
    std::int32_t prefix_bits;
    std::uint64_t action_event_token;
    std::uint64_t motion_event_token;
    std::uint64_t ack_event_token;
    std::uint64_t motion_prefix[16];
    std::uint64_t ack_prefix[16];
};

struct TransitionOutput {
    std::int32_t status;
    std::int32_t schedule_id;
    std::int32_t renewal;
    std::int32_t tau;
    std::int32_t duration;
    std::int32_t sector_before;
    std::int32_t sector_after;
    std::int32_t action;
    std::int32_t ack_sign;
    std::int32_t utility;
    std::int32_t terminal;
    std::int32_t next_tau;
    std::int32_t next_duration;
    std::int32_t init_events_consumed;
    std::int32_t action_events_consumed;
    std::int32_t motion_events_consumed;
    std::int32_t ack_events_consumed;
    std::uint64_t init_event_token;
    std::uint64_t action_event_token;
    std::uint64_t motion_event_token;
    std::uint64_t ack_event_token;
};

struct Session {
    std::int32_t schedule_id;
    std::int32_t sector;
    std::int32_t renewal;
    std::int32_t init_events;
    std::int32_t action_events;
    std::int32_t motion_events;
    std::int32_t ack_events;
    std::uint64_t init_token;
};

std::mutex sessions_mutex;
std::unordered_map<std::uint64_t, Session> sessions;
std::uint64_t next_handle = 1;

bool valid_width(std::int32_t width) { return width >= 1 && width <= MAX_WIDTH; }

struct Threshold { std::uint64_t words[16]; std::uint64_t remainder; };

Threshold binary_threshold(std::uint64_t numerator, std::uint64_t denominator, std::int32_t bits) {
    Threshold result{};
    std::uint64_t remainder = numerator;
    for (std::int32_t bit = 0; bit < bits; ++bit) {
        remainder *= 2;
        if (remainder >= denominator) {
            remainder -= denominator;
            result.words[bit / 64] |= std::uint64_t(1) << (63 - bit % 64);
        }
    }
    result.remainder = remainder;
    return result;
}

struct Threshold128Entry {
    std::uint64_t numerator;
    std::uint64_t denominator;
    Threshold threshold;
};

struct Threshold128Cache {
    Threshold128Entry entries[14]{};
    std::int32_t count = 0;

    Threshold128Cache() {
        add(1, 5); add(4, 5);
        for (const std::int32_t duration : {4, 8, 12}) {
            std::uint64_t power15 = 1, power16 = 1;
            for (std::int32_t i = 0; i < duration; ++i) { power15 *= 15; power16 *= 16; }
            const std::uint64_t denominator = 3 * power16;
            const std::uint64_t diagonal = power16 + 2 * power15;
            const std::uint64_t off = power16 - power15;
            add(off, denominator); add(diagonal, denominator);
            add(diagonal + off, denominator); add(2 * off, denominator);
        }
    }

    void add(std::uint64_t numerator, std::uint64_t denominator) {
        entries[count++] = Threshold128Entry{numerator, denominator, binary_threshold(numerator, denominator, 128)};
    }

    const Threshold* find(std::uint64_t numerator, std::uint64_t denominator) const {
        for (std::int32_t i = 0; i < count; ++i) {
            if (entries[i].numerator == numerator && entries[i].denominator == denominator) return &entries[i].threshold;
        }
        return nullptr;
    }
};

const Threshold* resolved_threshold(std::uint64_t numerator, std::uint64_t denominator,
                                    std::int32_t bits, Threshold* scratch) {
    if (bits == 128) {
        static const Threshold128Cache cache;
        if (const Threshold* cached = cache.find(numerator, denominator)) return cached;
    }
    *scratch = binary_threshold(numerator, denominator, bits);
    return scratch;
}

std::int32_t compare_words(const std::uint64_t* left, const std::uint64_t* right, std::int32_t count) {
    for (std::int32_t i = 0; i < count; ++i) {
        if (left[i] < right[i]) return -1;
        if (left[i] > right[i]) return 1;
    }
    return 0;
}

bool interval_below(const std::uint64_t* prefix, std::int32_t bits,
                    std::uint64_t numerator, std::uint64_t denominator) {
    Threshold scratch{};
    const Threshold& threshold = *resolved_threshold(numerator, denominator, bits, &scratch);
    std::uint64_t incremented[16];
    const std::int32_t count = bits / 64;
    std::memcpy(incremented, prefix, static_cast<std::size_t>(count) * sizeof(std::uint64_t));
    for (std::int32_t i = count - 1; i >= 0; --i) {
        ++incremented[i];
        if (incremented[i] != 0) break;
        if (i == 0) return false;
    }
    return compare_words(incremented, threshold.words, count) <= 0;
}

bool interval_straddles(const std::uint64_t* prefix, std::int32_t bits,
                        std::uint64_t numerator, std::uint64_t denominator) {
    Threshold scratch{};
    const Threshold& threshold = *resolved_threshold(numerator, denominator, bits, &scratch);
    const std::int32_t comparison = compare_words(prefix, threshold.words, bits / 64);
    return threshold.remainder == 0 ? comparison < 0 : comparison <= 0;
}

template <typename Input>
std::int32_t exact_motion(std::int32_t sector, std::int32_t duration,
                          const Input& input) {
    std::uint64_t power15 = 1, power16 = 1;
    for (std::int32_t i = 0; i < duration; ++i) { power15 *= 15; power16 *= 16; }
    const std::uint64_t denominator = 3 * power16;
    const std::uint64_t diagonal = power16 + 2 * power15;
    const std::uint64_t off = power16 - power15;
    std::uint64_t cumulative = 0;
    for (std::int32_t bits : {128, 256, 512, 1024}) {
        if (bits > input.prefix_bits) break;
        cumulative = 0;
        bool unresolved = false;
        for (std::int32_t candidate = 0; candidate < 2; ++candidate) {
            cumulative += (candidate == sector ? diagonal : off);
            if (interval_below(input.motion_prefix, bits, cumulative, denominator)) return candidate;
            if (interval_straddles(input.motion_prefix, bits, cumulative, denominator)) { unresolved = true; break; }
        }
        if (!unresolved) return 2;
    }
    return -1;
}

template <typename Input>
std::int32_t exact_ack(std::int32_t action, std::int32_t next_sector,
                       const Input& input) {
    const std::uint64_t numerator = action == next_sector ? 4 : 1;
    for (std::int32_t bits : {128, 256, 512, 1024}) {
        if (bits > input.prefix_bits) break;
        if (interval_below(input.ack_prefix, bits, numerator, 5)) return 1;
        if (!interval_straddles(input.ack_prefix, bits, numerator, 5)) return -1;
    }
    return 0;
}

std::int32_t row_count(std::int32_t schedule) {
    switch (schedule) {
        case 0: return 48;
        case 1: return 24;
        case 2: return 16;
        case 3: return 32;
        case 4: return 32;
        default: return 0;
    }
}

bool schedule_row(std::int32_t schedule, std::int32_t renewal,
                  std::int32_t* tau, std::int32_t* duration) {
    const std::int32_t count = row_count(schedule);
    if (renewal < 0 || renewal >= count) return false;
    if (schedule == 0) { *tau = 4 * renewal; *duration = 4; return true; }
    if (schedule == 1) { *tau = 8 * renewal; *duration = 8; return true; }
    if (schedule == 2) { *tau = 12 * renewal; *duration = 12; return true; }
    if (schedule == 3) {
        if (renewal < 24) { *tau = 4 * renewal; *duration = 4; }
        else { *tau = 96 + 12 * (renewal - 24); *duration = 12; }
        return true;
    }
    if (renewal < 8) { *tau = 12 * renewal; *duration = 12; }
    else { *tau = 96 + 4 * (renewal - 8); *duration = 4; }
    return true;
}

void reset_output(TransitionOutput* output, const Session& session) {
    std::memset(output, 0, sizeof(*output));
    std::int32_t tau = 0, duration = 0;
    schedule_row(session.schedule_id, 0, &tau, &duration);
    output->status = 0;
    output->schedule_id = session.schedule_id;
    output->renewal = -1;
    output->tau = tau;
    output->duration = duration;
    output->sector_before = session.sector;
    output->sector_after = session.sector;
    output->next_tau = tau;
    output->next_duration = duration;
    output->init_events_consumed = 1;
    output->init_event_token = session.init_token;
}

std::int32_t exact_uniform_sector(const ResetInput& input) {
    for (std::int32_t bits : {128, 256, 512, 1024}) {
        if (bits > input.prefix_bits) break;
        if (interval_below(input.init_prefix, bits, 1, 3)) return 0;
        if (interval_straddles(input.init_prefix, bits, 1, 3)) continue;
        if (interval_below(input.init_prefix, bits, 2, 3)) return 1;
        if (interval_straddles(input.init_prefix, bits, 2, 3)) continue;
        return 2;
    }
    return -1;
}
}

RISP_EXPORT std::int32_t risp_g_init_r01_abi_version() { return ABI_VERSION; }
RISP_EXPORT std::uint64_t risp_g_init_r01_fixture_magic() { return FIXTURE_MAGIC; }
RISP_EXPORT std::int32_t risp_g_init_r01_max_width() { return MAX_WIDTH; }
RISP_EXPORT std::size_t risp_g_init_r01_sizeof_reset_input() { return sizeof(ResetInput); }
RISP_EXPORT std::size_t risp_g_init_r01_sizeof_step_input() { return sizeof(StepInput); }
RISP_EXPORT std::size_t risp_g_init_r01_sizeof_extended_step_input() { return sizeof(ExtendedStepInput); }
RISP_EXPORT std::size_t risp_g_init_r01_sizeof_transition_output() { return sizeof(TransitionOutput); }

RISP_EXPORT std::int32_t risp_g_init_r01_interactive_reset_batch(
    const ResetInput* inputs, std::int32_t width, std::uint64_t* handles,
    TransitionOutput* outputs) {
    if (!inputs || !handles || !outputs || !valid_width(width)) return 10;
    for (std::int32_t i = 0; i < width; ++i) {
        if (inputs[i].magic != FIXTURE_MAGIC || inputs[i].abi_version != ABI_VERSION ||
            row_count(inputs[i].schedule_id) == 0 || inputs[i].prefix_bits != 1024 ||
            exact_uniform_sector(inputs[i]) < 0) return 11;
    }
    std::lock_guard<std::mutex> lock(sessions_mutex);
    for (std::int32_t i = 0; i < width; ++i) {
        const std::uint64_t handle = next_handle++;
        Session session{inputs[i].schedule_id, exact_uniform_sector(inputs[i]), 0,
                        1, 0, 0, 0, inputs[i].init_event_token};
        sessions.emplace(handle, session);
        handles[i] = handle;
        reset_output(&outputs[i], session);
    }
    return 0;
}

std::int32_t interactive_step_batch_impl(
    const std::uint64_t* handles, const ExtendedStepInput* inputs, std::int32_t width,
    TransitionOutput* outputs, std::int32_t expected_prefix_bits) {
    if (!handles || !inputs || !outputs || !valid_width(width)) return 20;
    std::lock_guard<std::mutex> lock(sessions_mutex);
    Session* selected[MAX_WIDTH]{};
    for (std::int32_t i = 0; i < width; ++i) {
        const auto found = sessions.find(handles[i]);
        if (found == sessions.end()) return 21;
        for (std::int32_t j = 0; j < i; ++j) if (handles[j] == handles[i]) return 22;
        const Session& session = found->second;
        if (session.renewal >= row_count(session.schedule_id) || inputs[i].action < 0 ||
            inputs[i].action > 2 || inputs[i].prefix_bits != expected_prefix_bits) return 23;
        std::int32_t tau = 0, duration = 0;
        schedule_row(session.schedule_id, session.renewal, &tau, &duration);
        const std::int32_t next_sector = exact_motion(session.sector, duration, inputs[i]);
        if (next_sector < 0) return 24;
        const std::int32_t ack_sign = exact_ack(inputs[i].action, next_sector, inputs[i]);
        if (ack_sign == 0) return 25;
        selected[i] = &found->second;
    }
    for (std::int32_t i = 0; i < width; ++i) {
        Session& session = *selected[i];
        std::int32_t tau = 0, duration = 0;
        schedule_row(session.schedule_id, session.renewal, &tau, &duration);
        const std::int32_t sector_before = session.sector;
        const std::int32_t next_sector = exact_motion(session.sector, duration, inputs[i]);
        const std::int32_t ack_sign = exact_ack(inputs[i].action, next_sector, inputs[i]);
        session.sector = next_sector;
        ++session.action_events; ++session.motion_events; ++session.ack_events;
        const std::int32_t completed = session.renewal;
        ++session.renewal;
        const bool terminal = session.renewal == row_count(session.schedule_id);
        std::int32_t next_tau = 192, next_duration = 0;
        if (!terminal) schedule_row(session.schedule_id, session.renewal, &next_tau, &next_duration);
        TransitionOutput output{};
        output.status = 0; output.schedule_id = session.schedule_id;
        output.renewal = completed; output.tau = tau; output.duration = duration;
        output.sector_before = sector_before; output.sector_after = session.sector;
        output.action = inputs[i].action; output.ack_sign = ack_sign;
        output.utility = duration * ack_sign;
        output.terminal = terminal ? 1 : 0; output.next_tau = next_tau;
        output.next_duration = next_duration;
        output.init_events_consumed = session.init_events;
        output.action_events_consumed = session.action_events;
        output.motion_events_consumed = session.motion_events;
        output.ack_events_consumed = session.ack_events;
        output.init_event_token = session.init_token;
        output.action_event_token = inputs[i].action_event_token;
        output.motion_event_token = inputs[i].motion_event_token;
        output.ack_event_token = inputs[i].ack_event_token;
        outputs[i] = output;
    }
    return 0;
}

RISP_EXPORT std::int32_t risp_g_init_r01_interactive_step_batch_extended(
    const std::uint64_t* handles, const ExtendedStepInput* inputs, std::int32_t width,
    TransitionOutput* outputs) {
    return interactive_step_batch_impl(handles, inputs, width, outputs, 1024);
}

RISP_EXPORT std::int32_t risp_g_init_r01_interactive_step_batch(
    const std::uint64_t* handles, const StepInput* inputs, std::int32_t width,
    TransitionOutput* outputs) {
    if (!inputs || !valid_width(width)) return 20;
    for (std::int32_t i = 0; i < width; ++i) {
        if (inputs[i].action < 0 || inputs[i].action > 2 || inputs[i].prefix_bits != 128) return 23;
    }
    ExtendedStepInput expanded[MAX_WIDTH]{};
    for (std::int32_t i = 0; i < width; ++i) {
        ExtendedStepInput item{};
        item.action = inputs[i].action; item.prefix_bits = 128;
        item.action_event_token = inputs[i].action_event_token;
        item.motion_event_token = inputs[i].motion_event_token;
        item.ack_event_token = inputs[i].ack_event_token;
        item.motion_prefix[0] = inputs[i].motion_prefix[0]; item.motion_prefix[1] = inputs[i].motion_prefix[1];
        item.ack_prefix[0] = inputs[i].ack_prefix[0]; item.ack_prefix[1] = inputs[i].ack_prefix[1];
        expanded[i] = item;
    }
    return interactive_step_batch_impl(handles, expanded, width, outputs, 128);
}

RISP_EXPORT std::int32_t risp_g_init_r01_interactive_close_batch(
    const std::uint64_t* handles, std::int32_t width) {
    if (!handles || !valid_width(width)) return 30;
    std::lock_guard<std::mutex> lock(sessions_mutex);
    for (std::int32_t i = 0; i < width; ++i) {
        if (sessions.find(handles[i]) == sessions.end()) return 31;
        for (std::int32_t j = 0; j < i; ++j) if (handles[j] == handles[i]) return 32;
    }
    for (std::int32_t i = 0; i < width; ++i) sessions.erase(handles[i]);
    return 0;
}
