#include <algorithm>
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <string>
#include <utility>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace {

using FloatArray = py::array_t<float, py::array::c_style>;
using DoubleArray = py::array_t<double, py::array::c_style>;
using BoolArray = py::array_t<bool, py::array::c_style>;

void require_rank(const py::buffer_info& info, int rank, const char* name) {
    if (info.ndim != rank) {
        throw std::invalid_argument(
            std::string(name) + " must have rank " + std::to_string(rank));
    }
}

py::tuple observe_six_batch(
    const FloatArray& capabilities,
    const FloatArray& priorities,
    const FloatArray& loads,
    const FloatArray& target_mixes,
    const BoolArray& active_mask,
    const FloatArray& log_counts,
    float time_fraction) {
    const py::buffer_info capability_info = capabilities.request();
    const py::buffer_info priority_info = priorities.request();
    const py::buffer_info load_info = loads.request();
    const py::buffer_info mix_info = target_mixes.request();
    const py::buffer_info active_info = active_mask.request();
    const py::buffer_info log_info = log_counts.request();
    require_rank(capability_info, 3, "capabilities");
    require_rank(priority_info, 2, "priorities");
    require_rank(load_info, 1, "loads");
    require_rank(mix_info, 1, "target_mixes");
    require_rank(active_info, 2, "active_mask");
    require_rank(log_info, 1, "log_counts");

    const py::ssize_t batch = capability_info.shape[0];
    const py::ssize_t capacity = capability_info.shape[1];
    if (batch <= 0 || capacity <= 0 || capability_info.shape[2] != 2 ||
        priority_info.shape[0] != batch || priority_info.shape[1] != capacity ||
        active_info.shape[0] != batch || active_info.shape[1] != capacity ||
        load_info.shape[0] != batch || mix_info.shape[0] != batch ||
        log_info.shape[0] != batch || !std::isfinite(time_fraction)) {
        throw std::invalid_argument("toy observation batch dimensions are invalid");
    }

    FloatArray observations({batch, capacity, py::ssize_t{6}});
    FloatArray critic_states({batch, py::ssize_t{6}});
    const auto* capability_data =
        static_cast<const float*>(capability_info.ptr);
    const auto* priority_data = static_cast<const float*>(priority_info.ptr);
    const auto* load_data = static_cast<const float*>(load_info.ptr);
    const auto* mix_data = static_cast<const float*>(mix_info.ptr);
    const auto* active_data = static_cast<const bool*>(active_info.ptr);
    const auto* log_data = static_cast<const float*>(log_info.ptr);
    auto* observation_data =
        static_cast<float*>(observations.request().ptr);
    auto* critic_data = static_cast<float*>(critic_states.request().ptr);
    std::fill(
        observation_data,
        observation_data + static_cast<std::size_t>(batch * capacity * 6),
        0.0F);

    {
        py::gil_scoped_release release;
        for (py::ssize_t batch_index = 0; batch_index < batch; ++batch_index) {
            float aggregate_first = 0.0F;
            float aggregate_second = 0.0F;
            py::ssize_t active_count = 0;
            const float load = load_data[batch_index];
            const float target_mix = mix_data[batch_index];
            const float log_count = log_data[batch_index];
            if (!std::isfinite(load) || !std::isfinite(target_mix) ||
                !std::isfinite(log_count)) {
                throw std::invalid_argument(
                    "toy observation inputs must contain only finite values");
            }
            for (py::ssize_t member = 0; member < capacity; ++member) {
                if (!active_data[batch_index * capacity + member]) {
                    continue;
                }
                ++active_count;
                const std::size_t capability_offset = static_cast<std::size_t>(
                    (batch_index * capacity + member) * 2);
                const std::size_t observation_offset = static_cast<std::size_t>(
                    (batch_index * capacity + member) * 6);
                const float first = capability_data[capability_offset];
                const float second = capability_data[capability_offset + 1];
                const float priority =
                    priority_data[batch_index * capacity + member];
                if (!std::isfinite(first) || !std::isfinite(second) ||
                    !std::isfinite(priority)) {
                    throw std::invalid_argument(
                        "toy observation inputs must contain only finite values");
                }
                observation_data[observation_offset] = first;
                observation_data[observation_offset + 1] = second;
                observation_data[observation_offset + 2] = priority;
                observation_data[observation_offset + 3] = load;
                observation_data[observation_offset + 4] = target_mix;
                observation_data[observation_offset + 5] = log_count;
                aggregate_first += first;
                aggregate_second += second;
            }
            if (active_count <= 0) {
                throw std::invalid_argument("toy observation batch has an empty roster");
            }
            const std::size_t critic_offset =
                static_cast<std::size_t>(batch_index * 6);
            critic_data[critic_offset] = load;
            critic_data[critic_offset + 1] = target_mix;
            critic_data[critic_offset + 2] = aggregate_first;
            critic_data[critic_offset + 3] = aggregate_second;
            critic_data[critic_offset + 4] = log_count;
            critic_data[critic_offset + 5] = time_fraction;
        }
    }
    return py::make_tuple(std::move(observations), std::move(critic_states));
}

DoubleArray reward_batch(
    const FloatArray& capabilities,
    const BoolArray& active_mask,
    const FloatArray& actions,
    const FloatArray& loads,
    const FloatArray& target_mixes) {
    const py::buffer_info capability_info = capabilities.request();
    const py::buffer_info active_info = active_mask.request();
    const py::buffer_info action_info = actions.request();
    const py::buffer_info load_info = loads.request();
    const py::buffer_info mix_info = target_mixes.request();
    require_rank(capability_info, 3, "capabilities");
    require_rank(active_info, 2, "active_mask");
    require_rank(action_info, 3, "actions");
    require_rank(load_info, 1, "loads");
    require_rank(mix_info, 1, "target_mixes");

    const py::ssize_t batch = capability_info.shape[0];
    const py::ssize_t capacity = capability_info.shape[1];
    if (batch <= 0 || capacity <= 0 || capability_info.shape[2] != 2 ||
        active_info.shape[0] != batch || active_info.shape[1] != capacity ||
        action_info.shape[0] != batch || action_info.shape[1] != capacity ||
        action_info.shape[2] != 2 || load_info.shape[0] != batch ||
        mix_info.shape[0] != batch) {
        throw std::invalid_argument("toy reward batch dimensions are invalid");
    }

    DoubleArray rewards({batch});
    const auto* capability_data =
        static_cast<const float*>(capability_info.ptr);
    const auto* active_data = static_cast<const bool*>(active_info.ptr);
    const auto* action_data = static_cast<const float*>(action_info.ptr);
    const auto* load_data = static_cast<const float*>(load_info.ptr);
    const auto* mix_data = static_cast<const float*>(mix_info.ptr);
    auto* reward_data = static_cast<double*>(rewards.request().ptr);

    {
        py::gil_scoped_release release;
        for (py::ssize_t batch_index = 0; batch_index < batch; ++batch_index) {
            double served_first = 0.0;
            double served_second = 0.0;
            double aggregate_first = 0.0;
            double aggregate_second = 0.0;
            py::ssize_t active_count = 0;
            for (py::ssize_t member = 0; member < capacity; ++member) {
                const std::size_t offset = static_cast<std::size_t>(
                    (batch_index * capacity + member) * 2);
                const float first_action = action_data[offset];
                const float second_action = action_data[offset + 1];
                if (!std::isfinite(first_action) ||
                    !std::isfinite(second_action) ||
                    std::abs(first_action) > 1.0F ||
                    std::abs(second_action) > 1.0F) {
                    throw std::invalid_argument(
                        "toy actions must be finite and within support");
                }
                if (!active_data[batch_index * capacity + member]) {
                    if (first_action != 0.0F || second_action != 0.0F) {
                        throw std::invalid_argument(
                            "toy inactive actions must be exactly zero");
                    }
                    continue;
                }
                ++active_count;
                const float first_capability = capability_data[offset];
                const float second_capability = capability_data[offset + 1];
                if (!std::isfinite(first_capability) ||
                    !std::isfinite(second_capability)) {
                    throw std::invalid_argument(
                        "toy capabilities must contain only finite values");
                }
                const float effort = (first_action + 1.0F) / 2.0F;
                const float action_mix = (second_action + 1.0F) / 2.0F;
                const float first_service =
                    (effort * action_mix) * first_capability;
                const float second_service =
                    (effort * (1.0F - action_mix)) * second_capability;
                served_first += static_cast<double>(first_service);
                served_second += static_cast<double>(second_service);
                aggregate_first += static_cast<double>(first_capability);
                aggregate_second += static_cast<double>(second_capability);
            }
            if (active_count <= 0) {
                throw std::invalid_argument("toy reward batch has an empty roster");
            }
            const double load = static_cast<double>(load_data[batch_index]);
            const double target_mix =
                static_cast<double>(mix_data[batch_index]);
            if (!std::isfinite(load) || !std::isfinite(target_mix)) {
                throw std::invalid_argument(
                    "toy reward inputs must contain only finite values");
            }
            const double target_first =
                load * target_mix * aggregate_first;
            const double target_second =
                load * (1.0 - target_mix) * aggregate_second;
            const double first_error =
                std::abs(served_first - target_first) /
                std::max(target_first, 1.0e-8);
            const double second_error =
                std::abs(served_second - target_second) /
                std::max(target_second, 1.0e-8);
            reward_data[batch_index] = std::min(
                1.0, std::max(0.0, 1.0 - (first_error + second_error) / 2.0));
        }
    }
    return rewards;
}

}  // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, module) {
    module.doc() = "HMASD deterministic continuous-roster toy backend";
    module.def(
        "observe_six_batch",
        &observe_six_batch,
        py::arg("capabilities"),
        py::arg("priorities"),
        py::arg("loads"),
        py::arg("target_mixes"),
        py::arg("active_mask"),
        py::arg("log_counts"),
        py::arg("time_fraction"));
    module.def(
        "reward_batch",
        &reward_batch,
        py::arg("capabilities"),
        py::arg("active_mask"),
        py::arg("actions"),
        py::arg("loads"),
        py::arg("target_mixes"));
}
