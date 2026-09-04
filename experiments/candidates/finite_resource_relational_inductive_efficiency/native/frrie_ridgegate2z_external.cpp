// Package-owned C++17 CPU environment for FRRIE RIDGEGATE-2Z.
//
// This translation unit deliberately contains no policy, recurrent state,
// action codec, autonomous inference, RNG, checkpoint identity, network, or
// GPU behavior.  Callers provide complete FP32 potential-outcome tapes and
// legal external actions.  Snapshot bytes are the direct packed state POD.

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <type_traits>

#if defined(_WIN32)
#define FRRIE_EXPORT extern "C" __declspec(dllexport)
#else
#define FRRIE_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {

// Semantic external-action seam V2.  Export suffix `_v1` is the frozen first
// revision of the packed C calling convention, not the semantic seam label.
constexpr std::uint32_t kAbiVersion = 2;
constexpr std::uint32_t kStateVersion = 1;
constexpr int kMaxAgents = 21;
constexpr int kHorizon = 12;
constexpr int kBasins = 2;
constexpr int kEventsPerBasin = 3;
constexpr int kActions = 6;
constexpr int kObservationDim = 22;
constexpr int kFifoCapacity = 4;

enum Role : std::uint8_t {
  kWestSurveyor = 0,
  kEastSurveyor = 1,
  kRidgeRelay = 2,
  kInactiveRole = 255,
};

enum Action : std::uint8_t {
  kScan = 0,
  kUplink = 1,
  kListenWest = 2,
  kListenEast = 3,
  kForwardBase = 4,
  kHold = 5,
  kUnsetAction = 255,
};

enum ErrorCode : std::int32_t {
  kOk = 0,
  kNull = 1,
  kAbiMismatch = 2,
  kBatchCount = 3,
  kRoster = 4,
  kEventTimes = 5,
  kUniformNonfinite = 6,
  kUniformRange = 7,
  kStateVersionMismatch = 8,
  kStateInvalid = 9,
  kActionIllegal = 10,
  kTerminal = 11,
  kSnapshotSize = 12,
};

#pragma pack(push, 1)

struct ReportV1 {
  std::uint8_t occupied;
  std::uint8_t basin;
  std::uint8_t event_ordinal;
  std::uint8_t reserved;
  std::int32_t event_time;
};

struct PendingUplinkV1 {
  ReportV1 report;
  std::int16_t sender;
  std::int16_t receiver;
  std::uint8_t decoded;
};

struct PendingBaseV1 {
  ReportV1 report;
  std::int16_t sender;
  std::uint8_t decoded;
  std::uint8_t reserved;
};

struct MetricsV1 {
  std::uint32_t dw;
  std::uint32_t de;
  std::uint32_t duplicate_arrivals;
  std::uint32_t expired_arrivals;
  std::uint32_t collision_loss;
  std::uint32_t empty_actions;
  std::uint32_t radio_actions;
  std::uint32_t waste_actions;
  std::uint32_t new_timely_deliveries;
  float waste;
  float terminal_audit;
};

struct ResetInputV1 {
  std::uint32_t abi_version;
  std::uint32_t state_version;
  std::int32_t roster;
  std::uint32_t reserved;
  std::int32_t event_times[kBasins][kEventsPerBasin];
  float detection_uniforms[kHorizon][kMaxAgents];
  float uplink_uniforms[kHorizon][kMaxAgents][kMaxAgents];
  float base_uniforms[kHorizon][kMaxAgents];
};

struct NativeStateV1 {
  std::uint32_t abi_version;
  std::uint32_t state_version;
  std::int32_t roster;
  std::int32_t slot;
  std::uint8_t terminal;
  std::uint8_t predecision_prepared;
  std::uint8_t reserved[2];
  std::uint8_t roles[kMaxAgents];
  std::int32_t event_times[kBasins][kEventsPerBasin];
  float detection_uniforms[kHorizon][kMaxAgents];
  float uplink_uniforms[kHorizon][kMaxAgents][kMaxAgents];
  float base_uniforms[kHorizon][kMaxAgents];
  ReportV1 fifos[kMaxAgents][kFifoCapacity];
  std::uint8_t fifo_sizes[kMaxAgents];
  PendingUplinkV1 pending_uplinks[kMaxAgents];
  std::uint8_t pending_uplink_count;
  PendingBaseV1 pending_base;
  std::uint8_t pending_base_present;
  std::uint8_t delivered[kBasins][kEventsPerBasin];
  std::uint8_t previous_action[kMaxAgents];
  std::uint8_t previous_success[kMaxAgents];
  MetricsV1 metrics;
};

struct StepInputV1 {
  std::uint32_t abi_version;
  std::uint8_t actions[kMaxAgents];
  std::uint8_t reserved[3];
};

struct ObservationOutputV1 {
  std::uint32_t abi_version;
  std::uint32_t state_version;
  std::int32_t roster;
  std::int32_t slot;
  std::uint8_t terminal;
  std::uint8_t reserved[3];
  std::uint8_t roles[kMaxAgents];
  std::uint8_t legal_masks[kMaxAgents][kActions];
  float observations[kMaxAgents][kObservationDim];
};

struct StepOutputV1 {
  std::uint32_t abi_version;
  std::uint32_t state_version;
  std::int32_t slot_before;
  std::int32_t slot_after;
  std::uint8_t terminal;
  std::uint8_t reserved[3];
  std::uint8_t previous_success[kMaxAgents];
  MetricsV1 metrics;
};

#pragma pack(pop)

static_assert(std::is_standard_layout<NativeStateV1>::value, "state must be POD");
static_assert(std::is_trivially_copyable<NativeStateV1>::value, "state must be directly snapshotable");
static_assert(sizeof(ReportV1) == 8, "report ABI drift");
static_assert(sizeof(PendingUplinkV1) == 13, "pending uplink ABI drift");
static_assert(sizeof(PendingBaseV1) == 12, "pending base ABI drift");
static_assert(sizeof(MetricsV1) == 44, "metrics ABI drift");

bool registered_roster(const int roster) {
  return roster == 6 || roster == 9 || roster == 15 || roster == 21;
}

bool batch_valid(const std::uint32_t count, const std::uint32_t native_width) {
  return native_width > 0 && count > 0 && count <= native_width;
}

bool uniform_finite(const float value) { return std::isfinite(value); }
bool uniform_in_range(const float value) { return value >= 0.0f && value < 1.0f; }

std::int32_t validate_tape(const std::int32_t event_times[kBasins][kEventsPerBasin],
                           const float detection[kHorizon][kMaxAgents],
                           const float uplink[kHorizon][kMaxAgents][kMaxAgents],
                           const float base[kHorizon][kMaxAgents]) {
  for (int basin = 0; basin < kBasins; ++basin) {
    for (int ordinal = 0; ordinal < kEventsPerBasin; ++ordinal) {
      const int time = event_times[basin][ordinal];
      if (time < 0 || time > 7) return kEventTimes;
      for (int prior = 0; prior < ordinal; ++prior) {
        if (event_times[basin][prior] == time) return kEventTimes;
      }
    }
  }
  for (int slot = 0; slot < kHorizon; ++slot) {
    for (int agent = 0; agent < kMaxAgents; ++agent) {
      const float detection_value = detection[slot][agent];
      const float base_value = base[slot][agent];
      if (!uniform_finite(detection_value) || !uniform_finite(base_value)) {
        return kUniformNonfinite;
      }
      if (!uniform_in_range(detection_value) || !uniform_in_range(base_value)) {
        return kUniformRange;
      }
      for (int receiver = 0; receiver < kMaxAgents; ++receiver) {
        const float value = uplink[slot][agent][receiver];
        if (!uniform_finite(value)) return kUniformNonfinite;
        if (!uniform_in_range(value)) return kUniformRange;
      }
    }
  }
  return kOk;
}

std::int32_t validate_reset_input(const ResetInputV1& input) {
  if (input.abi_version != kAbiVersion) return kAbiMismatch;
  if (input.state_version != kStateVersion) return kStateVersionMismatch;
  if (input.reserved != 0) return kAbiMismatch;
  if (!registered_roster(input.roster)) return kRoster;
  return validate_tape(input.event_times, input.detection_uniforms,
                       input.uplink_uniforms, input.base_uniforms);
}

bool report_valid(const ReportV1& report, const NativeStateV1& state) {
  if (report.reserved != 0) return false;
  if (report.occupied == 0) return report.basin == 0 && report.event_ordinal == 0 &&
                                    report.event_time == 0;
  if (report.occupied != 1 || report.basin >= kBasins ||
      report.event_ordinal >= kEventsPerBasin) {
    return false;
  }
  return report.event_time == state.event_times[report.basin][report.event_ordinal];
}

std::int32_t validate_state(const NativeStateV1& state) {
  if (state.abi_version != kAbiVersion || state.state_version != kStateVersion) {
    return kStateVersionMismatch;
  }
  if (!registered_roster(state.roster)) return kStateInvalid;
  if (state.slot < 0 || state.slot > kHorizon) return kStateInvalid;
  if ((state.terminal != 0 && state.terminal != 1) ||
      (state.predecision_prepared != 0 && state.predecision_prepared != 1)) {
    return kStateInvalid;
  }
  if (state.reserved[0] != 0 || state.reserved[1] != 0) return kStateInvalid;
  if ((state.slot == kHorizon) != (state.terminal == 1)) return kStateInvalid;
  if (state.terminal == 0 && state.predecision_prepared != 1) return kStateInvalid;
  const int per_role = state.roster / 3;
  for (int agent = 0; agent < kMaxAgents; ++agent) {
    const std::uint8_t expected = agent < per_role
                                      ? kWestSurveyor
                                      : (agent < 2 * per_role
                                             ? kEastSurveyor
                                             : (agent < state.roster ? kRidgeRelay : kInactiveRole));
    if (state.roles[agent] != expected) return kStateInvalid;
    if (state.fifo_sizes[agent] > kFifoCapacity) return kStateInvalid;
    const int role_capacity = expected == kRidgeRelay ? 4 : (expected == kInactiveRole ? 0 : 2);
    if (state.fifo_sizes[agent] > role_capacity) return kStateInvalid;
    for (int position = 0; position < kFifoCapacity; ++position) {
      const bool should_occupy = position < state.fifo_sizes[agent];
      if ((state.fifos[agent][position].occupied == 1) != should_occupy ||
          !report_valid(state.fifos[agent][position], state)) {
        return kStateInvalid;
      }
    }
    if (agent < state.roster) {
      if (state.previous_action[agent] != kUnsetAction &&
          state.previous_action[agent] >= kActions) return kStateInvalid;
      if (state.previous_success[agent] > 1) return kStateInvalid;
    } else if (state.previous_action[agent] != kUnsetAction ||
               state.previous_success[agent] != 0) {
      return kStateInvalid;
    }
  }
  if (state.pending_uplink_count > kMaxAgents || state.pending_base_present > 1) {
    return kStateInvalid;
  }
  for (int index = 0; index < state.pending_uplink_count; ++index) {
    const PendingUplinkV1& pending = state.pending_uplinks[index];
    if (pending.decoded != 1 || pending.sender < 0 || pending.sender >= state.roster ||
        pending.receiver < 0 || pending.receiver >= state.roster ||
        state.roles[pending.receiver] != kRidgeRelay ||
        !report_valid(pending.report, state) || pending.report.occupied != 1) {
      return kStateInvalid;
    }
  }
  if (state.pending_base_present) {
    if (state.pending_base.decoded != 1 || state.pending_base.sender < 0 ||
        state.pending_base.sender >= state.roster ||
        state.roles[state.pending_base.sender] != kRidgeRelay ||
        state.pending_base.reserved != 0 ||
        !report_valid(state.pending_base.report, state) ||
        state.pending_base.report.occupied != 1) {
      return kStateInvalid;
    }
  }
  std::uint32_t delivered_counts[kBasins] = {};
  for (int basin = 0; basin < kBasins; ++basin) {
    for (int ordinal = 0; ordinal < kEventsPerBasin; ++ordinal) {
      if (state.delivered[basin][ordinal] > 1) return kStateInvalid;
      delivered_counts[basin] += state.delivered[basin][ordinal];
    }
  }
  if (state.metrics.dw != delivered_counts[0] || state.metrics.de != delivered_counts[1] ||
      state.metrics.waste_actions > state.metrics.radio_actions ||
      state.metrics.new_timely_deliveries !=
          state.metrics.dw + state.metrics.de ||
      !std::isfinite(state.metrics.waste) ||
      !std::isfinite(state.metrics.terminal_audit) || state.metrics.waste < 0.0f ||
      state.metrics.waste > 1.0f) {
    return kStateInvalid;
  }
  return validate_tape(state.event_times, state.detection_uniforms,
                       state.uplink_uniforms, state.base_uniforms) == kOk
             ? kOk
             : kStateInvalid;
}

bool legal_action(const std::uint8_t role, const std::uint8_t action) {
  if (role == kWestSurveyor || role == kEastSurveyor) {
    return action == kScan || action == kUplink || action == kHold;
  }
  if (role == kRidgeRelay) {
    return action == kListenWest || action == kListenEast ||
           action == kForwardBase || action == kHold;
  }
  return false;
}

float logistic_loaded(const float p0, const int multiplicity) {
  const float logit = std::log(p0 / (1.0f - p0));
  const float shifted = logit - 0.22f * static_cast<float>(multiplicity - 1);
  return 1.0f / (1.0f + std::exp(-shifted));
}

void clear_report(ReportV1& report) { std::memset(&report, 0, sizeof(report)); }

void pop_fifo_head(NativeStateV1& state, const int agent) {
  const int size = state.fifo_sizes[agent];
  if (size <= 0) return;
  for (int position = 1; position < size; ++position) {
    state.fifos[agent][position - 1] = state.fifos[agent][position];
  }
  clear_report(state.fifos[agent][size - 1]);
  state.fifo_sizes[agent] = static_cast<std::uint8_t>(size - 1);
}

void append_fifo(NativeStateV1& state, const int agent, const ReportV1& report) {
  const int capacity = state.roles[agent] == kRidgeRelay ? 4 : 2;
  if (state.fifo_sizes[agent] == capacity) pop_fifo_head(state, agent);
  const int tail = state.fifo_sizes[agent];
  state.fifos[agent][tail] = report;
  state.fifo_sizes[agent] = static_cast<std::uint8_t>(tail + 1);
}

void purge_expired(NativeStateV1& state) {
  for (int agent = 0; agent < state.roster; ++agent) {
    int position = 0;
    while (position < state.fifo_sizes[agent]) {
      if (state.slot >= state.fifos[agent][position].event_time + 4) {
        const int size = state.fifo_sizes[agent];
        for (int next = position + 1; next < size; ++next) {
          state.fifos[agent][next - 1] = state.fifos[agent][next];
        }
        clear_report(state.fifos[agent][size - 1]);
        state.fifo_sizes[agent] = static_cast<std::uint8_t>(size - 1);
      } else {
        ++position;
      }
    }
  }
}

void update_metric_floats(NativeStateV1& state) {
  MetricsV1& metrics = state.metrics;
  metrics.waste = metrics.radio_actions == 0
                      ? 0.0f
                      : static_cast<float>(metrics.waste_actions) /
                            static_cast<float>(metrics.radio_actions);
  const float dw = static_cast<float>(metrics.dw);
  const float de = static_cast<float>(metrics.de);
  metrics.terminal_audit = 0.65f * (dw + de) / 6.0f +
                           0.25f * std::min(dw, de) / 3.0f +
                           0.10f * (1.0f - metrics.waste);
}

void prepare_predecision(NativeStateV1& state) {
  std::memset(state.previous_success, 0, sizeof(state.previous_success));
  bool sender_decoded[kMaxAgents] = {};
  bool sender_nonexpired[kMaxAgents] = {};

  // Step 1: all decoded uplink copies append (or expire) before any dequeue.
  for (int index = 0; index < state.pending_uplink_count; ++index) {
    const PendingUplinkV1& pending = state.pending_uplinks[index];
    sender_decoded[pending.sender] = true;
    const bool expired = state.slot >= pending.report.event_time + 4;
    if (expired) {
      ++state.metrics.expired_arrivals;
    } else {
      append_fifo(state, pending.receiver, pending.report);
      sender_nonexpired[pending.sender] = true;
      state.previous_success[pending.receiver] = 1;
    }
  }

  // The one decoded base arrival is classified before its sender dequeue.
  int base_sender = -1;
  if (state.pending_base_present) {
    const PendingBaseV1& pending = state.pending_base;
    base_sender = pending.sender;
    const ReportV1& report = pending.report;
    const bool expired = state.slot >= report.event_time + 4;
    const bool duplicate = state.delivered[report.basin][report.event_ordinal] != 0;
    if (expired) ++state.metrics.expired_arrivals;
    if (duplicate) ++state.metrics.duplicate_arrivals;
    if (!expired && !duplicate) {
      state.delivered[report.basin][report.event_ordinal] = 1;
      if (report.basin == 0) {
        ++state.metrics.dw;
      } else {
        ++state.metrics.de;
      }
      ++state.metrics.new_timely_deliveries;
      state.previous_success[pending.sender] = 1;
    }
  }

  // Step 2: link acknowledgement dequeues heads even for expired/duplicates.
  for (int sender = 0; sender < state.roster; ++sender) {
    if (sender_decoded[sender]) {
      pop_fifo_head(state, sender);
      state.previous_success[sender] = sender_nonexpired[sender] ? 1 : 0;
    }
  }
  if (base_sender >= 0) pop_fifo_head(state, base_sender);

  std::memset(state.pending_uplinks, 0, sizeof(state.pending_uplinks));
  state.pending_uplink_count = 0;
  std::memset(&state.pending_base, 0, sizeof(state.pending_base));
  state.pending_base_present = 0;

  // Step 3: expiration purge precedes observation.
  purge_expired(state);
  state.predecision_prepared = 1;
  update_metric_floats(state);
}

void initialize_state(NativeStateV1& state, const ResetInputV1& input) {
  std::memset(&state, 0, sizeof(state));
  state.abi_version = kAbiVersion;
  state.state_version = kStateVersion;
  state.roster = input.roster;
  state.slot = 0;
  state.terminal = 0;
  state.predecision_prepared = 1;
  const int per_role = state.roster / 3;
  for (int agent = 0; agent < kMaxAgents; ++agent) {
    state.roles[agent] = agent < per_role
                             ? kWestSurveyor
                             : (agent < 2 * per_role
                                    ? kEastSurveyor
                                    : (agent < state.roster ? kRidgeRelay : kInactiveRole));
    state.previous_action[agent] = kUnsetAction;
  }
  std::memcpy(state.event_times, input.event_times, sizeof(state.event_times));
  std::memcpy(state.detection_uniforms, input.detection_uniforms,
              sizeof(state.detection_uniforms));
  std::memcpy(state.uplink_uniforms, input.uplink_uniforms,
              sizeof(state.uplink_uniforms));
  std::memcpy(state.base_uniforms, input.base_uniforms, sizeof(state.base_uniforms));
  update_metric_floats(state);
}

void set_legal_mask(const std::uint8_t role, std::uint8_t mask[kActions]) {
  std::memset(mask, 0, kActions);
  if (role == kWestSurveyor || role == kEastSurveyor) {
    mask[kScan] = mask[kUplink] = mask[kHold] = 1;
  } else if (role == kRidgeRelay) {
    mask[kListenWest] = mask[kListenEast] = mask[kForwardBase] = mask[kHold] = 1;
  }
}

void fill_observation(const NativeStateV1& state, ObservationOutputV1& output) {
  std::memset(&output, 0, sizeof(output));
  output.abi_version = kAbiVersion;
  output.state_version = kStateVersion;
  output.roster = state.roster;
  output.slot = state.slot;
  output.terminal = state.terminal;
  for (int agent = 0; agent < kMaxAgents; ++agent) {
    output.roles[agent] = state.roles[agent];
    if (agent >= state.roster) continue;
    set_legal_mask(state.roles[agent], output.legal_masks[agent]);
    float* observation = output.observations[agent];
    observation[state.roles[agent]] = 1.0f;
    observation[3] = static_cast<float>(state.slot) / 11.0f;
    const float normalized_count = static_cast<float>(state.roster / 3) / 7.0f;
    observation[4] = observation[5] = observation[6] = normalized_count;
    for (int position = 0; position < kFifoCapacity; ++position) {
      const int offset = 7 + 2 * position;
      if (position < state.fifo_sizes[agent]) {
        const ReportV1& report = state.fifos[agent][position];
        const int age = std::max(0, state.slot - report.event_time);
        observation[offset] = 1.0f;
        observation[offset + 1] = static_cast<float>(std::min(age, 3)) / 3.0f;
      }
    }
    if (state.previous_action[agent] < kActions) {
      observation[15 + state.previous_action[agent]] = 1.0f;
    }
    observation[21] = state.previous_success[agent] ? 1.0f : 0.0f;
  }
}

ReportV1 fifo_head(const NativeStateV1& state, const int agent) {
  return state.fifos[agent][0];
}

void increment_waste(NativeStateV1& state) { ++state.metrics.waste_actions; }

void resolve_uplink(NativeStateV1& state, const StepInputV1& input) {
  const int slot = state.slot;
  const int per_role = state.roster / 3;
  for (int basin = 0; basin < kBasins; ++basin) {
    int transmitters[kMaxAgents] = {};
    int transmitter_count = 0;
    const int begin = basin == 0 ? 0 : per_role;
    const int end = basin == 0 ? per_role : 2 * per_role;
    for (int sender = begin; sender < end; ++sender) {
      if (input.actions[sender] != kUplink) continue;
      ++state.metrics.radio_actions;
      if (state.fifo_sizes[sender] == 0) {
        ++state.metrics.empty_actions;
        increment_waste(state);
      } else {
        transmitters[transmitter_count++] = sender;
      }
    }
    if (transmitter_count >= 2) {
      state.metrics.collision_loss += static_cast<std::uint32_t>(transmitter_count);
    }

    bool transmitter_useful = false;
    const int sole_sender = transmitter_count == 1 ? transmitters[0] : -1;
    const std::uint8_t listen_action = basin == 0 ? kListenWest : kListenEast;
    for (int receiver = 2 * per_role; receiver < state.roster; ++receiver) {
      if (input.actions[receiver] != listen_action) continue;
      ++state.metrics.radio_actions;
      bool enqueued_nonexpired = false;
      if (slot < kHorizon - 1 && sole_sender >= 0) {
        const float p0 = basin == 0 ? 0.86f : 0.78f;
        const float probability = logistic_loaded(p0, per_role);
        if (state.uplink_uniforms[slot][sole_sender][receiver] < probability) {
          PendingUplinkV1 pending{};
          pending.report = fifo_head(state, sole_sender);
          pending.sender = static_cast<std::int16_t>(sole_sender);
          pending.receiver = static_cast<std::int16_t>(receiver);
          pending.decoded = 1;
          state.pending_uplinks[state.pending_uplink_count++] = pending;
          enqueued_nonexpired = slot + 1 < pending.report.event_time + 4;
          transmitter_useful = transmitter_useful || enqueued_nonexpired;
        }
      }
      if (!enqueued_nonexpired) increment_waste(state);
    }
    for (int index = 0; index < transmitter_count; ++index) {
      if (transmitter_count != 1 || !transmitter_useful || slot == kHorizon - 1) {
        increment_waste(state);
      }
    }
  }
}

void resolve_base(NativeStateV1& state, const StepInputV1& input) {
  const int slot = state.slot;
  const int per_role = state.roster / 3;
  int transmitters[kMaxAgents] = {};
  int transmitter_count = 0;
  for (int relay = 2 * per_role; relay < state.roster; ++relay) {
    if (input.actions[relay] != kForwardBase) continue;
    ++state.metrics.radio_actions;
    if (state.fifo_sizes[relay] == 0) {
      ++state.metrics.empty_actions;
      increment_waste(state);
    } else {
      transmitters[transmitter_count++] = relay;
    }
  }
  if (transmitter_count >= 2) {
    state.metrics.collision_loss += static_cast<std::uint32_t>(transmitter_count);
  }
  bool new_timely_delivery = false;
  if (slot < kHorizon - 1 && transmitter_count == 1) {
    const int sender = transmitters[0];
    const float probability = logistic_loaded(0.90f, per_role);
    if (state.base_uniforms[slot][sender] < probability) {
      PendingBaseV1 pending{};
      pending.report = fifo_head(state, sender);
      pending.sender = static_cast<std::int16_t>(sender);
      pending.decoded = 1;
      state.pending_base = pending;
      state.pending_base_present = 1;
      new_timely_delivery = slot + 1 < pending.report.event_time + 4 &&
                            state.delivered[pending.report.basin]
                                           [pending.report.event_ordinal] == 0;
    }
  }
  for (int index = 0; index < transmitter_count; ++index) {
    if (transmitter_count != 1 || !new_timely_delivery || slot == kHorizon - 1) {
      increment_waste(state);
    }
  }
}

void resolve_scan(NativeStateV1& state, const StepInputV1& input) {
  const int slot = state.slot;
  const int per_role = state.roster / 3;
  for (int basin = 0; basin < kBasins; ++basin) {
    int ordinal_at_slot = -1;
    for (int ordinal = 0; ordinal < kEventsPerBasin; ++ordinal) {
      if (state.event_times[basin][ordinal] == slot) ordinal_at_slot = ordinal;
    }
    if (ordinal_at_slot < 0) continue;
    const int begin = basin == 0 ? 0 : per_role;
    const int end = basin == 0 ? per_role : 2 * per_role;
    for (int surveyor = begin; surveyor < end; ++surveyor) {
      if (input.actions[surveyor] != kScan ||
          state.detection_uniforms[slot][surveyor] >= 0.75f) {
        continue;
      }
      ReportV1 report{};
      report.occupied = 1;
      report.basin = static_cast<std::uint8_t>(basin);
      report.event_ordinal = static_cast<std::uint8_t>(ordinal_at_slot);
      report.event_time = slot;
      append_fifo(state, surveyor, report);
    }
  }
}

void execute_step(NativeStateV1& state, const StepInputV1& input, StepOutputV1& output) {
  const int slot_before = state.slot;
  for (int agent = 0; agent < state.roster; ++agent) {
    state.previous_action[agent] = input.actions[agent];
  }
  std::memset(state.previous_success, 0, sizeof(state.previous_success));
  state.predecision_prepared = 0;

  // Step 5: all radio decisions use the same predecision FIFO heads.
  resolve_uplink(state, input);
  resolve_base(state, input);
  // Step 6: scan append follows all radio scheduling.
  resolve_scan(state, input);

  ++state.slot;
  if (state.slot == kHorizon) {
    // Slot-11 transmissions never create pending arrivals.
    state.terminal = 1;
    state.predecision_prepared = 0;
    std::memset(state.pending_uplinks, 0, sizeof(state.pending_uplinks));
    state.pending_uplink_count = 0;
    std::memset(&state.pending_base, 0, sizeof(state.pending_base));
    state.pending_base_present = 0;
    update_metric_floats(state);
  } else {
    prepare_predecision(state);
  }

  std::memset(&output, 0, sizeof(output));
  output.abi_version = kAbiVersion;
  output.state_version = kStateVersion;
  output.slot_before = slot_before;
  output.slot_after = state.slot;
  output.terminal = state.terminal;
  std::memcpy(output.previous_success, state.previous_success,
              sizeof(output.previous_success));
  output.metrics = state.metrics;
}

}  // namespace

FRRIE_EXPORT std::uint32_t frrie_native_abi_v1() { return kAbiVersion; }

FRRIE_EXPORT std::size_t frrie_native_state_size_v1() { return sizeof(NativeStateV1); }

FRRIE_EXPORT std::int32_t frrie_reset_batch_v1(
    NativeStateV1* states, const ResetInputV1* inputs, const std::uint32_t count,
    const std::uint32_t native_width) {
  if (states == nullptr || inputs == nullptr) return kNull;
  if (!batch_valid(count, native_width)) return kBatchCount;
  for (std::uint32_t lane = 0; lane < count; ++lane) {
    const std::int32_t error = validate_reset_input(inputs[lane]);
    if (error != kOk) return error;
  }
  for (std::uint32_t lane = 0; lane < count; ++lane) initialize_state(states[lane], inputs[lane]);
  return kOk;
}

FRRIE_EXPORT std::int32_t frrie_observe_batch_v1(
    const NativeStateV1* states, ObservationOutputV1* outputs,
    const std::uint32_t count, const std::uint32_t native_width) {
  if (states == nullptr || outputs == nullptr) return kNull;
  if (!batch_valid(count, native_width)) return kBatchCount;
  for (std::uint32_t lane = 0; lane < count; ++lane) {
    const std::int32_t error = validate_state(states[lane]);
    if (error != kOk) return error;
    if (states[lane].terminal) return kTerminal;
  }
  for (std::uint32_t lane = 0; lane < count; ++lane) fill_observation(states[lane], outputs[lane]);
  return kOk;
}

FRRIE_EXPORT std::int32_t frrie_step_batch_v1(
    NativeStateV1* states, const StepInputV1* inputs, StepOutputV1* outputs,
    const std::uint32_t count, const std::uint32_t native_width) {
  if (states == nullptr || inputs == nullptr || outputs == nullptr) return kNull;
  if (!batch_valid(count, native_width)) return kBatchCount;
  for (std::uint32_t lane = 0; lane < count; ++lane) {
    const std::int32_t state_error = validate_state(states[lane]);
    if (state_error != kOk) return state_error;
    if (states[lane].terminal) return kTerminal;
    if (inputs[lane].abi_version != kAbiVersion) return kAbiMismatch;
    if (inputs[lane].reserved[0] != 0 || inputs[lane].reserved[1] != 0 ||
        inputs[lane].reserved[2] != 0) return kAbiMismatch;
    for (int agent = 0; agent < states[lane].roster; ++agent) {
      if (!legal_action(states[lane].roles[agent], inputs[lane].actions[agent])) {
        return kActionIllegal;
      }
    }
  }
  for (std::uint32_t lane = 0; lane < count; ++lane) {
    execute_step(states[lane], inputs[lane], outputs[lane]);
  }
  return kOk;
}

FRRIE_EXPORT std::int32_t frrie_snapshot_batch_v1(
    const NativeStateV1* states, void* snapshot_bytes, const std::size_t byte_count,
    const std::uint32_t count, const std::uint32_t native_width) {
  if (states == nullptr || snapshot_bytes == nullptr) return kNull;
  if (!batch_valid(count, native_width)) return kBatchCount;
  if (byte_count != sizeof(NativeStateV1) * static_cast<std::size_t>(count)) {
    return kSnapshotSize;
  }
  for (std::uint32_t lane = 0; lane < count; ++lane) {
    const std::int32_t error = validate_state(states[lane]);
    if (error != kOk) return error;
  }
  std::memmove(snapshot_bytes, states, byte_count);
  return kOk;
}

FRRIE_EXPORT std::int32_t frrie_restore_batch_v1(
    NativeStateV1* states, const void* snapshot_bytes, const std::size_t byte_count,
    const std::uint32_t count, const std::uint32_t native_width) {
  if (states == nullptr || snapshot_bytes == nullptr) return kNull;
  if (!batch_valid(count, native_width)) return kBatchCount;
  if (byte_count != sizeof(NativeStateV1) * static_cast<std::size_t>(count)) {
    return kSnapshotSize;
  }
  const auto* snapshots = static_cast<const NativeStateV1*>(snapshot_bytes);
  for (std::uint32_t lane = 0; lane < count; ++lane) {
    const std::int32_t error = validate_state(snapshots[lane]);
    if (error != kOk) return error;
  }
  std::memmove(states, snapshot_bytes, byte_count);
  return kOk;
}
