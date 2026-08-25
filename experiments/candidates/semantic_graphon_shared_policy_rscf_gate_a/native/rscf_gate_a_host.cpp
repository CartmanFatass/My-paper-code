#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace {

constexpr const char* kAbiTag = "SGSP_RSCF_NATIVE_ABI_V1";
constexpr int kNativeThreads = 1;
constexpr int kMaxAgents = 15;
constexpr int kHorizon = 12;
constexpr int kHiddenDim = 64;
constexpr int kFifoCapacity = 4;
constexpr int kReportLifetime = 4;
constexpr std::uint64_t kDigestMultiplier = 1000003ULL;

using I32Array = py::array_t<std::int32_t, py::array::c_style>;
using U32Array = py::array_t<std::uint32_t, py::array::c_style>;
using F64Array = py::array_t<double, py::array::c_style>;

struct Report {
    int basin;
    int ordinal;
    int time;
};

struct ScheduledUplink {
    int due;
    int sender;
    Report report;
    std::vector<int> listeners;
    std::vector<int> decoded;
};

struct ScheduledBase {
    int due;
    int sender;
    Report report;
};

void require_shape(
    const py::buffer_info& info,
    const std::vector<py::ssize_t>& shape,
    const char* name) {
    if (info.ndim != static_cast<py::ssize_t>(shape.size())) {
        throw std::invalid_argument(
            std::string(name) + " rank differs from SGSP_RSCF_NATIVE_ABI_V1");
    }
    py::ssize_t expected_stride = info.itemsize;
    for (py::ssize_t axis = info.ndim - 1; axis >= 0; --axis) {
        if (info.shape[axis] != shape[static_cast<std::size_t>(axis)]) {
            throw std::invalid_argument(
                std::string(name) + " shape differs from SGSP_RSCF_NATIVE_ABI_V1");
        }
        if (info.strides[axis] != expected_stride) {
            throw std::invalid_argument(std::string(name) + " must be C-contiguous");
        }
        expected_stride *= info.shape[axis];
    }
}

bool supported_width(py::ssize_t width) {
    return width == 32 || width == 64 || width == 128 || width == 256;
}

int floor_mod(int value, int modulus) {
    const int remainder = value % modulus;
    return remainder < 0 ? remainder + modulus : remainder;
}

std::int64_t python_round(double value) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument("non-finite hidden fixture payload");
    }
    const double lower = std::floor(value);
    const double fraction = value - lower;
    const auto integer = static_cast<std::int64_t>(lower);
    if (fraction < 0.5) {
        return integer;
    }
    if (fraction > 0.5) {
        return integer + 1;
    }
    return (integer & 1LL) == 0 ? integer : integer + 1;
}

std::uint64_t digest_step(std::uint64_t digest, std::int64_t value) {
    return digest * kDigestMultiplier + static_cast<std::uint64_t>(value) + 97ULL;
}

void append_fifo(std::vector<Report>& fifo, const Report& report, std::size_t capacity) {
    fifo.push_back(report);
    if (fifo.size() > capacity) {
        fifo.erase(fifo.begin());
    }
}

int policy_action(
    int role,
    int slot,
    int fifo_count,
    int previous_action,
    int previous_success,
    const double* hidden,
    std::uint32_t action_word) {
    constexpr int role01_actions[3] = {0, 1, 5};
    constexpr int role2_actions[4] = {2, 3, 4, 5};
    const int* legal = role == 2 ? role2_actions : role01_actions;
    const int legal_count = role == 2 ? 4 : 3;
    const int hidden_index = (role * 7) % kHiddenDim;
    const int hidden_code = static_cast<int>(python_round(hidden[hidden_index] * 64.0));
    int weights[4] = {0, 0, 0, 0};
    int total = 0;
    for (int index = 0; index < legal_count; ++index) {
        const int action = legal[index];
        const int term = role * 17 + action * 23 + slot * 7 + fifo_count * 11 +
            (previous_action + 1) * 3 + previous_success * 5 + hidden_code;
        weights[index] = 1 + floor_mod(term, 31);
        total += weights[index];
    }
    int needle = static_cast<int>(action_word % static_cast<std::uint32_t>(total));
    for (int index = 0; index < legal_count; ++index) {
        if (needle < weights[index]) {
            return legal[index];
        }
        needle -= weights[index];
    }
    throw std::logic_error("nonempty fixture policy support did not select an action");
}

void advance_hidden(
    double* hidden,
    int slot,
    int role,
    int action,
    int fifo_count,
    int success) {
    for (int component = 0; component < kHiddenDim; ++component) {
        const auto prior_code = python_round(hidden[component] * 64.0);
        const int injection = floor_mod(
            (slot + 1) * 3 + role * 5 + action * 7 + fifo_count * 11 +
                success * 13 + component,
            65) - 32;
        hidden[component] = static_cast<double>(prior_code + injection) / 128.0;
    }
}

py::dict run_suffix_batch(
    const I32Array& n_agents,
    const I32Array& roles,
    const I32Array& origin_slot,
    const I32Array& focal_index,
    const I32Array& forced_action,
    const I32Array& factual_actions,
    const I32Array& initial_fifo_basin,
    const I32Array& initial_fifo_time,
    const I32Array& initial_previous_action,
    const I32Array& initial_previous_success,
    const F64Array& initial_hidden,
    const I32Array& event_times,
    const U32Array& action_tape,
    const U32Array& detection_tape,
    const U32Array& uplink_tape,
    const U32Array& base_tape) {
    const auto n_info = n_agents.request();
    if (n_info.ndim != 1 || !supported_width(n_info.shape[0])) {
        throw std::invalid_argument("n_agents must have a supported Gate A width");
    }
    const py::ssize_t width = n_info.shape[0];
    require_shape(n_info, {width}, "n_agents");
    const auto roles_info = roles.request();
    const auto origin_info = origin_slot.request();
    const auto focal_info = focal_index.request();
    const auto forced_info = forced_action.request();
    const auto factual_info = factual_actions.request();
    const auto fifo_basin_info = initial_fifo_basin.request();
    const auto fifo_time_info = initial_fifo_time.request();
    const auto previous_action_info = initial_previous_action.request();
    const auto previous_success_info = initial_previous_success.request();
    const auto hidden_info = initial_hidden.request();
    const auto events_info = event_times.request();
    const auto action_info = action_tape.request();
    const auto detection_info = detection_tape.request();
    const auto uplink_info = uplink_tape.request();
    const auto base_info = base_tape.request();
    require_shape(roles_info, {width, kMaxAgents}, "roles");
    require_shape(origin_info, {width}, "origin_slot");
    require_shape(focal_info, {width}, "focal_index");
    require_shape(forced_info, {width}, "forced_action");
    require_shape(factual_info, {width, kMaxAgents}, "factual_actions");
    require_shape(fifo_basin_info, {width, kMaxAgents, kFifoCapacity}, "initial_fifo_basin");
    require_shape(fifo_time_info, {width, kMaxAgents, kFifoCapacity}, "initial_fifo_time");
    require_shape(previous_action_info, {width, kMaxAgents}, "initial_previous_action");
    require_shape(previous_success_info, {width, kMaxAgents}, "initial_previous_success");
    require_shape(hidden_info, {width, kMaxAgents, kHiddenDim}, "initial_hidden");
    require_shape(events_info, {width, 2, 3}, "event_times");
    require_shape(action_info, {width, kHorizon, kMaxAgents}, "action_tape");
    require_shape(detection_info, {width, kHorizon, 2, 5}, "detection_tape");
    require_shape(uplink_info, {width, kHorizon, kMaxAgents}, "uplink_tape");
    require_shape(base_info, {width, kHorizon, kMaxAgents}, "base_tape");

    const auto* n_data = static_cast<const std::int32_t*>(n_info.ptr);
    const auto* roles_data = static_cast<const std::int32_t*>(roles_info.ptr);
    const auto* origin_data = static_cast<const std::int32_t*>(origin_info.ptr);
    const auto* focal_data = static_cast<const std::int32_t*>(focal_info.ptr);
    const auto* forced_data = static_cast<const std::int32_t*>(forced_info.ptr);
    const auto* factual_data = static_cast<const std::int32_t*>(factual_info.ptr);
    const auto* fifo_basin_data = static_cast<const std::int32_t*>(fifo_basin_info.ptr);
    const auto* fifo_time_data = static_cast<const std::int32_t*>(fifo_time_info.ptr);
    const auto* previous_action_data = static_cast<const std::int32_t*>(previous_action_info.ptr);
    const auto* previous_success_data = static_cast<const std::int32_t*>(previous_success_info.ptr);
    const auto* hidden_data = static_cast<const double*>(hidden_info.ptr);
    const auto* events_data = static_cast<const std::int32_t*>(events_info.ptr);
    const auto* action_data = static_cast<const std::uint32_t*>(action_info.ptr);
    const auto* detection_data = static_cast<const std::uint32_t*>(detection_info.ptr);
    const auto* uplink_data = static_cast<const std::uint32_t*>(uplink_info.ptr);
    const auto* base_data = static_cast<const std::uint32_t*>(base_info.ptr);
    for (py::ssize_t index = 0; index < hidden_info.size; ++index) {
        if (!std::isfinite(hidden_data[index])) {
            throw std::invalid_argument("initial_hidden contains non-finite values");
        }
    }

    F64Array terminal_return(width);
    py::array_t<std::uint64_t> audit_digest(width);
    I32Array transition_count(width);
    I32Array decision_count(width);
    I32Array delivery_count(width);
    I32Array waste_count(width);
    I32Array scan_count(width);
    py::array_t<std::int64_t> hidden_code_sum(width);
    I32Array forced_action_count(width);
    I32Array factual_teammate_count(width);
    auto* return_output = terminal_return.mutable_data();
    auto* digest_output = audit_digest.mutable_data();
    auto* transition_output = transition_count.mutable_data();
    auto* decision_output = decision_count.mutable_data();
    auto* delivery_output = delivery_count.mutable_data();
    auto* waste_output = waste_count.mutable_data();
    auto* scan_output = scan_count.mutable_data();
    auto* hidden_sum_output = hidden_code_sum.mutable_data();
    auto* forced_count_output = forced_action_count.mutable_data();
    auto* teammate_count_output = factual_teammate_count.mutable_data();

    {
        py::gil_scoped_release release;
        for (py::ssize_t lane = 0; lane < width; ++lane) {
            const int n = n_data[lane];
            if (n != 9 && n != 15) {
                throw std::invalid_argument("n_agents lane is not 9 or 15");
            }
            const int slot = origin_data[lane];
            const int focal = focal_data[lane];
            const int forced = forced_data[lane];
            if (slot < 0 || slot >= kHorizon || focal < 0 || focal >= n) {
                throw std::invalid_argument("origin or focal lane value is invalid");
            }
            std::array<int, kMaxAgents> lane_roles{};
            std::array<int, kMaxAgents> previous_action{};
            std::array<int, kMaxAgents> previous_success{};
            std::array<int, kMaxAgents> actions{};
            std::array<std::vector<Report>, kMaxAgents> fifo;
            std::array<double, kMaxAgents * kHiddenDim> hidden{};
            for (int agent = 0; agent < n; ++agent) {
                const std::size_t agent_offset = static_cast<std::size_t>(lane * kMaxAgents + agent);
                lane_roles[agent] = roles_data[agent_offset];
                previous_action[agent] = previous_action_data[agent_offset];
                previous_success[agent] = previous_success_data[agent_offset];
                for (int component = 0; component < kHiddenDim; ++component) {
                    hidden[agent * kHiddenDim + component] =
                        hidden_data[agent_offset * kHiddenDim + component];
                }
                for (int position = 0; position < kFifoCapacity; ++position) {
                    const std::size_t fifo_offset =
                        (agent_offset * kFifoCapacity) + position;
                    const int basin = fifo_basin_data[fifo_offset];
                    if (basin >= 0) {
                        fifo[agent].push_back(
                            Report{basin, position, fifo_time_data[fifo_offset]});
                    }
                }
            }
            std::array<std::array<int, 3>, 2> events{};
            for (int basin = 0; basin < 2; ++basin) {
                for (int ordinal = 0; ordinal < 3; ++ordinal) {
                    events[basin][ordinal] = events_data[(lane * 2 + basin) * 3 + ordinal];
                }
            }
            std::vector<ScheduledUplink> scheduled_uplinks;
            std::vector<ScheduledBase> scheduled_base;
            std::set<std::pair<int, int>> delivered;
            int delivered_by_basin[2] = {0, 0};
            int radio = 0;
            int waste = 0;
            int deliveries = 0;
            int scans = 0;
            int transitions = 0;
            int decisions = 0;
            std::uint64_t digest = 1469598103934665603ULL;

            for (int current_slot = slot; current_slot < kHorizon; ++current_slot) {
                std::array<int, kMaxAgents> success{};
                std::vector<ScheduledUplink> uplink_acks;
                std::vector<ScheduledUplink> future_uplinks;
                for (const auto& scheduled : scheduled_uplinks) {
                    if (scheduled.due != current_slot) {
                        future_uplinks.push_back(scheduled);
                        continue;
                    }
                    for (const int receiver : scheduled.decoded) {
                        if (current_slot < scheduled.report.time + kReportLifetime) {
                            append_fifo(fifo[receiver], scheduled.report, 4);
                            success[receiver] = 1;
                            success[scheduled.sender] = 1;
                        }
                    }
                    uplink_acks.push_back(scheduled);
                }
                scheduled_uplinks = std::move(future_uplinks);
                std::vector<ScheduledBase> base_acks;
                std::vector<ScheduledBase> future_base;
                for (const auto& scheduled : scheduled_base) {
                    if (scheduled.due != current_slot) {
                        future_base.push_back(scheduled);
                        continue;
                    }
                    const auto key = std::make_pair(scheduled.report.basin, scheduled.report.ordinal);
                    if (current_slot < scheduled.report.time + kReportLifetime &&
                        delivered.insert(key).second) {
                        ++delivered_by_basin[scheduled.report.basin];
                        ++deliveries;
                        success[scheduled.sender] = 1;
                    }
                    base_acks.push_back(scheduled);
                }
                scheduled_base = std::move(future_base);
                for (const auto& acknowledged : uplink_acks) {
                    if (!fifo[acknowledged.sender].empty()) {
                        fifo[acknowledged.sender].erase(fifo[acknowledged.sender].begin());
                    }
                    if (!success[acknowledged.sender]) {
                        ++waste;
                    }
                    for (const int listener : acknowledged.listeners) {
                        if (!success[listener]) {
                            ++waste;
                        }
                    }
                }
                for (const auto& acknowledged : base_acks) {
                    if (!fifo[acknowledged.sender].empty()) {
                        fifo[acknowledged.sender].erase(fifo[acknowledged.sender].begin());
                    }
                    if (!success[acknowledged.sender]) {
                        ++waste;
                    }
                }
                for (int agent = 0; agent < n; ++agent) {
                    auto& queue = fifo[agent];
                    std::vector<Report> retained;
                    retained.reserve(queue.size());
                    for (const auto& report : queue) {
                        if (current_slot < report.time + kReportLifetime) {
                            retained.push_back(report);
                        }
                    }
                    queue = std::move(retained);
                    previous_success[agent] = success[agent];
                }

                for (int agent = 0; agent < n; ++agent) {
                    if (current_slot == slot) {
                        actions[agent] = factual_data[lane * kMaxAgents + agent];
                        if (agent == focal) {
                            actions[agent] = forced;
                        }
                    } else {
                        const std::size_t tape_offset =
                            (lane * kHorizon + current_slot) * kMaxAgents + agent;
                        actions[agent] = policy_action(
                            lane_roles[agent],
                            current_slot,
                            static_cast<int>(fifo[agent].size()),
                            previous_action[agent],
                            previous_success[agent],
                            hidden.data() + agent * kHiddenDim,
                            action_data[tape_offset]);
                    }
                }
                decisions += n;
                for (int agent = 0; agent < n; ++agent) {
                    digest = digest_step(digest, (current_slot << 8) | actions[agent]);
                }

                for (int basin = 0; basin < 2; ++basin) {
                    std::vector<int> uplinks;
                    std::vector<int> nonempty;
                    std::vector<int> listeners;
                    for (int agent = 0; agent < n; ++agent) {
                        if (lane_roles[agent] == basin && actions[agent] == 1) {
                            uplinks.push_back(agent);
                            if (!fifo[agent].empty()) {
                                nonempty.push_back(agent);
                            }
                        }
                        if (lane_roles[agent] == 2 && actions[agent] == 2 + basin) {
                            listeners.push_back(agent);
                        }
                    }
                    radio += static_cast<int>(uplinks.size() + listeners.size());
                    waste += static_cast<int>(uplinks.size() - nonempty.size());
                    if (nonempty.size() >= 2) {
                        waste += static_cast<int>(nonempty.size() + listeners.size());
                    } else if (nonempty.size() == 1 && current_slot + 1 < kHorizon) {
                        const int sender = nonempty.front();
                        const Report report = fifo[sender].front();
                        const std::uint32_t threshold = static_cast<std::uint32_t>(4800 + 400 * basin);
                        std::vector<int> decoded;
                        for (const int receiver : listeners) {
                            const std::size_t tape_offset =
                                (lane * kHorizon + current_slot) * kMaxAgents + receiver;
                            if (uplink_data[tape_offset] < threshold) {
                                decoded.push_back(receiver);
                            }
                        }
                        if (!decoded.empty()) {
                            scheduled_uplinks.push_back(ScheduledUplink{
                                current_slot + 1, sender, report, listeners, decoded});
                        } else {
                            waste += static_cast<int>(nonempty.size() + listeners.size());
                        }
                    } else {
                        waste += static_cast<int>(nonempty.size() + listeners.size());
                    }
                }

                std::vector<int> forwards;
                std::vector<int> nonempty_forwards;
                for (int agent = 0; agent < n; ++agent) {
                    if (lane_roles[agent] == 2 && actions[agent] == 4) {
                        forwards.push_back(agent);
                        if (!fifo[agent].empty()) {
                            nonempty_forwards.push_back(agent);
                        }
                    }
                }
                radio += static_cast<int>(forwards.size());
                waste += static_cast<int>(forwards.size() - nonempty_forwards.size());
                if (nonempty_forwards.size() >= 2) {
                    waste += static_cast<int>(nonempty_forwards.size());
                } else if (nonempty_forwards.size() == 1 && current_slot + 1 < kHorizon) {
                    const int sender = nonempty_forwards.front();
                    const std::size_t tape_offset =
                        (lane * kHorizon + current_slot) * kMaxAgents + sender;
                    if (base_data[tape_offset] < 9000U) {
                        scheduled_base.push_back(
                            ScheduledBase{current_slot + 1, sender, fifo[sender].front()});
                    } else {
                        ++waste;
                    }
                } else {
                    waste += static_cast<int>(nonempty_forwards.size());
                }

                for (int basin = 0; basin < 2; ++basin) {
                    int ordinal = -1;
                    for (int candidate = 0; candidate < 3; ++candidate) {
                        if (events[basin][candidate] == current_slot) {
                            ordinal = candidate;
                            break;
                        }
                    }
                    if (ordinal < 0) {
                        continue;
                    }
                    for (int agent = 0; agent < n; ++agent) {
                        if (lane_roles[agent] == basin && actions[agent] == 0) {
                            ++scans;
                            const int local_index = agent % (n / 3);
                            const std::size_t detection_offset =
                                ((lane * kHorizon + current_slot) * 2 + basin) * 5 + local_index;
                            if (detection_data[detection_offset] < 7500U) {
                                append_fifo(
                                    fifo[agent], Report{basin, ordinal, current_slot}, 2);
                            }
                        }
                    }
                }

                for (int agent = 0; agent < n; ++agent) {
                    advance_hidden(
                        hidden.data() + agent * kHiddenDim,
                        current_slot,
                        lane_roles[agent],
                        actions[agent],
                        static_cast<int>(fifo[agent].size()),
                        previous_success[agent]);
                    previous_action[agent] = actions[agent];
                    previous_success[agent] = 0;
                }
                ++transitions;
            }

            if (!scheduled_uplinks.empty() || !scheduled_base.empty()) {
                throw std::runtime_error("fixture suffix left a post-horizon scheduled arrival");
            }
            for (const int metric : {radio, waste, deliveries, scans, transitions, decisions}) {
                digest = digest_step(digest, metric);
            }
            std::int64_t lane_hidden_sum = 0;
            for (int agent = 0; agent < n; ++agent) {
                for (int component = 0; component < kHiddenDim; ++component) {
                    lane_hidden_sum += python_round(hidden[agent * kHiddenDim + component] * 128.0);
                }
            }
            digest = digest_step(digest, lane_hidden_sum);
            std::int64_t return_micros =
                (650000LL * (delivered_by_basin[0] + delivered_by_basin[1])) / 6 +
                (250000LL * (delivered_by_basin[0] < delivered_by_basin[1]
                    ? delivered_by_basin[0]
                    : delivered_by_basin[1])) / 3;
            return_micros += radio == 0
                ? 100000LL
                : (100000LL * (radio - waste > 0 ? radio - waste : 0)) / radio;
            return_output[lane] = static_cast<double>(return_micros) / 1000000.0;
            digest_output[lane] = digest;
            transition_output[lane] = transitions;
            decision_output[lane] = decisions;
            delivery_output[lane] = deliveries;
            waste_output[lane] = waste;
            scan_output[lane] = scans;
            hidden_sum_output[lane] = lane_hidden_sum;
            forced_count_output[lane] = 1;
            teammate_count_output[lane] = n - 1;
        }
    }

    py::dict output;
    output["terminal_return"] = std::move(terminal_return);
    output["audit_digest"] = std::move(audit_digest);
    output["transition_count"] = std::move(transition_count);
    output["decision_count"] = std::move(decision_count);
    output["delivery_count"] = std::move(delivery_count);
    output["waste_count"] = std::move(waste_count);
    output["scan_count"] = std::move(scan_count);
    output["hidden_code_sum"] = std::move(hidden_code_sum);
    output["forced_action_count"] = std::move(forced_action_count);
    output["factual_teammate_count"] = std::move(factual_teammate_count);
    return output;
}

py::dict compiled_identity() {
    py::dict identity;
    identity["abi_tag"] = kAbiTag;
    identity["native_threads"] = kNativeThreads;
    identity["host_kind"] = "TEST_ONLY_DETERMINISTIC_FULL_SUFFIX";
    identity["language_standard"] = "C++17";
    return identity;
}

}  // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, module) {
    module.doc() = "TEST-only SGSP RSCF Gate A deterministic full-suffix host";
    module.def("compiled_identity", &compiled_identity);
    module.def(
        "run_suffix_batch",
        &run_suffix_batch,
        py::arg("n_agents"),
        py::arg("roles"),
        py::arg("origin_slot"),
        py::arg("focal_index"),
        py::arg("forced_action"),
        py::arg("factual_actions"),
        py::arg("initial_fifo_basin"),
        py::arg("initial_fifo_time"),
        py::arg("initial_previous_action"),
        py::arg("initial_previous_success"),
        py::arg("initial_hidden"),
        py::arg("event_times"),
        py::arg("action_tape"),
        py::arg("detection_tape"),
        py::arg("uplink_tape"),
        py::arg("base_tape"));
}
