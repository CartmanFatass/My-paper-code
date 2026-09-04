#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#ifdef _WIN32
#define TBCC_EXPORT extern "C" __declspec(dllexport)
#else
#define TBCC_EXPORT extern "C"
#endif

namespace {

constexpr std::uint64_t kMagic = 0x5442434352303241ULL;
constexpr std::int32_t kAbi = 2;
constexpr std::int32_t kMaxWidth = 144;
constexpr std::int32_t kHorizon = 364;
constexpr std::int32_t kMaxHold = 13;
constexpr std::int32_t kObservationWidth = 18;
constexpr std::int32_t kHookHandoff = 1;
constexpr std::int32_t kFormationRotate = 2;

struct ResetInput {
    std::uint64_t magic;
    std::int32_t abi_version;
    std::int32_t event_0;
    std::int32_t event_1;
    std::int32_t k_initial;
    std::int32_t k_after;
    std::int32_t switch_tick;
    std::int32_t active;
    double initial_v;
    double initial_y;
    double initial_phi;
};

struct RenewalInput {
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

struct SetupFixtureInput {
    std::uint64_t magic;
    std::int32_t abi_version;
    std::int32_t event_0;
    std::int32_t event_1;
};

struct SetupFixtureOutput {
    std::int32_t status;
    std::int32_t p[4];
    std::int32_t q;
};

struct PrimitiveFixtureInput {
    std::uint64_t magic;
    std::int32_t abi_version;
    std::int32_t q;
    std::int32_t n;
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
    std::int32_t action;
    double eta_v;
    double eta_y;
    double eta_omega;
};

struct State {
    double x = 0.0;
    double v = 0.0;
    double y = 0.0;
    double w = 0.0;
    double phi = 0.0;
    double omega = 0.0;
    std::array<double, 4> z{};
    double formation = 0.0;
    std::int32_t prior_a = 1;
    std::array<std::int32_t, 4> prior_r{};
    std::array<std::int32_t, 4> p{{1, 2, 3, 4}};
    std::int32_t q = 0;
    std::int32_t n = 0;
    std::int32_t current_k = 5;
    std::int32_t k_after = 5;
    std::int32_t switch_tick = 0;
    bool switched = false;
    bool enabled = true;
    bool terminal = false;
    bool safe_dock = false;
    bool timeout = false;
    bool cable_overload = false;
    bool gantry_contact = false;
    bool attitude_loss = false;
    bool formation_loss = false;
    double reward_sum = 0.0;
    double energy_sum = 0.0;
    std::int32_t energy_ticks = 0;
    std::int32_t dock_tick = -1;
    std::uint64_t session = 0;
    std::int32_t lane = 0;
    std::int32_t width = 0;
    HostOutput cached{};
};

std::mutex g_mutex;
std::unordered_map<std::uint64_t, State> g_states;
std::atomic<std::uint64_t> g_next_session{1};

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

bool allowed_k(std::int32_t value) {
    return value == 5 || value == 7 || value == 11 || value == 13;
}

bool compose(std::int32_t e0, std::int32_t e1, std::array<std::int32_t, 4>& p, std::int32_t& q) {
    if (!((e0 == kHookHandoff && e1 == kFormationRotate) ||
          (e0 == kFormationRotate && e1 == kHookHandoff))) {
        return false;
    }
    p = {{1, 2, 3, 4}};
    for (const auto event : {e0, e1}) {
        const auto old = p;
        if (event == kHookHandoff) {
            p = {{old[1], old[0], old[2], old[3]}};
        } else {
            p = {{old[3], old[0], old[1], old[2]}};
        }
    }
    if (p == std::array<std::int32_t, 4>{{4, 2, 1, 3}}) {
        q = 1;
        return true;
    }
    if (p == std::array<std::int32_t, 4>{{1, 4, 2, 3}}) {
        q = 0;
        return true;
    }
    return false;
}

bool valid_reset(const ResetInput& input) {
    if (input.magic != kMagic || input.abi_version != kAbi) return false;
    std::array<std::int32_t, 4> p{};
    std::int32_t q = -1;
    if (!compose(input.event_0, input.event_1, p, q)) return false;
    if (!allowed_k(input.k_initial) || !allowed_k(input.k_after)) return false;
    if (input.active != 0 && input.active != 1) return false;
    if (!finite(input.initial_v) || !finite(input.initial_y) || !finite(input.initial_phi)) return false;
    if (input.initial_v < 0.0 || input.initial_v > 0.03) return false;
    if (input.initial_y < -0.01 || input.initial_y > 0.01) return false;
    if (input.initial_phi < -0.01 || input.initial_phi > 0.01) return false;
    if (input.switch_tick == 0) return input.k_initial == input.k_after;
    if (input.switch_tick != 91 && input.switch_tick != 273) return false;
    if (!((input.k_initial == 7 && input.k_after == 13) ||
          (input.k_initial == 13 && input.k_after == 7))) return false;
    return input.switch_tick % input.k_initial == 0;
}

bool exact_disturbance(double value, double magnitude) {
    return finite(value) && std::fabs(value) == magnitude;
}

bool valid_renewal(const RenewalInput& input) {
    if ((input.active != 0 && input.active != 1) || input.action < 0 || input.action >= 18) return false;
    for (std::int32_t i = 0; i < kMaxHold; ++i) {
        if (!exact_disturbance(input.eta_v[i], 0.003) ||
            !exact_disturbance(input.eta_y[i], 0.002) ||
            !exact_disturbance(input.eta_omega[i], 0.004)) return false;
    }
    return true;
}

void maybe_switch(State& state) {
    if (state.switch_tick != 0 && !state.switched && state.n == state.switch_tick) {
        state.current_k = state.k_after;
        state.switched = true;
    }
}

void observation(const State& state, double* output) {
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

HostOutput snapshot(const State& state, std::int32_t advanced, std::int32_t hold_k,
                    const double* hold_rewards = nullptr) {
    HostOutput output{};
    output.status = 0;
    output.advanced = advanced > 0 ? 1 : 0;
    output.active = state.enabled && !state.terminal ? 1 : 0;
    output.terminal = state.terminal ? 1 : 0;
    output.ticks_advanced = advanced;
    output.n = state.n;
    output.hold_k = hold_k;
    output.next_k = state.current_k;
    output.safe_dock = state.safe_dock ? 1 : 0;
    output.timeout = state.timeout ? 1 : 0;
    output.cable_overload = state.cable_overload ? 1 : 0;
    output.gantry_contact = state.gantry_contact ? 1 : 0;
    output.attitude_loss = state.attitude_loss ? 1 : 0;
    output.formation_loss = state.formation_loss ? 1 : 0;
    observation(state, output.observation);
    output.reward_sum = state.reward_sum;
    output.energy_sum = state.energy_sum;
    output.energy_ticks = state.energy_ticks;
    output.dock_tick = state.dock_tick;
    output.last_hold_reward_count = advanced;
    for (std::int32_t i = 0; i < advanced; ++i) output.last_hold_rewards[i] = hold_rewards[i];
    return output;
}

double primitive(State& state, std::int32_t action, double eta_v, double eta_y, double eta_omega) {
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
    state.prior_r = r;
    ++state.n;

    state.cable_overload = *std::max_element(state.z.begin(), state.z.end()) > 0.25;
    const double clearance = 0.30 - std::fabs(state.y - y_ref(state.x)) - 0.55 * std::fabs(state.phi);
    state.gantry_contact = state.x >= 8.0 && state.x <= 16.0 && clearance <= 0.0;
    state.attitude_loss = std::fabs(state.phi) > 0.32;
    state.formation_loss = state.formation > 0.40;
    const bool failure = state.cable_overload || state.gantry_contact || state.attitude_loss || state.formation_loss;
    state.safe_dock = !failure && state.x >= 24.5 && std::fabs(state.y) <= 0.08
        && std::fabs(state.phi) <= 0.08
        && *std::max_element(state.z.begin(), state.z.end()) <= 0.25
        && state.formation <= 0.40;
    state.timeout = state.n >= kHorizon && !failure && !state.safe_dock;
    state.terminal = failure || state.safe_dock || state.timeout;
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

std::uint64_t handle_for(std::uint64_t session, std::int32_t lane) {
    return (session << 16U) | static_cast<std::uint64_t>(lane + 1);
}

bool validate_group(const std::uint64_t* handles, std::int32_t width,
                    std::vector<State*>& states, std::int32_t& error) {
    std::unordered_set<std::uint64_t> seen;
    std::uint64_t session = 0;
    for (std::int32_t i = 0; i < width; ++i) {
        if (!seen.insert(handles[i]).second) { error = 11; return false; }
        const auto found = g_states.find(handles[i]);
        if (found == g_states.end()) { error = 10; return false; }
        State& state = found->second;
        if (i == 0) session = state.session;
        if (state.session != session) { error = 12; return false; }
        if (state.width != width || state.lane != i) { error = 13; return false; }
        states.push_back(&state);
    }
    return true;
}

State primitive_fixture_state(const PrimitiveFixtureInput& input) {
    State state{};
    state.x = input.x; state.v = input.v; state.y = input.y; state.w = input.w;
    state.phi = input.phi; state.omega = input.omega;
    for (std::size_t i = 0; i < 4; ++i) {
        state.z[i] = input.z[i]; state.prior_r[i] = input.prior_r[i];
    }
    state.formation = input.formation; state.prior_a = input.prior_a;
    state.q = input.q; state.n = input.n; state.current_k = 1;
    return state;
}

bool valid_primitive_fixture(const PrimitiveFixtureInput& input) {
    if (input.magic != kMagic || input.abi_version != kAbi ||
        (input.q != 0 && input.q != 1) || input.n < 0 || input.n >= kHorizon ||
        input.action < 0 || input.action >= 18 || input.prior_a < 1 || input.prior_a > 2) return false;
    const double scalars[] = {input.x, input.v, input.y, input.w, input.phi,
        input.omega, input.formation, input.eta_v, input.eta_y, input.eta_omega};
    for (const auto value : scalars) if (!finite(value)) return false;
    for (const auto value : input.z) if (!finite(value)) return false;
    for (const auto value : input.prior_r) if (value < -1 || value > 1) return false;
    return exact_disturbance(input.eta_v, 0.003)
        && exact_disturbance(input.eta_y, 0.002)
        && exact_disturbance(input.eta_omega, 0.004);
}

}  // namespace

TBCC_EXPORT std::int32_t tbcc_r02_abi_version() { return kAbi; }
TBCC_EXPORT std::uint64_t tbcc_r02_fixture_magic() { return kMagic; }
TBCC_EXPORT std::int32_t tbcc_r02_max_width() { return kMaxWidth; }
TBCC_EXPORT std::size_t tbcc_r02_sizeof_reset_input() { return sizeof(ResetInput); }
TBCC_EXPORT std::size_t tbcc_r02_sizeof_renewal_input() { return sizeof(RenewalInput); }
TBCC_EXPORT std::size_t tbcc_r02_sizeof_host_output() { return sizeof(HostOutput); }
TBCC_EXPORT std::size_t tbcc_r02_sizeof_setup_fixture_input() { return sizeof(SetupFixtureInput); }
TBCC_EXPORT std::size_t tbcc_r02_sizeof_setup_fixture_output() { return sizeof(SetupFixtureOutput); }
TBCC_EXPORT std::size_t tbcc_r02_sizeof_primitive_fixture_input() { return sizeof(PrimitiveFixtureInput); }

TBCC_EXPORT std::int32_t tbcc_r02_test_setup_batch(
    const SetupFixtureInput* inputs, std::int32_t width, SetupFixtureOutput* outputs) {
    if (!inputs || !outputs || width < 1 || width > kMaxWidth) return 1;
    for (std::int32_t i = 0; i < width; ++i) {
        std::array<std::int32_t, 4> p{}; std::int32_t q = -1;
        if (inputs[i].magic != kMagic || inputs[i].abi_version != kAbi ||
            !compose(inputs[i].event_0, inputs[i].event_1, p, q)) return 2;
    }
    for (std::int32_t i = 0; i < width; ++i) {
        std::array<std::int32_t, 4> p{}; std::int32_t q = -1;
        compose(inputs[i].event_0, inputs[i].event_1, p, q);
        outputs[i] = SetupFixtureOutput{}; outputs[i].status = 0; outputs[i].q = q;
        for (std::size_t j = 0; j < 4; ++j) outputs[i].p[j] = p[j];
    }
    return 0;
}

TBCC_EXPORT std::int32_t tbcc_r02_test_primitive(
    const PrimitiveFixtureInput* input, HostOutput* output) {
    if (!input || !output) return 1;
    if (!valid_primitive_fixture(*input)) return 2;
    State state = primitive_fixture_state(*input);
    const double reward = primitive(state, input->action, input->eta_v, input->eta_y, input->eta_omega);
    *output = snapshot(state, 1, 1, &reward);
    return 0;
}

TBCC_EXPORT std::int32_t tbcc_r02_reset_batch(
    const ResetInput* inputs, std::int32_t width, std::uint64_t* handles, HostOutput* outputs) {
    if (!inputs || !handles || !outputs || width < 1 || width > kMaxWidth) return 1;
    for (std::int32_t i = 0; i < width; ++i) if (!valid_reset(inputs[i])) return 3;
    std::lock_guard<std::mutex> lock(g_mutex);
    const std::uint64_t session = g_next_session.fetch_add(1);
    if (session == 0 || session >= (1ULL << 48U)) return 4;
    for (std::int32_t i = 0; i < width; ++i) {
        State state{};
        state.v = inputs[i].initial_v; state.y = inputs[i].initial_y; state.phi = inputs[i].initial_phi;
        compose(inputs[i].event_0, inputs[i].event_1, state.p, state.q);
        state.current_k = inputs[i].k_initial; state.k_after = inputs[i].k_after;
        state.switch_tick = inputs[i].switch_tick; state.enabled = inputs[i].active == 1;
        state.session = session; state.lane = i; state.width = width;
        const auto handle = handle_for(session, i);
        state.cached = snapshot(state, 0, 0);
        g_states.emplace(handle, state); handles[i] = handle; outputs[i] = state.cached;
    }
    return 0;
}

TBCC_EXPORT std::int32_t tbcc_r02_renew_batch(
    const std::uint64_t* handles, const RenewalInput* inputs, std::int32_t width, HostOutput* outputs) {
    if (!handles || !inputs || !outputs || width < 1 || width > kMaxWidth) return 1;
    for (std::int32_t i = 0; i < width; ++i) if (!valid_renewal(inputs[i])) return 14;
    std::lock_guard<std::mutex> lock(g_mutex);
    std::vector<State*> states; states.reserve(static_cast<std::size_t>(width)); std::int32_t error = 0;
    if (!validate_group(handles, width, states, error)) return error;
    for (std::int32_t i = 0; i < width; ++i) {
        if (inputs[i].active == 1 && (!states[i]->enabled || states[i]->terminal)) return 15;
    }
    // Every input and lifecycle fact has been validated; mutation starts here.
    for (std::int32_t i = 0; i < width; ++i) {
        State& state = *states[i];
        if (inputs[i].active == 0) { outputs[i] = state.cached; continue; }
        maybe_switch(state);
        const std::int32_t held_k = state.current_k;
        const std::int32_t planned = std::min(held_k, kHorizon - state.n);
        std::int32_t advanced = 0;
        std::array<double, kMaxHold> hold_rewards{};
        for (std::int32_t tick = 0; tick < planned; ++tick) {
            hold_rewards[advanced] = primitive(
                state, inputs[i].action, inputs[i].eta_v[tick], inputs[i].eta_y[tick], inputs[i].eta_omega[tick]);
            ++advanced;
            if (state.terminal) break;
        }
        maybe_switch(state);
        state.cached = snapshot(state, advanced, held_k, hold_rewards.data());
        outputs[i] = state.cached;
    }
    return 0;
}

TBCC_EXPORT std::int32_t tbcc_r02_close_batch(const std::uint64_t* handles, std::int32_t width) {
    if (!handles || width < 1 || width > kMaxWidth) return 1;
    std::lock_guard<std::mutex> lock(g_mutex);
    std::vector<State*> states; states.reserve(static_cast<std::size_t>(width)); std::int32_t error = 0;
    if (!validate_group(handles, width, states, error)) return error;
    for (std::int32_t i = 0; i < width; ++i) g_states.erase(handles[i]);
    return 0;
}
