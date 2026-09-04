#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace py = pybind11;

namespace {

constexpr const char* kAbi = "SGSP_RSCF_NATIVE_ABI_V4_FP32";
constexpr const char* kHostKind = "RIDGEGATE_2Z_RSCF_FACTUAL_TRACE_AND_FULL_SUFFIX_CPU_TEST_V4_FP32";
constexpr int64_t kHorizon = 12;
constexpr int64_t kMaxAgents = 21;
constexpr int64_t kFifo = 4;
constexpr int64_t kMaxScheduled = 32;
constexpr int64_t kMetricDim = 8;
constexpr int64_t kHidden = 64;
constexpr int64_t kObs = 22;
constexpr int64_t kMessage = 32;
constexpr int64_t kActions = 6;
constexpr int64_t kActorInput = 55;

constexpr int64_t ROLE_WEST = 0;
constexpr int64_t ROLE_EAST = 1;
constexpr int64_t ROLE_RELAY = 2;
constexpr int64_t ACTION_SCAN = 0;
constexpr int64_t ACTION_UPLINK = 1;
constexpr int64_t ACTION_LISTEN_WEST = 2;
constexpr int64_t ACTION_LISTEN_EAST = 3;
constexpr int64_t ACTION_FORWARD_BASE = 4;
constexpr int64_t ACTION_HOLD = 5;
constexpr int64_t SCHEDULE_UPLINK = 1;
constexpr int64_t SCHEDULE_BASE = 2;

constexpr int64_t METRIC_NEW_TIMELY = 0;
constexpr int64_t METRIC_DUPLICATE = 1;
constexpr int64_t METRIC_EXPIRED = 2;
constexpr int64_t METRIC_COLLISION = 3;
constexpr int64_t METRIC_EMPTY = 4;
constexpr int64_t METRIC_RADIO = 5;
constexpr int64_t METRIC_WASTE = 6;
constexpr int64_t METRIC_DECODED = 7;

constexpr uint64_t kFnvOffset = 1469598103934665603ULL;
constexpr uint64_t kFnvPrime = 1099511628211ULL;

template <typename T>
py::array_t<T> require_array(
    const py::dict& values,
    const char* name,
    const std::vector<py::ssize_t>& shape,
    bool readonly = true) {
  if (!values.contains(name)) {
    throw std::invalid_argument(std::string("missing array: ") + name);
  }
  py::object object = values[name];
  if (!py::isinstance<py::array>(object)) {
    throw std::invalid_argument(std::string(name) + " must be a numpy array");
  }
  py::array array = py::reinterpret_borrow<py::array>(object);
  if (!array.dtype().is(py::dtype::of<T>())) {
    throw std::invalid_argument(std::string(name) + " has wrong dtype");
  }
  if (array.ndim() != static_cast<py::ssize_t>(shape.size())) {
    throw std::invalid_argument(std::string(name) + " has wrong rank");
  }
  for (py::ssize_t axis = 0; axis < array.ndim(); ++axis) {
    if (array.shape(axis) != shape[static_cast<size_t>(axis)]) {
      throw std::invalid_argument(std::string(name) + " has wrong shape");
    }
  }
  if ((array.flags() & py::array::c_style) == 0) {
    throw std::invalid_argument(std::string(name) + " must be C-contiguous");
  }
  if (readonly && array.writeable()) {
    throw std::invalid_argument(std::string(name) + " must be immutable/read-only");
  }
  return py::reinterpret_borrow<py::array_t<T>>(array);
}

template <typename T>
void require_finite(const py::array_t<T>&) {}

template <>
void require_finite<float>(const py::array_t<float>& array) {
  const float* data = array.data();
  for (py::ssize_t index = 0; index < array.size(); ++index) {
    if (!std::isfinite(data[index])) {
      throw std::invalid_argument("nonfinite native input");
    }
  }
}

uint64_t fnv_bytes(uint64_t value, const void* data, size_t size) {
  const auto* bytes = static_cast<const uint8_t*>(data);
  for (size_t index = 0; index < size; ++index) {
    value ^= bytes[index];
    value *= kFnvPrime;
  }
  return value;
}

uint64_t fnv_i64(uint64_t value, int64_t item) {
  return fnv_bytes(value, &item, sizeof(item));
}

uint64_t fnv_u64(uint64_t value, uint64_t item) {
  return fnv_bytes(value, &item, sizeof(item));
}

uint64_t fnv_f32(uint64_t value, float item) {
  return fnv_bytes(value, &item, sizeof(item));
}

uint64_t fnv_canonical_f32(uint64_t value, float item) {
  const int64_t quantized = static_cast<int64_t>(std::llround(item * 1.0e8f));
  return fnv_i64(value, quantized);
}

float sigmoid(float value) { return 1.0f / (1.0f + std::exp(-value)); }

float link_probability(float base, int64_t multiplicity) {
  const float logit = std::log(base / (1.0f - base));
  return sigmoid(logit - 0.22f * static_cast<float>(multiplicity - 1));
}

const std::array<float, 9> P0 = {
    0.92f, 0.48f, 0.88f,
    0.48f, 0.92f, 0.82f,
    0.86f, 0.78f, 0.90f};
const std::array<float, 9> LATENCY = {
    1.0f, 2.0f, 1.0f,
    2.0f, 1.0f, 1.0f,
    1.0f, 1.0f, 1.0f};
const std::array<int64_t, 3> ROTATED_SOURCE_COLUMN = {2, 0, 1};

std::array<int64_t, 4> legal_actions(int64_t role, int64_t* count) {
  if (role == ROLE_WEST || role == ROLE_EAST) {
    *count = 3;
    return {ACTION_SCAN, ACTION_UPLINK, ACTION_HOLD, -1};
  }
  if (role == ROLE_RELAY) {
    *count = 4;
    return {ACTION_LISTEN_WEST, ACTION_LISTEN_EAST, ACTION_FORWARD_BASE, ACTION_HOLD};
  }
  throw std::invalid_argument("invalid role");
}

bool is_legal(int64_t role, int64_t action) {
  int64_t count = 0;
  const auto legal = legal_actions(role, &count);
  for (int64_t index = 0; index < count; ++index) {
    if (legal[index] == action) {
      return true;
    }
  }
  return false;
}

struct Scheduled {
  int64_t kind;
  int64_t due;
  int64_t sender;
  int64_t receiver;
  int64_t basin;
  int64_t ordinal;
  int64_t birth;
};

struct Packet {
  int64_t basin = -1;
  int64_t ordinal = -1;
  int64_t birth = -1;

  bool valid() const { return birth >= 0; }
  bool operator==(const Packet& other) const {
    return basin == other.basin && ordinal == other.ordinal && birth == other.birth;
  }
};

struct LaneState {
  int64_t n = 0;
  std::array<int64_t, kMaxAgents> roles{};
  std::array<Packet, kMaxAgents * kFifo> fifo{};
  std::array<int64_t, 6> delivered{};
  std::array<int64_t, kMetricDim> metrics{};
  std::array<int64_t, kMaxAgents> previous_action{};
  std::array<int64_t, kMaxAgents> previous_success{};
  std::array<int64_t, 6> events{};
  std::array<float, kMaxAgents * kHidden> hidden{};
  std::vector<Scheduled> scheduled;

  Packet& packet(int64_t agent, int64_t position) {
    return fifo[static_cast<size_t>(agent * kFifo + position)];
  }
  const Packet& packet(int64_t agent, int64_t position) const {
    return fifo[static_cast<size_t>(agent * kFifo + position)];
  }
};

Packet fifo_head(const LaneState& state, int64_t agent) {
  return state.packet(agent, 0);
}

void fifo_remove_head(LaneState& state, int64_t agent, const Packet& expected) {
  if (!(state.packet(agent, 0) == expected)) {
    throw std::runtime_error("scheduled acknowledgement does not match FIFO head");
  }
  for (int64_t position = 0; position < kFifo - 1; ++position) {
    state.packet(agent, position) = state.packet(agent, position + 1);
  }
  state.packet(agent, kFifo - 1) = Packet{};
}

void fifo_append(LaneState& state, int64_t agent, int64_t capacity, const Packet& packet) {
  int64_t empty = -1;
  for (int64_t position = 0; position < capacity; ++position) {
    if (!state.packet(agent, position).valid()) {
      empty = position;
      break;
    }
  }
  if (empty < 0) {
    for (int64_t position = 0; position < capacity - 1; ++position) {
      state.packet(agent, position) = state.packet(agent, position + 1);
    }
    empty = capacity - 1;
  }
  state.packet(agent, empty) = packet;
}

void purge_expired(LaneState& state, int64_t slot) {
  for (int64_t agent = 0; agent < state.n; ++agent) {
    const int64_t capacity = state.roles[agent] == ROLE_RELAY ? 4 : 2;
    std::array<Packet, kFifo> kept{};
    int64_t count = 0;
    for (int64_t position = 0; position < capacity; ++position) {
      const Packet packet = state.packet(agent, position);
      if (packet.valid() && slot < packet.birth + 4) {
        kept[count++] = packet;
      }
    }
    for (int64_t position = 0; position < kFifo; ++position) {
      state.packet(agent, position) = position < count ? kept[position] : Packet{};
    }
  }
}

void process_arrivals(LaneState& state, int64_t slot) {
  std::vector<Scheduled> remaining;
  std::set<std::tuple<int64_t, int64_t, int64_t, int64_t, int64_t>> removed;
  for (const Scheduled& entry : state.scheduled) {
    if (entry.due != slot) {
      remaining.push_back(entry);
      continue;
    }
    const Packet packet{entry.basin, entry.ordinal, entry.birth};
    const auto key = std::make_tuple(entry.kind, entry.sender, entry.basin, entry.ordinal, entry.birth);
    if (removed.insert(key).second) {
      fifo_remove_head(state, entry.sender, packet);
    }
    state.metrics[METRIC_DECODED] += 1;
    if (slot >= entry.birth + 4) {
      state.metrics[METRIC_EXPIRED] += 1;
      continue;
    }
    if (entry.kind == SCHEDULE_UPLINK) {
      fifo_append(state, entry.receiver, 4, packet);
      state.previous_success[entry.sender] = 1;
      state.previous_success[entry.receiver] = 1;
    } else if (entry.kind == SCHEDULE_BASE) {
      const size_t delivered_index = static_cast<size_t>(entry.basin * 3 + entry.ordinal);
      if (state.delivered[delivered_index] != 0) {
        state.metrics[METRIC_DUPLICATE] += 1;
      } else {
        state.delivered[delivered_index] = 1;
        state.metrics[METRIC_NEW_TIMELY] += 1;
        state.previous_success[entry.sender] = 1;
      }
    } else {
      throw std::runtime_error("unsupported scheduled kind");
    }
  }
  state.scheduled.swap(remaining);
}

struct Parameters {
  const float* encoder_w1;
  const float* encoder_b1;
  const float* encoder_w2;
  const float* encoder_b2;
  const float* beta;
  const float* gru_w;
  const float* gru_u;
  const float* gru_b;
  const float* actor_w;
  const float* actor_b;
};

void form_observations(const LaneState& state, int64_t slot, std::vector<float>& observations) {
  observations.assign(static_cast<size_t>(state.n * kObs), 0.0f);
  const float normalized_count = (static_cast<float>(state.n) / 3.0f) / 7.0f;
  for (int64_t agent = 0; agent < state.n; ++agent) {
    float* obs = observations.data() + agent * kObs;
    obs[state.roles[agent]] = 1.0f;
    obs[3] = static_cast<float>(slot) / 11.0f;
    obs[4] = normalized_count;
    obs[5] = normalized_count;
    obs[6] = normalized_count;
    for (int64_t position = 0; position < kFifo; ++position) {
      const Packet packet = state.packet(agent, position);
      if (packet.valid()) {
        obs[7 + 2 * position] = 1.0f;
        const int64_t age = std::min<int64_t>(std::max<int64_t>(slot - packet.birth, 0), 3);
        obs[8 + 2 * position] = static_cast<float>(age) / 3.0f;
      }
    }
    if (state.previous_action[agent] >= 0) {
      obs[15 + state.previous_action[agent]] = 1.0f;
    }
    obs[21] = static_cast<float>(state.previous_success[agent]);
  }
}

void policy_step(
    LaneState& state,
    const Parameters& p,
    const std::vector<float>& observations,
    const float* action_uniform,
    std::array<int64_t, kMaxAgents>& actions,
    int64_t mode = 0,
    float* messages_output = nullptr,
    float* summaries_output = nullptr,
    float* denominators_output = nullptr,
    float* probabilities_output = nullptr,
    const float* messages_override = nullptr) {
  if (mode != 0 && mode != 1) {
    throw std::invalid_argument("unsupported policy mode");
  }
  std::vector<float> messages(static_cast<size_t>(state.n * kMessage));
  std::array<float, 64> layer{};
  std::array<float, 3 * kMessage> role_sums{};
  std::array<int64_t, 3> counts{};
  for (int64_t agent = 0; agent < state.n; ++agent) {
    counts[state.roles[agent]] += 1;
    if (messages_override == nullptr) {
      for (int64_t out = 0; out < 64; ++out) {
        float value = p.encoder_b1[out];
        for (int64_t input = 0; input < kObs; ++input) {
          value += p.encoder_w1[out * kObs + input] * observations[agent * kObs + input];
        }
        layer[out] = std::tanh(value);
      }
    }
    for (int64_t out = 0; out < kMessage; ++out) {
      float message = 0.0f;
      if (messages_override == nullptr) {
        float value = p.encoder_b2[out];
        for (int64_t input = 0; input < 64; ++input) {
          value += p.encoder_w2[out * 64 + input] * layer[input];
        }
        message = std::tanh(value);
      } else {
        message = messages_override[agent * kMessage + out];
      }
      messages[agent * kMessage + out] = message;
      if (messages_output != nullptr) {
        messages_output[agent * kMessage + out] = message;
      }
      role_sums[state.roles[agent] * kMessage + out] += message;
    }
  }

  std::array<float, 9> omega{};
  for (int64_t receiver = 0; receiver < 3; ++receiver) {
    for (int64_t sender = 0; sender < 3; ++sender) {
      const int64_t multiplicity = counts[sender];
      const size_t edge = static_cast<size_t>(receiver * 3 + sender);
      const int64_t physical_sender = mode == 0 ? sender : ROTATED_SOURCE_COLUMN[sender];
      const size_t physical_edge = static_cast<size_t>(receiver * 3 + physical_sender);
      const float probability = link_probability(P0[physical_edge], multiplicity);
      const float k0 = probability / LATENCY[physical_edge];
      const float v =
          (2.0f * std::log(static_cast<float>(multiplicity)) - std::log(14.0f)) /
          std::log(7.0f / 2.0f);
      const float residual = p.beta[edge * 2] + p.beta[edge * 2 + 1] * v;
      omega[edge] = k0 * std::exp(residual);
    }
  }

  std::array<float, kActorInput> actor_input{};
  std::array<float, kHidden> reset_hidden{};
  std::array<float, kHidden> z{};
  std::array<float, kHidden> r{};
  std::array<float, kHidden> candidate{};
  for (int64_t agent = 0; agent < state.n; ++agent) {
    const int64_t receiver = state.roles[agent];
    for (int64_t index = 0; index < kObs; ++index) {
      actor_input[index] = observations[agent * kObs + index];
    }
    float denominator = 0.0f;
    for (int64_t sender = 0; sender < 3; ++sender) {
      denominator += static_cast<float>(counts[sender]) * omega[receiver * 3 + sender];
    }
    for (int64_t component = 0; component < kMessage; ++component) {
      float numerator = 0.0f;
      for (int64_t sender = 0; sender < 3; ++sender) {
        numerator += omega[receiver * 3 + sender] * role_sums[sender * kMessage + component];
      }
      actor_input[kObs + component] = numerator / (denominator + 1e-12f);
    }
    actor_input[54] = denominator;
    if (denominators_output != nullptr) {
      denominators_output[agent] = denominator;
    }
    if (summaries_output != nullptr) {
      for (int64_t component = 0; component < kMessage; ++component) {
        summaries_output[agent * kMessage + component] = actor_input[kObs + component];
      }
    }

    const float* prior_hidden = state.hidden.data() + agent * kHidden;
    for (int64_t unit = 0; unit < kHidden; ++unit) {
      float z_value = p.gru_b[unit];
      float r_value = p.gru_b[kHidden + unit];
      for (int64_t input = 0; input < kActorInput; ++input) {
        z_value += p.gru_w[(0 * kHidden + unit) * kActorInput + input] * actor_input[input];
        r_value += p.gru_w[(1 * kHidden + unit) * kActorInput + input] * actor_input[input];
      }
      for (int64_t input = 0; input < kHidden; ++input) {
        z_value += p.gru_u[(0 * kHidden + unit) * kHidden + input] * prior_hidden[input];
        r_value += p.gru_u[(1 * kHidden + unit) * kHidden + input] * prior_hidden[input];
      }
      z[unit] = sigmoid(z_value);
      r[unit] = sigmoid(r_value);
      reset_hidden[unit] = r[unit] * prior_hidden[unit];
    }
    for (int64_t unit = 0; unit < kHidden; ++unit) {
      float value = p.gru_b[2 * kHidden + unit];
      for (int64_t input = 0; input < kActorInput; ++input) {
        value += p.gru_w[(2 * kHidden + unit) * kActorInput + input] * actor_input[input];
      }
      for (int64_t input = 0; input < kHidden; ++input) {
        value += p.gru_u[(2 * kHidden + unit) * kHidden + input] * reset_hidden[input];
      }
      candidate[unit] = std::tanh(value);
    }
    float* next_hidden = state.hidden.data() + agent * kHidden;
    for (int64_t unit = 0; unit < kHidden; ++unit) {
      next_hidden[unit] = (1.0f - z[unit]) * candidate[unit] + z[unit] * prior_hidden[unit];
    }

    std::array<float, kActions> logits{};
    for (int64_t action = 0; action < kActions; ++action) {
      float value = p.actor_b[action];
      for (int64_t unit = 0; unit < kHidden; ++unit) {
        value += p.actor_w[action * kHidden + unit] * next_hidden[unit];
      }
      logits[action] = value;
    }
    int64_t legal_count = 0;
    const auto legal = legal_actions(receiver, &legal_count);
    float maximum = -std::numeric_limits<float>::infinity();
    for (int64_t index = 0; index < legal_count; ++index) {
      maximum = std::max(maximum, logits[legal[index]]);
    }
    std::array<float, 4> probability{};
    if (probabilities_output != nullptr) {
      for (int64_t action = 0; action < kActions; ++action) {
        probabilities_output[agent * kActions + action] = 0.0f;
      }
    }
    float total = 0.0f;
    for (int64_t index = 0; index < legal_count; ++index) {
      probability[index] = std::exp(logits[legal[index]] - maximum);
      total += probability[index];
    }
    std::array<float, 4> executed_probability{};
    for (int64_t index = 0; index < legal_count; ++index) {
      executed_probability[index] =
          0.96f * probability[index] / total + 0.04f / legal_count;
      if (probabilities_output != nullptr) {
        probabilities_output[agent * kActions + legal[index]] = executed_probability[index];
      }
    }
    float cumulative = 0.0f;
    actions[agent] = legal[legal_count - 1];
    for (int64_t index = 0; index < legal_count; ++index) {
      cumulative += executed_probability[index];
      if (action_uniform[agent] < cumulative) {
        actions[agent] = legal[index];
        break;
      }
    }
  }
}

void schedule_radio(
    LaneState& state,
    int64_t slot,
    const std::array<int64_t, kMaxAgents>& actions,
    const float* uplink_uniform,
    const float* base_uniform) {
  const int64_t per_role = state.n / 3;
  for (int64_t agent = 0; agent < state.n; ++agent) {
    const int64_t action = actions[agent];
    if (action == ACTION_UPLINK || action == ACTION_LISTEN_WEST ||
        action == ACTION_LISTEN_EAST || action == ACTION_FORWARD_BASE) {
      state.metrics[METRIC_RADIO] += 1;
    }
  }

  for (int64_t basin = 0; basin < 2; ++basin) {
    const int64_t surveyor_role = basin;
    const int64_t listen_action = basin == 0 ? ACTION_LISTEN_WEST : ACTION_LISTEN_EAST;
    std::vector<int64_t> uplink_agents;
    std::vector<int64_t> nonempty;
    std::vector<int64_t> listeners;
    for (int64_t agent = 0; agent < state.n; ++agent) {
      if (state.roles[agent] == surveyor_role && actions[agent] == ACTION_UPLINK) {
        uplink_agents.push_back(agent);
        if (fifo_head(state, agent).valid()) {
          nonempty.push_back(agent);
        }
      }
      if (state.roles[agent] == ROLE_RELAY && actions[agent] == listen_action) {
        listeners.push_back(agent);
      }
    }
    for (const int64_t agent : uplink_agents) {
      if (!fifo_head(state, agent).valid()) {
        state.metrics[METRIC_EMPTY] += 1;
        state.metrics[METRIC_WASTE] += 1;
      }
    }
    if (nonempty.size() != 1) {
      if (nonempty.size() >= 2) {
        state.metrics[METRIC_COLLISION] += static_cast<int64_t>(nonempty.size());
        state.metrics[METRIC_WASTE] += static_cast<int64_t>(nonempty.size());
      }
      state.metrics[METRIC_WASTE] += static_cast<int64_t>(listeners.size());
      continue;
    }
    const int64_t sender = nonempty[0];
    const Packet packet = fifo_head(state, sender);
    if (packet.basin != basin) {
      throw std::runtime_error("surveyor FIFO packet basin mismatches public role");
    }
    const int64_t due = slot + 1;
    std::set<int64_t> decoded_nonexpired;
    if (slot < kHorizon - 1) {
      const float probability = link_probability(P0[ROLE_RELAY * 3 + surveyor_role], per_role);
      for (const int64_t receiver : listeners) {
        if (uplink_uniform[sender * kMaxAgents + receiver] < probability) {
          state.scheduled.push_back(
              Scheduled{SCHEDULE_UPLINK, due, sender, receiver, packet.basin, packet.ordinal, packet.birth});
          if (due < packet.birth + 4) {
            decoded_nonexpired.insert(receiver);
          }
        }
      }
    }
    if (decoded_nonexpired.empty()) {
      state.metrics[METRIC_WASTE] += 1;
    }
    for (const int64_t receiver : listeners) {
      if (decoded_nonexpired.count(receiver) == 0) {
        state.metrics[METRIC_WASTE] += 1;
      }
    }
  }

  std::vector<int64_t> forward_agents;
  std::vector<int64_t> nonempty_forward;
  for (int64_t agent = 0; agent < state.n; ++agent) {
    if (actions[agent] == ACTION_FORWARD_BASE) {
      forward_agents.push_back(agent);
      if (fifo_head(state, agent).valid()) {
        nonempty_forward.push_back(agent);
      }
    }
  }
  for (const int64_t agent : forward_agents) {
    if (!fifo_head(state, agent).valid()) {
      state.metrics[METRIC_EMPTY] += 1;
      state.metrics[METRIC_WASTE] += 1;
    }
  }
  if (nonempty_forward.size() >= 2) {
    state.metrics[METRIC_COLLISION] += static_cast<int64_t>(nonempty_forward.size());
    state.metrics[METRIC_WASTE] += static_cast<int64_t>(nonempty_forward.size());
  } else if (nonempty_forward.size() == 1) {
    const int64_t sender = nonempty_forward[0];
    const Packet packet = fifo_head(state, sender);
    const int64_t due = slot + 1;
    const bool decoded =
        slot < kHorizon - 1 && base_uniform[sender] < link_probability(0.90f, per_role);
    const bool new_timely = decoded && due < packet.birth + 4 &&
                            state.delivered[packet.basin * 3 + packet.ordinal] == 0;
    if (decoded) {
      state.scheduled.push_back(
          Scheduled{SCHEDULE_BASE, due, sender, -1, packet.basin, packet.ordinal, packet.birth});
    }
    if (!new_timely) {
      state.metrics[METRIC_WASTE] += 1;
    }
  }
  if (state.scheduled.size() > static_cast<size_t>(kMaxScheduled)) {
    throw std::runtime_error("scheduled-arrival capacity exceeded");
  }
}

void scan(
    LaneState& state,
    int64_t slot,
    const std::array<int64_t, kMaxAgents>& actions,
    const float* detection_uniform) {
  for (int64_t agent = 0; agent < state.n; ++agent) {
    const int64_t role = state.roles[agent];
    if ((role != ROLE_WEST && role != ROLE_EAST) || actions[agent] != ACTION_SCAN) {
      continue;
    }
    for (int64_t ordinal = 0; ordinal < 3; ++ordinal) {
      if (state.events[role * 3 + ordinal] == slot && detection_uniform[agent] < 0.75f) {
        fifo_append(state, agent, 2, Packet{role, ordinal, slot});
      }
    }
  }
}

float terminal(const LaneState& state) {
  int64_t west = 0;
  int64_t east = 0;
  for (int64_t ordinal = 0; ordinal < 3; ++ordinal) {
    west += state.delivered[ordinal];
    east += state.delivered[3 + ordinal];
  }
  const int64_t radio = state.metrics[METRIC_RADIO];
  const float waste = radio == 0 ? 0.0f : static_cast<float>(state.metrics[METRIC_WASTE]) / radio;
  return 0.65f * static_cast<float>(west + east) / 6.0f +
         0.25f * static_cast<float>(std::min(west, east)) / 3.0f +
         0.10f * (1.0f - waste);
}

struct BatchInputs {
  py::ssize_t width;
  py::array_t<int64_t> n_agents;
  py::array_t<int64_t> origin_slot;
  py::array_t<int64_t> focal_agent;
  py::array_t<int64_t> roles;
  py::array_t<int64_t> fifo_basin;
  py::array_t<int64_t> fifo_ordinal;
  py::array_t<int64_t> fifo_birth;
  py::array_t<int64_t> scheduled_count;
  py::array_t<int64_t> scheduled_kind;
  py::array_t<int64_t> scheduled_due;
  py::array_t<int64_t> scheduled_sender;
  py::array_t<int64_t> scheduled_receiver;
  py::array_t<int64_t> scheduled_basin;
  py::array_t<int64_t> scheduled_ordinal;
  py::array_t<int64_t> scheduled_birth;
  py::array_t<int64_t> delivered;
  py::array_t<int64_t> metrics;
  py::array_t<int64_t> previous_action;
  py::array_t<int64_t> previous_success;
  py::array_t<int64_t> event_schedule;
  py::array_t<float> post_gru_hidden;
  py::array_t<float> current_observations;
  py::array_t<float> current_messages;
  py::array_t<float> current_legal_probabilities;
  py::array_t<int64_t> factual_joint_action;
  py::array_t<int64_t> focal_intervention;
  py::array_t<float> factual_terminal;
  py::array_t<float> detection_uniform;
  py::array_t<float> uplink_uniform;
  py::array_t<float> base_uniform;
  py::array_t<float> action_uniform;

  explicit BatchInputs(const py::dict& batch)
      : width(py::reinterpret_borrow<py::array>(batch["n_agents"]).shape(0)),
        n_agents(require_array<int64_t>(batch, "n_agents", {width})),
        origin_slot(require_array<int64_t>(batch, "origin_slot", {width})),
        focal_agent(require_array<int64_t>(batch, "focal_agent", {width})),
        roles(require_array<int64_t>(batch, "roles", {width, kMaxAgents})),
        fifo_basin(require_array<int64_t>(batch, "fifo_basin", {width, kMaxAgents, kFifo})),
        fifo_ordinal(require_array<int64_t>(batch, "fifo_ordinal", {width, kMaxAgents, kFifo})),
        fifo_birth(require_array<int64_t>(batch, "fifo_birth", {width, kMaxAgents, kFifo})),
        scheduled_count(require_array<int64_t>(batch, "scheduled_count", {width})),
        scheduled_kind(require_array<int64_t>(batch, "scheduled_kind", {width, kMaxScheduled})),
        scheduled_due(require_array<int64_t>(batch, "scheduled_due", {width, kMaxScheduled})),
        scheduled_sender(require_array<int64_t>(batch, "scheduled_sender", {width, kMaxScheduled})),
        scheduled_receiver(require_array<int64_t>(batch, "scheduled_receiver", {width, kMaxScheduled})),
        scheduled_basin(require_array<int64_t>(batch, "scheduled_basin", {width, kMaxScheduled})),
        scheduled_ordinal(require_array<int64_t>(batch, "scheduled_ordinal", {width, kMaxScheduled})),
        scheduled_birth(require_array<int64_t>(batch, "scheduled_birth", {width, kMaxScheduled})),
        delivered(require_array<int64_t>(batch, "delivered", {width, 2, 3})),
        metrics(require_array<int64_t>(batch, "metrics", {width, kMetricDim})),
        previous_action(require_array<int64_t>(batch, "previous_action", {width, kMaxAgents})),
        previous_success(require_array<int64_t>(batch, "previous_success", {width, kMaxAgents})),
        event_schedule(require_array<int64_t>(batch, "event_schedule", {width, 2, 3})),
        post_gru_hidden(require_array<float>(batch, "post_gru_hidden", {width, kMaxAgents, kHidden})),
        current_observations(require_array<float>(batch, "current_observations", {width, kMaxAgents, kObs})),
        current_messages(require_array<float>(batch, "current_messages", {width, kMaxAgents, kMessage})),
        current_legal_probabilities(require_array<float>(batch, "current_legal_probabilities", {width, kMaxAgents, kActions})),
        factual_joint_action(require_array<int64_t>(batch, "factual_joint_action", {width, kMaxAgents})),
        focal_intervention(require_array<int64_t>(batch, "focal_intervention", {width})),
        factual_terminal(require_array<float>(batch, "factual_terminal", {width})),
        detection_uniform(require_array<float>(batch, "detection_uniform", {width, kHorizon, kMaxAgents})),
        uplink_uniform(require_array<float>(batch, "uplink_uniform", {width, kHorizon, kMaxAgents, kMaxAgents})),
        base_uniform(require_array<float>(batch, "base_uniform", {width, kHorizon, kMaxAgents})),
        action_uniform(require_array<float>(batch, "action_uniform", {width, kHorizon, kMaxAgents})) {
    if (!(width == 32 || width == 64 || width == 128 || width == 256)) {
      throw std::invalid_argument("unsupported width");
    }
    require_finite(post_gru_hidden);
    require_finite(current_observations);
    require_finite(current_messages);
    require_finite(current_legal_probabilities);
    require_finite(factual_terminal);
    require_finite(detection_uniform);
    require_finite(uplink_uniform);
    require_finite(base_uniform);
    require_finite(action_uniform);
  }
};

struct ParameterInputs {
  py::array_t<float> encoder_w1;
  py::array_t<float> encoder_b1;
  py::array_t<float> encoder_w2;
  py::array_t<float> encoder_b2;
  py::array_t<float> beta;
  py::array_t<float> gru_w;
  py::array_t<float> gru_u;
  py::array_t<float> gru_b;
  py::array_t<float> actor_w;
  py::array_t<float> actor_b;

  explicit ParameterInputs(const py::dict& values)
      : encoder_w1(require_array<float>(values, "encoder_w1", {64, 22})),
        encoder_b1(require_array<float>(values, "encoder_b1", {64})),
        encoder_w2(require_array<float>(values, "encoder_w2", {32, 64})),
        encoder_b2(require_array<float>(values, "encoder_b2", {32})),
        beta(require_array<float>(values, "beta", {3, 3, 2})),
        gru_w(require_array<float>(values, "gru_w", {3, 64, 55})),
        gru_u(require_array<float>(values, "gru_u", {3, 64, 64})),
        gru_b(require_array<float>(values, "gru_b", {3, 64})),
        actor_w(require_array<float>(values, "actor_w", {6, 64})),
        actor_b(require_array<float>(values, "actor_b", {6})) {
    require_finite(encoder_w1);
    require_finite(encoder_b1);
    require_finite(encoder_w2);
    require_finite(encoder_b2);
    require_finite(beta);
    require_finite(gru_w);
    require_finite(gru_u);
    require_finite(gru_b);
    require_finite(actor_w);
    require_finite(actor_b);
  }

  Parameters pointers() const {
    return Parameters{encoder_w1.data(), encoder_b1.data(), encoder_w2.data(), encoder_b2.data(),
                      beta.data(), gru_w.data(), gru_u.data(), gru_b.data(), actor_w.data(), actor_b.data()};
  }
};

struct EpisodeInputs {
  py::ssize_t width;
  py::array_t<int64_t> n_agents;
  py::array_t<int64_t> roles;
  py::array_t<int64_t> event_schedule;
  py::array_t<int64_t> selector_slot;
  py::array_t<int64_t> selector_local_index;
  py::array_t<float> detection_uniform;
  py::array_t<float> uplink_uniform;
  py::array_t<float> base_uniform;
  py::array_t<float> action_uniform;

  explicit EpisodeInputs(const py::dict& batch)
      : width(py::reinterpret_borrow<py::array>(batch["n_agents"]).shape(0)),
        n_agents(require_array<int64_t>(batch, "n_agents", {width})),
        roles(require_array<int64_t>(batch, "roles", {width, kMaxAgents})),
        event_schedule(require_array<int64_t>(batch, "event_schedule", {width, 2, 3})),
        selector_slot(require_array<int64_t>(batch, "selector_slot", {width, 3})),
        selector_local_index(require_array<int64_t>(batch, "selector_local_index", {width, 3})),
        detection_uniform(require_array<float>(batch, "detection_uniform", {width, kHorizon, kMaxAgents})),
        uplink_uniform(require_array<float>(batch, "uplink_uniform", {width, kHorizon, kMaxAgents, kMaxAgents})),
        base_uniform(require_array<float>(batch, "base_uniform", {width, kHorizon, kMaxAgents})),
        action_uniform(require_array<float>(batch, "action_uniform", {width, kHorizon, kMaxAgents})) {
    if (!(width == 32 || width == 64 || width == 128 || width == 256)) {
      throw std::invalid_argument("unsupported episode width");
    }
    require_finite(detection_uniform);
    require_finite(uplink_uniform);
    require_finite(base_uniform);
    require_finite(action_uniform);
  }
};

uint64_t common_tape_digest(const BatchInputs& input, py::ssize_t lane, int64_t n, int64_t origin) {
  uint64_t digest = fnv_i64(kFnvOffset, n);
  digest = fnv_i64(digest, origin);
  const float* detection = input.detection_uniform.data();
  const float* base = input.base_uniform.data();
  const float* action = input.action_uniform.data();
  const float* uplink = input.uplink_uniform.data();
  for (int64_t slot = origin; slot < kHorizon; ++slot) {
    for (int64_t agent = 0; agent < n; ++agent) {
      const size_t index3 = static_cast<size_t>((lane * kHorizon + slot) * kMaxAgents + agent);
      digest = fnv_f32(digest, detection[index3]);
      digest = fnv_f32(digest, base[index3]);
      digest = fnv_f32(digest, action[index3]);
      for (int64_t receiver = 0; receiver < n; ++receiver) {
        const size_t index4 = static_cast<size_t>(((lane * kHorizon + slot) * kMaxAgents + agent) * kMaxAgents + receiver);
        digest = fnv_f32(digest, uplink[index4]);
      }
    }
  }
  return digest;
}

uint64_t episode_common_tape_digest(const EpisodeInputs& input, py::ssize_t lane, int64_t n) {
  uint64_t digest = fnv_i64(kFnvOffset, n);
  digest = fnv_i64(digest, 0);
  for (int64_t slot = 0; slot < kHorizon; ++slot) {
    for (int64_t agent = 0; agent < n; ++agent) {
      const size_t index3 = static_cast<size_t>((lane * kHorizon + slot) * kMaxAgents + agent);
      digest = fnv_f32(digest, input.detection_uniform.data()[index3]);
      digest = fnv_f32(digest, input.base_uniform.data()[index3]);
      digest = fnv_f32(digest, input.action_uniform.data()[index3]);
      for (int64_t receiver = 0; receiver < n; ++receiver) {
        const size_t index4 = static_cast<size_t>(
            ((lane * kHorizon + slot) * kMaxAgents + agent) * kMaxAgents + receiver);
        digest = fnv_f32(digest, input.uplink_uniform.data()[index4]);
      }
    }
  }
  return digest;
}

uint64_t trace_snapshot_digest(
    int64_t slot,
    const LaneState& state,
    const std::vector<float>& observations,
    const float* messages,
    const float* summaries,
    const float* denominators,
    const float* incoming_hidden,
    const float* post_hidden,
    const float* probabilities,
    const std::array<int64_t, kMaxAgents>& actions) {
  uint64_t digest = fnv_i64(kFnvOffset, slot);
  for (int64_t agent = 0; agent < state.n; ++agent) {
    digest = fnv_i64(digest, state.roles[agent]);
  }
  for (int64_t agent = 0; agent < state.n; ++agent) {
    for (int64_t position = 0; position < kFifo; ++position) {
      digest = fnv_i64(digest, state.packet(agent, position).basin);
    }
  }
  for (int64_t agent = 0; agent < state.n; ++agent) {
    for (int64_t position = 0; position < kFifo; ++position) {
      digest = fnv_i64(digest, state.packet(agent, position).ordinal);
    }
  }
  for (int64_t agent = 0; agent < state.n; ++agent) {
    for (int64_t position = 0; position < kFifo; ++position) {
      digest = fnv_i64(digest, state.packet(agent, position).birth);
    }
  }
  for (const int64_t value : state.delivered) {
    digest = fnv_i64(digest, value);
  }
  for (const int64_t value : state.metrics) {
    digest = fnv_i64(digest, value);
  }
  for (int64_t agent = 0; agent < state.n; ++agent) {
    digest = fnv_i64(digest, state.previous_action[agent]);
  }
  for (int64_t agent = 0; agent < state.n; ++agent) {
    digest = fnv_i64(digest, state.previous_success[agent]);
  }
  for (const int64_t value : state.events) {
    digest = fnv_i64(digest, value);
  }
  for (int64_t agent = 0; agent < state.n; ++agent) {
    digest = fnv_i64(digest, actions[agent]);
  }
  const float* float_arrays[] = {
      observations.data(), messages, summaries, denominators,
      incoming_hidden, post_hidden, probabilities};
  const int64_t widths[] = {kObs, kMessage, kMessage, 1, kHidden, kHidden, kActions};
  for (int64_t array = 0; array < 7; ++array) {
    for (int64_t index = 0; index < state.n * widths[array]; ++index) {
      digest = fnv_canonical_f32(digest, float_arrays[array][index]);
    }
  }
  return digest;
}

uint64_t audit_prefix(
    const BatchInputs& input,
    py::ssize_t lane,
    int64_t n,
    int64_t origin,
    int64_t focal,
    uint64_t common_digest) {
  uint64_t digest = fnv_u64(kFnvOffset, common_digest);
  digest = fnv_i64(digest, origin);
  digest = fnv_i64(digest, focal);
  for (int64_t agent = 0; agent < n; ++agent) {
    const size_t agent_index = static_cast<size_t>(lane * kMaxAgents + agent);
    digest = fnv_i64(digest, input.roles.data()[agent_index]);
    for (int64_t position = 0; position < kFifo; ++position) {
      const size_t packet_index = agent_index * kFifo + position;
      digest = fnv_i64(digest, input.fifo_basin.data()[packet_index]);
      digest = fnv_i64(digest, input.fifo_ordinal.data()[packet_index]);
      digest = fnv_i64(digest, input.fifo_birth.data()[packet_index]);
    }
  }
  digest = fnv_i64(digest, input.scheduled_count.data()[lane]);
  for (int64_t index = 0; index < 6; ++index) {
    digest = fnv_i64(digest, input.delivered.data()[lane * 6 + index]);
  }
  for (int64_t index = 0; index < kMetricDim; ++index) {
    digest = fnv_i64(digest, input.metrics.data()[lane * kMetricDim + index]);
  }
  for (int64_t agent = 0; agent < n; ++agent) {
    const size_t agent_index = static_cast<size_t>(lane * kMaxAgents + agent);
    digest = fnv_i64(digest, input.previous_action.data()[agent_index]);
    digest = fnv_i64(digest, input.previous_success.data()[agent_index]);
  }
  for (int64_t index = 0; index < 6; ++index) {
    digest = fnv_i64(digest, input.event_schedule.data()[lane * 6 + index]);
  }
  const float* float_arrays[] = {
      input.post_gru_hidden.data() + lane * kMaxAgents * kHidden,
      input.current_observations.data() + lane * kMaxAgents * kObs,
      input.current_messages.data() + lane * kMaxAgents * kMessage,
      input.current_legal_probabilities.data() + lane * kMaxAgents * kActions};
  const int64_t float_widths[] = {kHidden, kObs, kMessage, kActions};
  for (int64_t array = 0; array < 4; ++array) {
    for (int64_t index = 0; index < n * float_widths[array]; ++index) {
      digest = fnv_f32(digest, float_arrays[array][index]);
    }
  }
  for (int64_t agent = 0; agent < n; ++agent) {
    digest = fnv_i64(digest, input.factual_joint_action.data()[lane * kMaxAgents + agent]);
  }
  digest = fnv_i64(digest, input.focal_intervention.data()[lane]);
  return digest;
}

py::dict run_factual_trajectory(
    const py::dict& episode_dict,
    const py::dict& parameter_dict,
    const std::string& mode_name) {
  EpisodeInputs input(episode_dict);
  ParameterInputs parameter_input(parameter_dict);
  const Parameters parameters = parameter_input.pointers();
  const int64_t mode = mode_name == "INTACT" ? 0 : mode_name == "FULL_ROTATED" ? 1 : -1;
  if (mode < 0) {
    throw std::invalid_argument("unsupported factual trajectory mode");
  }
  const py::ssize_t width = input.width;
  auto f32 = [](const std::vector<py::ssize_t>& shape) { return py::array_t<float>(shape); };
  auto i64 = [](const std::vector<py::ssize_t>& shape) { return py::array_t<int64_t>(shape); };
  auto u64 = [](const std::vector<py::ssize_t>& shape) { return py::array_t<uint64_t>(shape); };
  py::array_t<float> observations = f32({width, kHorizon, kMaxAgents, kObs});
  py::array_t<float> messages = f32({width, kHorizon, kMaxAgents, kMessage});
  py::array_t<float> summaries = f32({width, kHorizon, kMaxAgents, kMessage});
  py::array_t<float> denominators = f32({width, kHorizon, kMaxAgents});
  py::array_t<float> incoming_hidden = f32({width, kHorizon, kMaxAgents, kHidden});
  py::array_t<float> post_hidden = f32({width, kHorizon, kMaxAgents, kHidden});
  py::array_t<float> probabilities = f32({width, kHorizon, kMaxAgents, kActions});
  py::array_t<int64_t> actions_trace = i64({width, kHorizon, kMaxAgents});
  py::array_t<int64_t> fifo_basin_trace = i64({width, kHorizon, kMaxAgents, kFifo});
  py::array_t<int64_t> fifo_ordinal_trace = i64({width, kHorizon, kMaxAgents, kFifo});
  py::array_t<int64_t> fifo_birth_trace = i64({width, kHorizon, kMaxAgents, kFifo});
  py::array_t<int64_t> scheduled_count = i64({width, kHorizon});
  py::array_t<int64_t> delivered_trace = i64({width, kHorizon, 2, 3});
  py::array_t<int64_t> metrics_trace = i64({width, kHorizon, kMetricDim});
  py::array_t<int64_t> previous_action_trace = i64({width, kHorizon, kMaxAgents});
  py::array_t<int64_t> previous_success_trace = i64({width, kHorizon, kMaxAgents});
  py::array_t<uint64_t> snapshot_digest = u64({width, kHorizon});
  py::array_t<int64_t> origin_slot = i64({width, 3});
  py::array_t<int64_t> origin_agent = i64({width, 3});
  py::array_t<uint64_t> origin_snapshot_digest = u64({width, 3});
  py::array_t<float> terminal_return = f32({width});
  py::array_t<int64_t> final_delivered = i64({width, 2});
  py::array_t<int64_t> final_metrics = i64({width, kMetricDim});
  py::array_t<uint64_t> common_digest = u64({width});
  py::array_t<uint64_t> trajectory_digest = u64({width});
  py::array_t<bool> active(width);

  std::fill_n(observations.mutable_data(), observations.size(), 0.0f);
  std::fill_n(messages.mutable_data(), messages.size(), 0.0f);
  std::fill_n(summaries.mutable_data(), summaries.size(), 0.0f);
  std::fill_n(denominators.mutable_data(), denominators.size(), 0.0f);
  std::fill_n(incoming_hidden.mutable_data(), incoming_hidden.size(), 0.0f);
  std::fill_n(post_hidden.mutable_data(), post_hidden.size(), 0.0f);
  std::fill_n(probabilities.mutable_data(), probabilities.size(), 0.0f);
  std::fill_n(actions_trace.mutable_data(), actions_trace.size(), int64_t{-1});
  std::fill_n(fifo_basin_trace.mutable_data(), fifo_basin_trace.size(), int64_t{-1});
  std::fill_n(fifo_ordinal_trace.mutable_data(), fifo_ordinal_trace.size(), int64_t{-1});
  std::fill_n(fifo_birth_trace.mutable_data(), fifo_birth_trace.size(), int64_t{-1});
  std::fill_n(scheduled_count.mutable_data(), scheduled_count.size(), int64_t{0});
  std::fill_n(delivered_trace.mutable_data(), delivered_trace.size(), int64_t{0});
  std::fill_n(metrics_trace.mutable_data(), metrics_trace.size(), int64_t{0});
  std::fill_n(previous_action_trace.mutable_data(), previous_action_trace.size(), int64_t{-1});
  std::fill_n(previous_success_trace.mutable_data(), previous_success_trace.size(), int64_t{0});
  std::fill_n(snapshot_digest.mutable_data(), snapshot_digest.size(), uint64_t{0});
  std::fill_n(origin_slot.mutable_data(), origin_slot.size(), int64_t{0});
  std::fill_n(origin_agent.mutable_data(), origin_agent.size(), int64_t{0});
  std::fill_n(origin_snapshot_digest.mutable_data(), origin_snapshot_digest.size(), uint64_t{0});
  std::fill_n(terminal_return.mutable_data(), terminal_return.size(), 0.0f);
  std::fill_n(final_delivered.mutable_data(), final_delivered.size(), int64_t{0});
  std::fill_n(final_metrics.mutable_data(), final_metrics.size(), int64_t{0});
  std::fill_n(common_digest.mutable_data(), common_digest.size(), uint64_t{0});
  std::fill_n(trajectory_digest.mutable_data(), trajectory_digest.size(), uint64_t{0});
  std::fill_n(active.mutable_data(), active.size(), false);

  {
    py::gil_scoped_release release;
    for (py::ssize_t lane = 0; lane < width; ++lane) {
      const int64_t n = input.n_agents.data()[lane];
      if (n == 0) {
        continue;
      }
      if (!(n == 6 || n == 9 || n == 15 || n == 21)) {
        throw std::invalid_argument("unsupported factual roster");
      }
      LaneState state;
      state.n = n;
      state.previous_action.fill(-1);
      std::array<int64_t, 3> role_counts{};
      for (int64_t agent = 0; agent < n; ++agent) {
        state.roles[agent] = input.roles.data()[lane * kMaxAgents + agent];
        if (state.roles[agent] < 0 || state.roles[agent] >= 3) {
          throw std::invalid_argument("invalid factual role");
        }
        role_counts[state.roles[agent]] += 1;
      }
      if (role_counts[0] != n / 3 || role_counts[1] != n / 3 || role_counts[2] != n / 3) {
        throw std::invalid_argument("factual roles are not balanced");
      }
      std::memcpy(
          state.events.data(), input.event_schedule.data() + lane * 6, sizeof(int64_t) * 6);
      for (int64_t basin = 0; basin < 2; ++basin) {
        std::set<int64_t> distinct;
        for (int64_t ordinal = 0; ordinal < 3; ++ordinal) {
          const int64_t event = state.events[basin * 3 + ordinal];
          if (event < 0 || event > 7 || !distinct.insert(event).second) {
            throw std::invalid_argument("invalid factual event schedule");
          }
        }
      }
      const int64_t per_role = n / 3;
      for (int64_t role = 0; role < 3; ++role) {
        const int64_t selector_slot_value = input.selector_slot.data()[lane * 3 + role];
        const int64_t local = input.selector_local_index.data()[lane * 3 + role];
        if (selector_slot_value < 0 || selector_slot_value >= kHorizon ||
            local < 0 || local >= per_role) {
          throw std::invalid_argument("invalid TEST selector origin");
        }
        origin_slot.mutable_data()[lane * 3 + role] = selector_slot_value;
        origin_agent.mutable_data()[lane * 3 + role] = role * per_role + local;
      }
      for (int64_t slot = 0; slot < kHorizon; ++slot) {
        for (int64_t agent = 0; agent < n; ++agent) {
          const size_t index3 = static_cast<size_t>((lane * kHorizon + slot) * kMaxAgents + agent);
          const float values[] = {
              input.detection_uniform.data()[index3],
              input.base_uniform.data()[index3],
              input.action_uniform.data()[index3]};
          for (const float value : values) {
            if (value < 0.0f || value >= 1.0f) {
              throw std::invalid_argument("factual tape outside [0,1)");
            }
          }
          for (int64_t receiver = 0; receiver < n; ++receiver) {
            const size_t index4 = static_cast<size_t>(
                ((lane * kHorizon + slot) * kMaxAgents + agent) * kMaxAgents + receiver);
            const float value = input.uplink_uniform.data()[index4];
            if (value < 0.0f || value >= 1.0f) {
              throw std::invalid_argument("factual uplink tape outside [0,1)");
            }
          }
        }
      }
      active.mutable_data()[lane] = true;
      std::vector<float> slot_observations;
      std::array<int64_t, kMaxAgents> actions{};
      for (int64_t slot = 0; slot < kHorizon; ++slot) {
        if (slot > 0) {
          process_arrivals(state, slot);
          purge_expired(state, slot);
        }
        if (!state.scheduled.empty()) {
          throw std::runtime_error("latency-one factual trace retained a pending predecision arrival");
        }
        form_observations(state, slot, slot_observations);
        const size_t slot_agent = static_cast<size_t>((lane * kHorizon + slot) * kMaxAgents);
        const size_t obs_offset = slot_agent * kObs;
        const size_t message_offset = slot_agent * kMessage;
        const size_t hidden_offset = slot_agent * kHidden;
        const size_t probability_offset = slot_agent * kActions;
        for (int64_t agent = 0; agent < n; ++agent) {
          std::memcpy(
              observations.mutable_data() + obs_offset + agent * kObs,
              slot_observations.data() + agent * kObs,
              sizeof(float) * kObs);
          std::memcpy(
              incoming_hidden.mutable_data() + hidden_offset + agent * kHidden,
              state.hidden.data() + agent * kHidden,
              sizeof(float) * kHidden);
          previous_action_trace.mutable_data()[slot_agent + agent] = state.previous_action[agent];
          previous_success_trace.mutable_data()[slot_agent + agent] = state.previous_success[agent];
          for (int64_t position = 0; position < kFifo; ++position) {
            const size_t trace_packet = (slot_agent + agent) * kFifo + position;
            const Packet packet = state.packet(agent, position);
            fifo_basin_trace.mutable_data()[trace_packet] = packet.basin;
            fifo_ordinal_trace.mutable_data()[trace_packet] = packet.ordinal;
            fifo_birth_trace.mutable_data()[trace_packet] = packet.birth;
          }
        }
        std::memcpy(
            delivered_trace.mutable_data() + (lane * kHorizon + slot) * 6,
            state.delivered.data(), sizeof(int64_t) * 6);
        std::memcpy(
            metrics_trace.mutable_data() + (lane * kHorizon + slot) * kMetricDim,
            state.metrics.data(), sizeof(int64_t) * kMetricDim);
        const float* uniforms = input.action_uniform.data() + slot_agent;
        policy_step(
            state,
            parameters,
            slot_observations,
            uniforms,
            actions,
            mode,
            messages.mutable_data() + message_offset,
            summaries.mutable_data() + message_offset,
            denominators.mutable_data() + slot_agent,
            probabilities.mutable_data() + probability_offset);
        for (int64_t agent = 0; agent < n; ++agent) {
          std::memcpy(
              post_hidden.mutable_data() + hidden_offset + agent * kHidden,
              state.hidden.data() + agent * kHidden,
              sizeof(float) * kHidden);
          actions_trace.mutable_data()[slot_agent + agent] = actions[agent];
        }
        const uint64_t slot_digest = trace_snapshot_digest(
            slot,
            state,
            slot_observations,
            messages.data() + message_offset,
            summaries.data() + message_offset,
            denominators.data() + slot_agent,
            incoming_hidden.data() + hidden_offset,
            post_hidden.data() + hidden_offset,
            probabilities.data() + probability_offset,
            actions);
        snapshot_digest.mutable_data()[lane * kHorizon + slot] = slot_digest;
        for (int64_t agent = 0; agent < n; ++agent) {
          state.previous_action[agent] = actions[agent];
          state.previous_success[agent] = 0;
        }
        const float* uplink = input.uplink_uniform.data() + slot_agent * kMaxAgents;
        const float* base = input.base_uniform.data() + slot_agent;
        const float* detection = input.detection_uniform.data() + slot_agent;
        schedule_radio(state, slot, actions, uplink, base);
        scan(state, slot, actions, detection);
      }
      const float target = terminal(state);
      terminal_return.mutable_data()[lane] = target;
      for (int64_t basin = 0; basin < 2; ++basin) {
        int64_t count = 0;
        for (int64_t ordinal = 0; ordinal < 3; ++ordinal) {
          count += state.delivered[basin * 3 + ordinal];
        }
        final_delivered.mutable_data()[lane * 2 + basin] = count;
      }
      std::memcpy(
          final_metrics.mutable_data() + lane * kMetricDim,
          state.metrics.data(), sizeof(int64_t) * kMetricDim);
      const uint64_t tape = episode_common_tape_digest(input, lane, n);
      common_digest.mutable_data()[lane] = tape;
      uint64_t digest = fnv_u64(kFnvOffset, tape);
      digest = fnv_i64(digest, mode);
      for (int64_t slot = 0; slot < kHorizon; ++slot) {
        digest = fnv_u64(digest, snapshot_digest.data()[lane * kHorizon + slot]);
      }
      digest = fnv_f32(digest, target);
      trajectory_digest.mutable_data()[lane] = digest;
      for (int64_t role = 0; role < 3; ++role) {
        const int64_t selected_slot = origin_slot.data()[lane * 3 + role];
        origin_snapshot_digest.mutable_data()[lane * 3 + role] =
            snapshot_digest.data()[lane * kHorizon + selected_slot];
      }
    }
  }

  py::dict result;
  result["observations"] = observations;
  result["messages"] = messages;
  result["role_summaries"] = summaries;
  result["denominators"] = denominators;
  result["incoming_hidden"] = incoming_hidden;
  result["post_gru_hidden"] = post_hidden;
  result["legal_probabilities"] = probabilities;
  result["factual_actions"] = actions_trace;
  result["fifo_basin"] = fifo_basin_trace;
  result["fifo_ordinal"] = fifo_ordinal_trace;
  result["fifo_birth"] = fifo_birth_trace;
  result["scheduled_count"] = scheduled_count;
  result["delivered"] = delivered_trace;
  result["metrics"] = metrics_trace;
  result["previous_action"] = previous_action_trace;
  result["previous_success"] = previous_success_trace;
  result["snapshot_digest"] = snapshot_digest;
  result["origin_slot"] = origin_slot;
  result["origin_agent"] = origin_agent;
  result["origin_snapshot_digest"] = origin_snapshot_digest;
  result["terminal_return"] = terminal_return;
  result["final_delivered"] = final_delivered;
  result["final_metrics"] = final_metrics;
  result["common_tape_digest"] = common_digest;
  result["trajectory_digest"] = trajectory_digest;
  result["active"] = active;
  return result;
}

py::dict run_shadow_trajectory(
    const py::dict& episode_dict,
    const py::dict& trace_dict,
    const py::dict& parameter_dict) {
  EpisodeInputs input(episode_dict);
  ParameterInputs parameter_input(parameter_dict);
  const Parameters parameters = parameter_input.pointers();
  const py::ssize_t width = input.width;
  const auto observations = require_array<float>(
      trace_dict, "observations", {width, kHorizon, kMaxAgents, kObs});
  const auto messages = require_array<float>(
      trace_dict, "messages", {width, kHorizon, kMaxAgents, kMessage});
  const auto incoming = require_array<float>(
      trace_dict, "incoming_hidden", {width, kHorizon, kMaxAgents, kHidden});
  const auto intact_digest = require_array<uint64_t>(
      trace_dict, "snapshot_digest", {width, kHorizon});
  const auto intact_active = require_array<bool>(trace_dict, "active", {width});
  require_finite(observations);
  require_finite(messages);
  require_finite(incoming);

  py::array_t<float> summaries(
      std::vector<py::ssize_t>{width, kHorizon, kMaxAgents, kMessage});
  py::array_t<float> denominators(
      std::vector<py::ssize_t>{width, kHorizon, kMaxAgents});
  py::array_t<float> post_hidden(
      std::vector<py::ssize_t>{width, kHorizon, kMaxAgents, kHidden});
  py::array_t<float> probabilities(
      std::vector<py::ssize_t>{width, kHorizon, kMaxAgents, kActions});
  py::array_t<uint64_t> snapshot_digest(
      std::vector<py::ssize_t>{width, kHorizon});
  py::array_t<bool> active(width);
  std::fill_n(summaries.mutable_data(), summaries.size(), 0.0f);
  std::fill_n(denominators.mutable_data(), denominators.size(), 0.0f);
  std::fill_n(post_hidden.mutable_data(), post_hidden.size(), 0.0f);
  std::fill_n(probabilities.mutable_data(), probabilities.size(), 0.0f);
  std::fill_n(snapshot_digest.mutable_data(), snapshot_digest.size(), uint64_t{0});
  std::fill_n(active.mutable_data(), active.size(), false);

  {
    py::gil_scoped_release release;
    for (py::ssize_t lane = 0; lane < width; ++lane) {
      const int64_t n = input.n_agents.data()[lane];
      if (n == 0) {
        continue;
      }
      if (!intact_active.data()[lane]) {
        throw std::invalid_argument("shadow input omits an active intact lane");
      }
      LaneState state;
      state.n = n;
      for (int64_t agent = 0; agent < n; ++agent) {
        state.roles[agent] = input.roles.data()[lane * kMaxAgents + agent];
      }
      std::array<int64_t, kMaxAgents> actions{};
      std::vector<float> slot_observations(static_cast<size_t>(n * kObs));
      for (int64_t slot = 0; slot < kHorizon; ++slot) {
        const size_t slot_agent = static_cast<size_t>((lane * kHorizon + slot) * kMaxAgents);
        const size_t obs_offset = slot_agent * kObs;
        const size_t message_offset = slot_agent * kMessage;
        const size_t hidden_offset = slot_agent * kHidden;
        const size_t probability_offset = slot_agent * kActions;
        std::memcpy(
            slot_observations.data(), observations.data() + obs_offset, sizeof(float) * n * kObs);
        std::memcpy(
            state.hidden.data(), incoming.data() + hidden_offset, sizeof(float) * n * kHidden);
        policy_step(
            state,
            parameters,
            slot_observations,
            input.action_uniform.data() + slot_agent,
            actions,
            1,
            nullptr,
            summaries.mutable_data() + message_offset,
            denominators.mutable_data() + slot_agent,
            probabilities.mutable_data() + probability_offset,
            messages.data() + message_offset);
        std::memcpy(
            post_hidden.mutable_data() + hidden_offset,
            state.hidden.data(), sizeof(float) * n * kHidden);
        uint64_t digest = fnv_u64(
            kFnvOffset, intact_digest.data()[lane * kHorizon + slot]);
        const float* arrays[] = {
            summaries.data() + message_offset,
            denominators.data() + slot_agent,
            post_hidden.data() + hidden_offset,
            probabilities.data() + probability_offset};
        const int64_t widths[] = {kMessage, 1, kHidden, kActions};
        for (int64_t array = 0; array < 4; ++array) {
          for (int64_t index = 0; index < n * widths[array]; ++index) {
            digest = fnv_canonical_f32(digest, arrays[array][index]);
          }
        }
        snapshot_digest.mutable_data()[lane * kHorizon + slot] = digest;
      }
      active.mutable_data()[lane] = true;
    }
  }
  py::dict result;
  result["role_summaries"] = summaries;
  result["denominators"] = denominators;
  result["post_gru_hidden"] = post_hidden;
  result["legal_probabilities"] = probabilities;
  result["snapshot_digest"] = snapshot_digest;
  result["active"] = active;
  return result;
}

py::dict run_suffix(const py::dict& batch_dict, const py::dict& parameter_dict) {
  BatchInputs input(batch_dict);
  ParameterInputs parameter_input(parameter_dict);
  const Parameters parameters = parameter_input.pointers();
  const py::ssize_t width = input.width;

  py::array_t<float> terminal_target(width);
  py::array_t<int64_t> final_delivered({width, static_cast<py::ssize_t>(2)});
  py::array_t<int64_t> final_metrics({width, static_cast<py::ssize_t>(kMetricDim)});
  py::array_t<int64_t> counters({width, static_cast<py::ssize_t>(4)});
  py::array_t<uint64_t> common_digest(width);
  py::array_t<uint64_t> audit_digest(width);
  py::array_t<bool> factual_candidate(width);
  py::array_t<bool> factual_identity(width);
  py::array_t<bool> active(width);

  std::fill_n(terminal_target.mutable_data(), terminal_target.size(), 0.0f);
  std::fill_n(final_delivered.mutable_data(), final_delivered.size(), int64_t{0});
  std::fill_n(final_metrics.mutable_data(), final_metrics.size(), int64_t{0});
  std::fill_n(counters.mutable_data(), counters.size(), int64_t{0});
  std::fill_n(common_digest.mutable_data(), common_digest.size(), uint64_t{0});
  std::fill_n(audit_digest.mutable_data(), audit_digest.size(), uint64_t{0});
  std::fill_n(factual_candidate.mutable_data(), factual_candidate.size(), false);
  std::fill_n(factual_identity.mutable_data(), factual_identity.size(), false);
  std::fill_n(active.mutable_data(), active.size(), false);

  {
    py::gil_scoped_release release;
    for (py::ssize_t lane = 0; lane < width; ++lane) {
      const int64_t n = input.n_agents.data()[lane];
      if (n == 0) {
        continue;
      }
      if (!(n == 6 || n == 9 || n == 15 || n == 21)) {
        throw std::invalid_argument("unsupported active roster");
      }
      const int64_t origin = input.origin_slot.data()[lane];
      const int64_t focal = input.focal_agent.data()[lane];
      if (origin < 0 || origin >= kHorizon || focal < 0 || focal >= n) {
        throw std::invalid_argument("invalid origin or focal agent");
      }
      active.mutable_data()[lane] = true;
      LaneState state;
      state.n = n;
      std::array<int64_t, 3> role_counts{};
      for (int64_t agent = 0; agent < n; ++agent) {
        const size_t agent_index = static_cast<size_t>(lane * kMaxAgents + agent);
        state.roles[agent] = input.roles.data()[agent_index];
        if (state.roles[agent] < 0 || state.roles[agent] >= 3) {
          throw std::invalid_argument("invalid active role");
        }
        role_counts[state.roles[agent]] += 1;
        const int64_t factual_action = input.factual_joint_action.data()[agent_index];
        if (!is_legal(state.roles[agent], factual_action)) {
          throw std::invalid_argument("illegal factual joint action");
        }
        state.previous_action[agent] = input.previous_action.data()[agent_index];
        state.previous_success[agent] = input.previous_success.data()[agent_index];
        if (state.previous_success[agent] != 0 && state.previous_success[agent] != 1) {
          throw std::invalid_argument("previous-success value is not binary");
        }
        if ((origin == 0 && state.previous_action[agent] != -1) ||
            (origin > 0 && !is_legal(state.roles[agent], state.previous_action[agent]))) {
          throw std::invalid_argument("invalid previous action");
        }
        const int64_t capacity = state.roles[agent] == ROLE_RELAY ? 4 : 2;
        bool seen_empty = false;
        for (int64_t position = 0; position < kFifo; ++position) {
          const size_t packet_index = agent_index * kFifo + position;
          state.packet(agent, position) = Packet{
              input.fifo_basin.data()[packet_index],
              input.fifo_ordinal.data()[packet_index],
              input.fifo_birth.data()[packet_index]};
          const Packet packet = state.packet(agent, position);
          if (!packet.valid()) {
            if (packet.basin != -1 || packet.ordinal != -1 || packet.birth != -1) {
              throw std::invalid_argument("partial FIFO sentinel");
            }
            seen_empty = true;
          } else {
            if (position >= capacity || seen_empty || packet.basin < 0 || packet.basin > 1 ||
                packet.ordinal < 0 || packet.ordinal >= 3 || packet.birth < 0 ||
                origin - packet.birth < 0 || origin - packet.birth > 3 ||
                (state.roles[agent] != ROLE_RELAY && packet.basin != state.roles[agent])) {
              throw std::invalid_argument("invalid pretransition FIFO packet");
            }
          }
        }
        std::memcpy(
            state.hidden.data() + agent * kHidden,
            input.post_gru_hidden.data() + agent_index * kHidden,
            sizeof(float) * kHidden);
        float probability_sum = 0.0f;
        int64_t legal_count = 0;
        const auto legal = legal_actions(state.roles[agent], &legal_count);
        for (int64_t action = 0; action < kActions; ++action) {
          const float probability = input.current_legal_probabilities.data()[agent_index * kActions + action];
          bool legal_action = false;
          for (int64_t index = 0; index < legal_count; ++index) {
            legal_action = legal_action || legal[index] == action;
          }
          if ((!legal_action && probability != 0.0f) ||
              (legal_action && probability < 0.04f / legal_count)) {
            throw std::invalid_argument("invalid current legal probability");
          }
          probability_sum += probability;
        }
        if (std::abs(probability_sum - 1.0f) > 1.0e-5f) {
          throw std::invalid_argument("current legal probabilities do not sum to one");
        }
      }
      if (role_counts[0] != n / 3 || role_counts[1] != n / 3 || role_counts[2] != n / 3) {
        throw std::invalid_argument("active roles are not balanced");
      }
      if (!is_legal(state.roles[focal], input.focal_intervention.data()[lane])) {
        throw std::invalid_argument("illegal focal intervention");
      }
      std::memcpy(
          state.delivered.data(),
          input.delivered.data() + lane * 6,
          sizeof(int64_t) * 6);
      std::memcpy(
          state.metrics.data(),
          input.metrics.data() + lane * kMetricDim,
          sizeof(int64_t) * kMetricDim);
      for (const int64_t value : state.delivered) {
        if (value != 0 && value != 1) {
          throw std::invalid_argument("delivered identity is not binary");
        }
      }
      for (const int64_t value : state.metrics) {
        if (value < 0) {
          throw std::invalid_argument("negative metric");
        }
      }
      if (state.metrics[METRIC_WASTE] > state.metrics[METRIC_RADIO]) {
        throw std::invalid_argument("waste count exceeds radio count");
      }
      int64_t delivered_count = 0;
      for (const int64_t value : state.delivered) {
        delivered_count += value;
      }
      if (state.metrics[METRIC_NEW_TIMELY] != delivered_count) {
        throw std::invalid_argument("new-timely metric disagrees with delivered identities");
      }
      std::memcpy(
          state.events.data(),
          input.event_schedule.data() + lane * 6,
          sizeof(int64_t) * 6);
      for (int64_t basin = 0; basin < 2; ++basin) {
        std::set<int64_t> distinct;
        for (int64_t ordinal = 0; ordinal < 3; ++ordinal) {
          const int64_t event = state.events[basin * 3 + ordinal];
          if (event < 0 || event > 7 || !distinct.insert(event).second) {
            throw std::invalid_argument("invalid event schedule");
          }
        }
      }
      for (int64_t agent = 0; agent < n; ++agent) {
        for (int64_t position = 0; position < kFifo; ++position) {
          const Packet packet = state.packet(agent, position);
          if (packet.valid() && state.events[packet.basin * 3 + packet.ordinal] != packet.birth) {
            throw std::invalid_argument("FIFO birth disagrees with event schedule");
          }
        }
      }
      const int64_t initial_scheduled = input.scheduled_count.data()[lane];
      if (initial_scheduled != 0) {
        throw std::invalid_argument("documented pretransition origin must have no pending arrivals");
      }
      for (int64_t index = 0; index < initial_scheduled; ++index) {
        const size_t schedule_index = static_cast<size_t>(lane * kMaxScheduled + index);
        state.scheduled.push_back(Scheduled{
            input.scheduled_kind.data()[schedule_index],
            input.scheduled_due.data()[schedule_index],
            input.scheduled_sender.data()[schedule_index],
            input.scheduled_receiver.data()[schedule_index],
            input.scheduled_basin.data()[schedule_index],
            input.scheduled_ordinal.data()[schedule_index],
            input.scheduled_birth.data()[schedule_index]});
      }

      for (int64_t slot = 0; slot < kHorizon; ++slot) {
        for (int64_t agent = 0; agent < n; ++agent) {
          const size_t index3 = static_cast<size_t>((lane * kHorizon + slot) * kMaxAgents + agent);
          const float values[] = {
              input.detection_uniform.data()[index3],
              input.base_uniform.data()[index3],
              input.action_uniform.data()[index3]};
          for (const float value : values) {
            if (value < 0.0f || value >= 1.0f) {
              throw std::invalid_argument("common tape value outside [0,1)");
            }
          }
          for (int64_t receiver = 0; receiver < n; ++receiver) {
            const size_t index4 = static_cast<size_t>(
                ((lane * kHorizon + slot) * kMaxAgents + agent) * kMaxAgents + receiver);
            const float value = input.uplink_uniform.data()[index4];
            if (value < 0.0f || value >= 1.0f) {
              throw std::invalid_argument("uplink tape value outside [0,1)");
            }
          }
        }
      }

      std::array<int64_t, kMaxAgents> actions{};
      for (int64_t agent = 0; agent < n; ++agent) {
        actions[agent] = input.factual_joint_action.data()[lane * kMaxAgents + agent];
      }
      actions[focal] = input.focal_intervention.data()[lane];
      int64_t transitions = 0;
      int64_t future_rounds = 0;
      int64_t future_decisions = 0;
      std::vector<float> observations;
      for (int64_t slot = origin; slot < kHorizon; ++slot) {
        if (slot > origin) {
          process_arrivals(state, slot);
          purge_expired(state, slot);
          form_observations(state, slot, observations);
          const float* uniforms = input.action_uniform.data() +
              (lane * kHorizon + slot) * kMaxAgents;
          policy_step(state, parameters, observations, uniforms, actions);
          future_rounds += 1;
          future_decisions += n;
        }
        for (int64_t agent = 0; agent < n; ++agent) {
          state.previous_action[agent] = actions[agent];
          state.previous_success[agent] = 0;
        }
        const float* uplink = input.uplink_uniform.data() +
            ((lane * kHorizon + slot) * kMaxAgents) * kMaxAgents;
        const float* base = input.base_uniform.data() +
            (lane * kHorizon + slot) * kMaxAgents;
        const float* detection = input.detection_uniform.data() +
            (lane * kHorizon + slot) * kMaxAgents;
        schedule_radio(state, slot, actions, uplink, base);
        scan(state, slot, actions, detection);
        transitions += 1;
      }

      const float target = terminal(state);
      terminal_target.mutable_data()[lane] = target;
      for (int64_t basin = 0; basin < 2; ++basin) {
        int64_t count = 0;
        for (int64_t ordinal = 0; ordinal < 3; ++ordinal) {
          count += state.delivered[basin * 3 + ordinal];
        }
        final_delivered.mutable_data()[lane * 2 + basin] = count;
      }
      for (int64_t metric = 0; metric < kMetricDim; ++metric) {
        final_metrics.mutable_data()[lane * kMetricDim + metric] = state.metrics[metric];
      }
      counters.mutable_data()[lane * 4] = transitions;
      counters.mutable_data()[lane * 4 + 1] = future_rounds;
      counters.mutable_data()[lane * 4 + 2] = future_decisions;
      counters.mutable_data()[lane * 4 + 3] = state.metrics[METRIC_DECODED];

      const uint64_t tape = common_tape_digest(input, lane, n, origin);
      common_digest.mutable_data()[lane] = tape;
      uint64_t audit = audit_prefix(input, lane, n, origin, focal, tape);
      audit = fnv_i64(audit, input.factual_joint_action.data()[lane * kMaxAgents + focal]);
      for (const int64_t value : state.delivered) {
        audit = fnv_i64(audit, value);
      }
      for (const int64_t value : state.metrics) {
        audit = fnv_i64(audit, value);
      }
      audit = fnv_f32(audit, target);
      audit_digest.mutable_data()[lane] = audit;

      const bool candidate = input.focal_intervention.data()[lane] ==
                             input.factual_joint_action.data()[lane * kMaxAgents + focal];
      factual_candidate.mutable_data()[lane] = candidate;
      const float expected = input.factual_terminal.data()[lane];
      factual_identity.mutable_data()[lane] =
          candidate && std::memcmp(&target, &expected, sizeof(float)) == 0;
    }
  }

  py::dict result;
  result["terminal_target"] = terminal_target;
  result["final_delivered"] = final_delivered;
  result["final_metrics"] = final_metrics;
  result["counters"] = counters;
  result["common_tape_digest"] = common_digest;
  result["audit_digest"] = audit_digest;
  result["factual_suffix_candidate"] = factual_candidate;
  result["factual_suffix_identity"] = factual_identity;
  result["active"] = active;
  return result;
}

std::string compiler_flags() {
#if defined(_MSC_VER)
  return "/O2|/std:c++17|/EHsc|/fp:precise";
#else
  return "-O3|-std=c++17|-ffp-contract=off|-fno-fast-math";
#endif
}

std::string compiler_id() {
#if defined(_MSC_VER)
  return std::string("MSVC-") + std::to_string(_MSC_VER);
#elif defined(__clang__)
  return std::string("Clang-") + __clang_version__;
#elif defined(__GNUC__)
  return std::string("GCC-") + __VERSION__;
#else
  return "UNKNOWN-COMPILER";
#endif
}

}  // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, module) {
  module.def("abi_version", []() { return std::string(kAbi); });
  module.def("host_kind", []() { return std::string(kHostKind); });
  module.def("native_threads", []() { return 1; });
  module.def("language_standard", []() { return std::string("C++17"); });
  module.def("compiler_flags", &compiler_flags);
  module.def("compiler_id", &compiler_id);
  module.def(
      "run_factual_trajectory",
      &run_factual_trajectory,
      py::arg("episode"),
      py::arg("parameters"),
      py::arg("mode"));
  module.def(
      "run_shadow_trajectory",
      &run_shadow_trajectory,
      py::arg("episode"),
      py::arg("intact_trace"),
      py::arg("parameters"));
  module.def("run_suffix", &run_suffix, py::arg("batch"), py::arg("parameters"));
}
