#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

#ifdef _WIN32
#define MF_EXPORT extern "C" __declspec(dllexport)
#else
#define MF_EXPORT extern "C"
#endif

namespace {

constexpr std::uint64_t kMagic = 0x4d4652534d4b3031ULL;
constexpr std::int32_t kAbi = 3;
constexpr std::int32_t kMaxWidth = 144;
constexpr std::int32_t kHorizon = 364;
constexpr std::int32_t kMaxHold = 13;
constexpr std::int32_t kObservationWidth = 18;
constexpr std::int32_t kHookHandoff = 1;
constexpr std::int32_t kFormationRotate = 2;
constexpr std::int32_t kOrderHR = 1;
constexpr std::int32_t kOrderRH = 2;

struct ResetInput {
    std::uint64_t magic;
    std::int32_t abi_version;
    std::int32_t k;
    std::int32_t active;
    std::int32_t pre_event_q;
    double initial_v;
    double initial_y;
    double initial_phi;
};

struct StepInput {
    std::int32_t active;
    std::int32_t action;
    double eta_v[kMaxHold];
    double eta_y[kMaxHold];
    double eta_omega[kMaxHold];
};

struct HostOutput {
    std::int32_t status;
    std::int32_t advanced;
    std::int32_t active;
    std::int32_t terminal;
    std::int32_t ticks_advanced;
    std::int32_t n;
    std::int32_t hold_k;
    std::int32_t next_k;
    std::int32_t safe_dock;
    std::int32_t timeout;
    std::int32_t cable_overload;
    std::int32_t gantry_contact;
    std::int32_t attitude_loss;
    std::int32_t formation_loss;
    double observation[kObservationWidth];
    double reward_sum;
    double energy_sum;
    std::int32_t energy_ticks;
    std::int32_t dock_tick;
    std::int32_t last_hold_reward_count;
    double last_hold_rewards[kMaxHold];
};

// This POD is the complete clone/resume state.  It deliberately contains no
// pointer, handle, mutex, RNG, Python object, or result identity.
struct NativeStateV1 {
    std::uint64_t magic;
    std::int32_t abi_version;
    std::int32_t event_phase;  // 0=pre-event, 1=post-event
    std::int32_t event_order;  // 0=none, 1=HR, 2=RH
    double x;
    double v;
    double y;
    double w;
    double phi;
    double omega;
    double z[4];
    double formation;
    std::int32_t prior_a;
    std::int32_t prior_r[4];
    std::int32_t p[4];
    std::int32_t q;
    std::int32_t n;
    std::int32_t current_k;
    std::int32_t enabled;
    std::int32_t terminal;
    std::int32_t safe_dock;
    std::int32_t timeout;
    std::int32_t cable_overload;
    std::int32_t gantry_contact;
    std::int32_t attitude_loss;
    std::int32_t formation_loss;
    double reward_sum;
    double energy_sum;
    std::int32_t energy_ticks;
    std::int32_t dock_tick;
    HostOutput cached;
};

constexpr std::int32_t kActions[18][5] = {
    {1, 0, 0, 0, 0}, {1, 1,-1, 0, 0}, {1,-1, 1, 0, 0},
    {1, 0, 0, 1,-1}, {1, 0, 0,-1, 1}, {1, 1, 0,-1, 0},
    {1,-1, 0, 1, 0}, {1, 0, 1, 0,-1}, {1, 0,-1, 0, 1},
    {2, 0, 0, 0, 0}, {2, 1,-1, 0, 0}, {2,-1, 1, 0, 0},
    {2, 0, 0, 1,-1}, {2, 0, 0,-1, 1}, {2, 1, 0,-1, 0},
    {2,-1, 0, 1, 0}, {2, 0, 1, 0,-1}, {2, 0,-1, 0, 1},
};

bool finite(double value) { return std::isfinite(value); }

double clip(double value, double low, double high) {
    return std::min(high, std::max(low, value));
}

double y_ref(double x) {
    constexpr double kPi = 3.141592653589793238462643383279502884;
    return (x >= 8.0 && x < 16.0) ? 0.18 * std::sin(kPi * (x - 8.0) / 8.0) : 0.0;
}

bool allowed_k(std::int32_t value) { return value == 7 || value == 13; }

bool exact_disturbance(double value, double magnitude) {
    return finite(value) && std::fabs(value) == magnitude;
}

bool valid_reset(const ResetInput& input) {
    return input.magic == kMagic && input.abi_version == kAbi && allowed_k(input.k)
        && (input.active == 0 || input.active == 1)
        && (input.pre_event_q == 0 || input.pre_event_q == 1)
        && finite(input.initial_v) && finite(input.initial_y) && finite(input.initial_phi)
        && input.initial_v >= 0.0 && input.initial_v <= 0.03
        && input.initial_y >= -0.01 && input.initial_y <= 0.01
        && input.initial_phi >= -0.01 && input.initial_phi <= 0.01;
}

bool valid_step(const StepInput& input) {
    if ((input.active != 0 && input.active != 1) || input.action < 0 || input.action >= 18) return false;
    for (std::int32_t i = 0; i < kMaxHold; ++i) {
        if (!exact_disturbance(input.eta_v[i], 0.003)
            || !exact_disturbance(input.eta_y[i], 0.002)
            || !exact_disturbance(input.eta_omega[i], 0.004)) return false;
    }
    return true;
}

void compose(std::int32_t order, std::int32_t* p, std::int32_t& q) {
    std::array<std::int32_t, 4> assignment{{1, 2, 3, 4}};
    const std::array<std::int32_t, 2> events = order == kOrderHR
        ? std::array<std::int32_t, 2>{{kHookHandoff, kFormationRotate}}
        : std::array<std::int32_t, 2>{{kFormationRotate, kHookHandoff}};
    for (const auto event : events) {
        const auto old = assignment;
        if (event == kHookHandoff) assignment = {{old[1], old[0], old[2], old[3]}};
        else assignment = {{old[3], old[0], old[1], old[2]}};
    }
    for (std::size_t i = 0; i < 4; ++i) p[i] = assignment[i];
    q = order == kOrderHR ? 1 : 0;
}

void observation(const NativeStateV1& state, double* output) {
    output[0] = state.x / 24.5;
    output[1] = state.v / 1.6;
    output[2] = state.y / 0.40;
    output[3] = state.w / 0.25;
    output[4] = state.phi / 0.35;
    output[5] = state.omega / 0.40;
    for (std::size_t i = 0; i < 4; ++i) output[6 + i] = state.z[i] / 0.25;
    output[10] = state.formation / 0.40;
    output[11] = static_cast<double>(state.prior_a) / 2.0;
    for (std::size_t i = 0; i < 4; ++i) output[12 + i] = static_cast<double>(state.prior_r[i]);
    output[16] = static_cast<double>(state.current_k) / 13.0;
    output[17] = static_cast<double>(state.n) / 364.0;
}

bool flag(std::int32_t value) { return value == 0 || value == 1; }

bool public_cache_coherent(const NativeStateV1& state) {
    const auto& cached = state.cached;
    if (cached.status != 0 || !flag(cached.advanced) || !flag(cached.active)
        || !flag(cached.terminal) || cached.n != state.n || cached.next_k != state.current_k
        || cached.active != (state.enabled && !state.terminal ? 1 : 0)
        || cached.terminal != state.terminal || cached.safe_dock != state.safe_dock
        || cached.timeout != state.timeout || cached.cable_overload != state.cable_overload
        || cached.gantry_contact != state.gantry_contact || cached.attitude_loss != state.attitude_loss
        || cached.formation_loss != state.formation_loss || cached.reward_sum != state.reward_sum
        || cached.energy_sum != state.energy_sum || cached.energy_ticks != state.energy_ticks
        || cached.dock_tick != state.dock_tick || cached.ticks_advanced < 0
        || cached.ticks_advanced > kMaxHold
        || cached.last_hold_reward_count != cached.ticks_advanced
        || cached.advanced != (cached.ticks_advanced > 0 ? 1 : 0)) return false;
    if (cached.hold_k != 0 && cached.hold_k != state.current_k) return false;
    double expected[kObservationWidth]{};
    observation(state, expected);
    for (std::int32_t i = 0; i < kObservationWidth; ++i) {
        if (!finite(cached.observation[i]) || cached.observation[i] != expected[i]) return false;
    }
    for (std::int32_t i = 0; i < kMaxHold; ++i) {
        if (!finite(cached.last_hold_rewards[i])) return false;
        if (i >= cached.last_hold_reward_count && cached.last_hold_rewards[i] != 0.0) return false;
    }
    return true;
}

bool valid_state(const NativeStateV1& state) {
    if (state.magic != kMagic || state.abi_version != kAbi || !allowed_k(state.current_k)
        || state.n < 0 || state.n > kHorizon || state.energy_ticks != state.n
        || !flag(state.enabled) || !flag(state.terminal) || !flag(state.safe_dock)
        || !flag(state.timeout) || !flag(state.cable_overload) || !flag(state.gantry_contact)
        || !flag(state.attitude_loss) || !flag(state.formation_loss)
        || state.prior_a < 1 || state.prior_a > 2 || state.dock_tick < -1
        || !finite(state.x) || !finite(state.v) || !finite(state.y) || !finite(state.w)
        || !finite(state.phi) || !finite(state.omega) || !finite(state.formation)
        || !finite(state.reward_sum) || !finite(state.energy_sum)) return false;
    for (const auto value : state.z) if (!finite(value)) return false;
    for (const auto value : state.prior_r) if (value < -1 || value > 1) return false;
    const bool failure = state.cable_overload || state.gantry_contact
        || state.attitude_loss || state.formation_loss;
    if (state.terminal != (failure || state.safe_dock || state.timeout ? 1 : 0)
        || (state.safe_dock && (failure || state.timeout || state.dock_tick != state.n))
        || (!state.safe_dock && state.dock_tick != -1)
        || (state.timeout && (failure || state.safe_dock || state.n != kHorizon))) return false;
    const std::array<std::int32_t, 4> p{{state.p[0], state.p[1], state.p[2], state.p[3]}};
    if (state.event_phase == 0) {
        if (state.event_order != 0 || !flag(state.q)
            || p != std::array<std::int32_t, 4>{{1, 2, 3, 4}}) return false;
    } else if (state.event_phase == 1 && state.event_order == kOrderHR) {
        if (state.q != 1 || p != std::array<std::int32_t, 4>{{4, 2, 1, 3}}) return false;
    } else if (state.event_phase == 1 && state.event_order == kOrderRH) {
        if (state.q != 0 || p != std::array<std::int32_t, 4>{{1, 4, 2, 3}}) return false;
    } else {
        return false;
    }
    return public_cache_coherent(state);
}

HostOutput snapshot(const NativeStateV1& state, std::int32_t advanced, std::int32_t hold_k,
                    const double* rewards = nullptr) {
    HostOutput output{};
    output.status = 0;
    output.advanced = advanced > 0 ? 1 : 0;
    output.active = state.enabled == 1 && state.terminal == 0 ? 1 : 0;
    output.terminal = state.terminal;
    output.ticks_advanced = advanced;
    output.n = state.n;
    output.hold_k = hold_k;
    output.next_k = state.current_k;
    output.safe_dock = state.safe_dock;
    output.timeout = state.timeout;
    output.cable_overload = state.cable_overload;
    output.gantry_contact = state.gantry_contact;
    output.attitude_loss = state.attitude_loss;
    output.formation_loss = state.formation_loss;
    observation(state, output.observation);
    output.reward_sum = state.reward_sum;
    output.energy_sum = state.energy_sum;
    output.energy_ticks = state.energy_ticks;
    output.dock_tick = state.dock_tick;
    output.last_hold_reward_count = advanced;
    for (std::int32_t i = 0; i < advanced; ++i) output.last_hold_rewards[i] = rewards[i];
    return output;
}

double primitive(NativeStateV1& state, std::int32_t action,
                 double eta_v, double eta_y, double eta_omega) {
    const auto* spec = kActions[action];
    const std::int32_t a = spec[0];
    const std::array<std::int32_t, 4> r{{spec[1], spec[2], spec[3], spec[4]}};
    const std::array<double, 4> b = state.q == 1
        ? std::array<double, 4>{{1.0, -1.0, 0.0, 0.0}}
        : std::array<double, 4>{{0.0, 0.0, 1.0, -1.0}};
    const double old_x = state.x;
    const double e = state.y - y_ref(state.x);
    std::array<double, 4> tau{};
    for (std::size_t i = 0; i < 4; ++i) {
        tau[i] = 0.38 + 0.12 * a + 0.16 * a * std::max(b[i], 0.0)
            - 0.10 * r[i] + 0.04 * std::fabs(state.phi) + 0.03 * std::fabs(e);
    }
    const double tau_bar = (tau[0] + tau[1] + tau[2] + tau[3]) / 4.0;
    double mu = 0.0;
    for (std::size_t i = 0; i < 4; ++i) mu += b[i] * (tau[i] - tau_bar);
    mu *= 0.5;
    const double nu = 0.25 * (r[0] + r[3] - r[1] - r[2]);
    const double old_phi = state.phi;
    state.omega = 0.90 * state.omega - 0.12 * state.phi + 0.08 * mu + 0.02 * state.w + eta_omega;
    state.phi = clip(state.phi + 0.1 * state.omega, -0.50, 0.50);
    state.w = 0.88 * state.w - 0.10 * e - 0.03 * old_phi + 0.025 * nu + eta_y;
    state.y += 0.1 * state.w;
    state.v = clip(0.92 * state.v + 0.08 * (0.75 * a)
        - 0.02 * std::fabs(state.phi) - 0.02 * std::fabs(e) + eta_v, 0.0, 1.60);
    state.x += 0.1 * state.v;
    for (std::size_t i = 0; i < 4; ++i) {
        state.z[i] = 0.84 * state.z[i] + std::max(0.0, tau[i] - 0.88);
    }
    state.formation = 0.86 * state.formation
        + 0.04 * std::max({std::abs(r[0]), std::abs(r[1]), std::abs(r[2]), std::abs(r[3])})
        + 0.05 * std::fabs(state.phi) + 0.04 * std::fabs(e);
    state.prior_a = a;
    for (std::size_t i = 0; i < 4; ++i) state.prior_r[i] = r[i];
    ++state.n;

    state.cable_overload = *std::max_element(state.z, state.z + 4) > 0.25 ? 1 : 0;
    const double clearance = 0.30 - std::fabs(state.y - y_ref(state.x)) - 0.55 * std::fabs(state.phi);
    state.gantry_contact = state.x >= 8.0 && state.x <= 16.0 && clearance <= 0.0 ? 1 : 0;
    state.attitude_loss = std::fabs(state.phi) > 0.32 ? 1 : 0;
    state.formation_loss = state.formation > 0.40 ? 1 : 0;
    const bool failure = state.cable_overload || state.gantry_contact || state.attitude_loss || state.formation_loss;
    state.safe_dock = !failure && state.x >= 24.5 && std::fabs(state.y) <= 0.08
        && std::fabs(state.phi) <= 0.08
        && *std::max_element(state.z, state.z + 4) <= 0.25
        && state.formation <= 0.40 ? 1 : 0;
    state.timeout = state.n >= kHorizon && !failure && !state.safe_dock ? 1 : 0;
    state.terminal = failure || state.safe_dock || state.timeout ? 1 : 0;
    if (state.safe_dock) state.dock_tick = state.n;

    double energy = 0.0;
    for (const auto value : r) energy += std::pow(a + 0.35 * value, 2.0);
    energy /= 4.0;
    double reward = 0.015 * (state.x - old_x) - 0.001 * energy
        - 0.002 * state.phi * state.phi
        - 0.002 * std::pow(state.y - y_ref(state.x), 2.0);
    if (state.safe_dock) reward += 1.0;
    else if (failure) reward -= 1.0;
    else if (state.timeout) reward -= 0.4;
    state.reward_sum += reward;
    state.energy_sum += energy;
    ++state.energy_ticks;
    return reward;
}

void advance_hold(NativeStateV1& state, const StepInput& input, HostOutput& output) {
    if (input.active == 0) {
        output = state.cached;
        return;
    }
    const auto held_k = state.current_k;
    const auto planned = std::min(held_k, kHorizon - state.n);
    std::array<double, kMaxHold> rewards{};
    std::int32_t advanced = 0;
    for (std::int32_t tick = 0; tick < planned; ++tick) {
        rewards[advanced] = primitive(state, input.action, input.eta_v[tick],
                                      input.eta_y[tick], input.eta_omega[tick]);
        ++advanced;
        if (state.terminal) break;
    }
    state.cached = snapshot(state, advanced, held_k, rewards.data());
    output = state.cached;
}

}  // namespace

MF_EXPORT std::int32_t mf_rs_abi_version() { return kAbi; }
MF_EXPORT std::uint64_t mf_rs_magic() { return kMagic; }
MF_EXPORT std::int32_t mf_rs_max_width() { return kMaxWidth; }
MF_EXPORT std::size_t mf_rs_sizeof_reset_input() { return sizeof(ResetInput); }
MF_EXPORT std::size_t mf_rs_sizeof_step_input() { return sizeof(StepInput); }
MF_EXPORT std::size_t mf_rs_sizeof_host_output() { return sizeof(HostOutput); }
MF_EXPORT std::size_t mf_rs_sizeof_native_state() { return sizeof(NativeStateV1); }

MF_EXPORT std::int32_t mf_rs_reset_batch(const ResetInput* inputs, std::int32_t width,
                                         NativeStateV1* states, HostOutput* outputs) {
    if (!inputs || !states || !outputs || width < 1 || width > kMaxWidth) return 1;
    for (std::int32_t i = 0; i < width; ++i) if (!valid_reset(inputs[i])) return 2;
    for (std::int32_t i = 0; i < width; ++i) {
        NativeStateV1 state{};
        state.magic = kMagic;
        state.abi_version = kAbi;
        state.event_phase = 0;
        state.event_order = 0;
        state.v = inputs[i].initial_v;
        state.y = inputs[i].initial_y;
        state.phi = inputs[i].initial_phi;
        state.prior_a = 1;
        // Treatment-common SOURCE prefix precedes the event intervention.
        // p is identity and q is the manifest-frozen cell bit.
        state.p[0] = 1; state.p[1] = 2; state.p[2] = 3; state.p[3] = 4;
        state.q = inputs[i].pre_event_q;
        state.current_k = inputs[i].k;
        state.enabled = inputs[i].active;
        state.dock_tick = -1;
        state.cached = snapshot(state, 0, 0);
        states[i] = state;
        outputs[i] = state.cached;
    }
    return 0;
}

MF_EXPORT std::int32_t mf_rs_validate_state_batch(const NativeStateV1* states, std::int32_t width) {
    if (!states || width < 1 || width > kMaxWidth) return 1;
    for (std::int32_t i = 0; i < width; ++i) if (!valid_state(states[i])) return 2;
    return 0;
}

MF_EXPORT std::int32_t mf_rs_step_batch(NativeStateV1* states, const StepInput* inputs,
                                        std::int32_t width, HostOutput* outputs) {
    if (!states || !inputs || !outputs || width < 1 || width > kMaxWidth) return 1;
    for (std::int32_t i = 0; i < width; ++i) {
        if (!valid_state(states[i]) || !valid_step(inputs[i])) return 2;
        if (inputs[i].active == 1 && (!states[i].enabled || states[i].terminal)) return 3;
    }
    for (std::int32_t i = 0; i < width; ++i) {
        advance_hold(states[i], inputs[i], outputs[i]);
    }
    return 0;
}

// Pure ABI3 technical proof.  The supplied source is copied, the copy advances
// through the exact production hold semantics above, and only measured outputs
// are written.  No caller-owned state, session, RNG, or result object advances.
MF_EXPORT std::int32_t mf_rs_verify_transition(const NativeStateV1* source,
                                               const StepInput* input,
                                               const NativeStateV1* expected,
                                               NativeStateV1* measured,
                                               HostOutput* output) {
    if (!source || !input || !expected || !measured || !output) return 1;
    if (!valid_state(*source) || !valid_step(*input)) return 2;
    if (input->active == 1 && (!source->enabled || source->terminal)) return 3;
    NativeStateV1 local = *source;
    advance_hold(local, *input, *output);
    *measured = local;
    return std::memcmp(&local, expected, sizeof(NativeStateV1)) == 0 ? 0 : 4;
}

MF_EXPORT std::int32_t mf_rs_apply_order_batch(NativeStateV1* states, const std::int32_t* orders,
                                               std::int32_t width, HostOutput* outputs) {
    if (!states || !orders || !outputs || width < 1 || width > kMaxWidth) return 1;
    for (std::int32_t i = 0; i < width; ++i) {
        if (!valid_state(states[i]) || states[i].terminal || states[i].event_phase != 0 ||
            (orders[i] != kOrderHR && orders[i] != kOrderRH)) return 2;
    }
    for (std::int32_t i = 0; i < width; ++i) {
        auto& state = states[i];
        compose(orders[i], state.p, state.q);
        state.event_phase = 1;
        state.event_order = orders[i];
        // LEVEL_RELEASE clears only nonpersistent event scratch.  This host
        // stores none, so every persistent coordinate (including z) is inert.
        state.cached = snapshot(state, 0, 0);
        outputs[i] = state.cached;
    }
    return 0;
}
