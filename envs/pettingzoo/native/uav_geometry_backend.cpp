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

using DoubleArray = py::array_t<double, py::array::c_style>;
using FloatArray = py::array_t<float, py::array::c_style>;
using BoolArray = py::array_t<bool, py::array::c_style>;

void require_rank(const py::buffer_info& info, int rank, const char* name) {
    if (info.ndim != rank) {
        throw std::invalid_argument(
            std::string(name) + " must have rank " + std::to_string(rank));
    }
}

double clamp_double(double value, double lower, double upper) {
    return std::min(upper, std::max(lower, value));
}

double air_to_ground_path_loss(
    const double* airborne,
    const double* ground,
    double frequency_term,
    double los_a,
    double los_b,
    double eta_los,
    double eta_nlos) {
    const double dx = airborne[0] - ground[0];
    const double dy = airborne[1] - ground[1];
    const double dz = airborne[2] - ground[2];
    const double distance_2d = std::sqrt(dx * dx + dy * dy);
    const double distance_3d = std::sqrt(dx * dx + dy * dy + dz * dz);
    const double safe_distance_2d = std::max(distance_2d, 1.0e-6);
    const double safe_distance_3d = std::max(distance_3d, 1.0e-6);
    constexpr double radians_to_degrees =
        180.0 / 3.141592653589793238462643383279502884;
    const double elevation_angle =
        std::atan(std::abs(dz) / safe_distance_2d) * radians_to_degrees;
    double p_los =
        1.0 / (1.0 + los_a * std::exp(-los_b * (elevation_angle - los_a)));
    p_los = clamp_double(p_los, 0.0, 1.0);

    const double fspl =
        20.0 * std::log10(safe_distance_3d) + frequency_term - 147.55;
    const double pl_los_linear = std::pow(10.0, -(fspl + eta_los) / 10.0);
    const double pl_nlos_linear = std::pow(10.0, -(fspl + eta_nlos) / 10.0);
    const double average_linear =
        p_los * pl_los_linear + (1.0 - p_los) * pl_nlos_linear;
    return -10.0 * std::log10(average_linear);
}

double air_to_air_path_loss(
    const double* first,
    const double* second,
    double frequency_term) {
    const double dx = first[0] - second[0];
    const double dy = first[1] - second[1];
    const double dz = first[2] - second[2];
    const double distance = std::sqrt(dx * dx + dy * dy + dz * dz);
    return 20.0 * std::log10(std::max(distance, 1.0e-6)) + frequency_term -
        147.55;
}

py::tuple step_geometry_batch(
    const DoubleArray& uav_positions,
    const DoubleArray& user_positions,
    const DoubleArray& ground_bs_positions,
    const FloatArray& prepared_velocities,
    const BoolArray& movable_mask,
    double time_step,
    double area_size,
    double minimum_height,
    double maximum_height,
    double carrier_frequency,
    double los_a,
    double los_b,
    double eta_los,
    double eta_nlos) {
    const py::buffer_info uav_info = uav_positions.request();
    const py::buffer_info user_info = user_positions.request();
    const py::buffer_info bs_info = ground_bs_positions.request();
    const py::buffer_info velocity_info = prepared_velocities.request();
    const py::buffer_info mask_info = movable_mask.request();
    require_rank(uav_info, 3, "uav_positions");
    require_rank(user_info, 3, "user_positions");
    require_rank(bs_info, 3, "ground_bs_positions");
    require_rank(velocity_info, 3, "prepared_velocities");
    require_rank(mask_info, 2, "movable_mask");

    const py::ssize_t batch = uav_info.shape[0];
    const py::ssize_t uavs = uav_info.shape[1];
    const py::ssize_t users = user_info.shape[1];
    const py::ssize_t bases = bs_info.shape[1];
    if (uav_info.shape[2] != 3 || user_info.shape[2] != 3 ||
        bs_info.shape[2] != 3 || velocity_info.shape[2] != 3) {
        throw std::invalid_argument(
            "all position/velocity trailing dimensions must be 3");
    }
    if (user_info.shape[0] != batch || bs_info.shape[0] != batch ||
        velocity_info.shape[0] != batch || velocity_info.shape[1] != uavs ||
        mask_info.shape[0] != batch || mask_info.shape[1] != uavs) {
        throw std::invalid_argument("batch or UAV dimensions do not match");
    }
    if (!(time_step > 0.0) || !(area_size > 0.0) ||
        !(carrier_frequency > 0.0) || minimum_height > maximum_height) {
        throw std::invalid_argument("invalid geometry configuration");
    }

    DoubleArray next_uav_positions({batch, uavs, py::ssize_t{3}});
    DoubleArray access_path_loss({batch, uavs, users});
    DoubleArray air_path_loss({batch, uavs, uavs});
    DoubleArray base_path_loss({batch, uavs, bases});

    const auto* uav_data = static_cast<const double*>(uav_info.ptr);
    const auto* user_data = static_cast<const double*>(user_info.ptr);
    const auto* bs_data = static_cast<const double*>(bs_info.ptr);
    const auto* velocity_data = static_cast<const float*>(velocity_info.ptr);
    const auto* mask_data = static_cast<const bool*>(mask_info.ptr);
    auto* next_data = static_cast<double*>(next_uav_positions.request().ptr);
    auto* access_data = static_cast<double*>(access_path_loss.request().ptr);
    auto* air_data = static_cast<double*>(air_path_loss.request().ptr);
    auto* base_data = static_cast<double*>(base_path_loss.request().ptr);

    const float time_step_f32 = static_cast<float>(time_step);
    const double frequency_term = 20.0 * std::log10(carrier_frequency);

    {
        py::gil_scoped_release release;
        for (py::ssize_t batch_index = 0; batch_index < batch; ++batch_index) {
            for (py::ssize_t uav_index = 0; uav_index < uavs; ++uav_index) {
                const std::size_t vector_offset = static_cast<std::size_t>(
                    (batch_index * uavs + uav_index) * 3);
                for (py::ssize_t coordinate = 0; coordinate < 3; ++coordinate) {
                    double value = uav_data[vector_offset + coordinate];
                    if (mask_data[batch_index * uavs + uav_index]) {
                        const float delta =
                            velocity_data[vector_offset + coordinate] *
                            time_step_f32;
                        value += static_cast<double>(delta);
                    }
                    if (coordinate < 2) {
                        value = clamp_double(value, 0.0, area_size);
                    } else {
                        value = clamp_double(
                            value, minimum_height, maximum_height);
                    }
                    next_data[vector_offset + coordinate] = value;
                }
            }

            for (py::ssize_t uav_index = 0; uav_index < uavs; ++uav_index) {
                const double* airborne = next_data + static_cast<std::size_t>(
                    (batch_index * uavs + uav_index) * 3);
                for (py::ssize_t user_index = 0; user_index < users;
                     ++user_index) {
                    const double* user = user_data + static_cast<std::size_t>(
                        (batch_index * users + user_index) * 3);
                    access_data[
                        (batch_index * uavs + uav_index) * users + user_index] =
                        air_to_ground_path_loss(
                            airborne,
                            user,
                            frequency_term,
                            los_a,
                            los_b,
                            eta_los,
                            eta_nlos);
                }
                for (py::ssize_t peer_index = 0; peer_index < uavs;
                     ++peer_index) {
                    const double* peer = next_data + static_cast<std::size_t>(
                        (batch_index * uavs + peer_index) * 3);
                    air_data[
                        (batch_index * uavs + uav_index) * uavs + peer_index] =
                        air_to_air_path_loss(
                            airborne, peer, frequency_term);
                }
                for (py::ssize_t base_index = 0; base_index < bases;
                     ++base_index) {
                    const double* base = bs_data + static_cast<std::size_t>(
                        (batch_index * bases + base_index) * 3);
                    base_data[
                        (batch_index * uavs + uav_index) * bases + base_index] =
                        air_to_ground_path_loss(
                            airborne,
                            base,
                            frequency_term,
                            los_a,
                            los_b,
                            eta_los,
                            eta_nlos);
                }
            }
        }
    }

    return py::make_tuple(
        std::move(next_uav_positions),
        std::move(access_path_loss),
        std::move(air_path_loss),
        std::move(base_path_loss));
}

}  // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, module) {
    module.doc() = "HMASD deterministic batched UAV geometry backend";
    module.def(
        "step_geometry_batch",
        &step_geometry_batch,
        py::arg("uav_positions"),
        py::arg("user_positions"),
        py::arg("ground_bs_positions"),
        py::arg("prepared_velocities"),
        py::arg("movable_mask"),
        py::arg("time_step"),
        py::arg("area_size"),
        py::arg("minimum_height"),
        py::arg("maximum_height"),
        py::arg("carrier_frequency"),
        py::arg("los_a"),
        py::arg("los_b"),
        py::arg("eta_los"),
        py::arg("eta_nlos"));
}
