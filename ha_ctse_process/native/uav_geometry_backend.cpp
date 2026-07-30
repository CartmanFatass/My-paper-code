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

void require_rank(const py::buffer_info& info, int rank, const char* name) {
    if (info.ndim != rank) {
        throw std::invalid_argument(
            std::string(name) + " must have rank " + std::to_string(rank));
    }
}

double clamp_double(double value, double lower, double upper) {
    return std::min(upper, std::max(lower, value));
}

// Bitwise identical to `_compute_distance` (scenario_base.py:3836): doubles
// throughout, LEFT-TO-RIGHT association `(dx*dx + dy*dy) + dz*dz`. Do not
// reorder -- the source's own docstring measures 6761/60008 mismatches under
// re-association, and this is the gate every interference sum below depends
// on.
double distance3(const double* a, const double* b) {
    const double dx = a[0] - b[0];
    const double dy = a[1] - b[1];
    const double dz = a[2] - b[2];
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

// PROVEN oracle functions, byte-for-byte unchanged: max_ulp 0 against
// `_compute_air_to_ground_path_loss` / `_compute_air_to_air_path_loss` over
// the full matrix (tests/uav_cpp_backend_oracle_test.py). Do not touch.
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

// Bitwise identical to `10 * np.log10(noise_power_linear_mw + total)` with
// `total` accumulated left-to-right (see the interference loops below).
double interference_plus_noise_dbm(double noise_power_linear_mw, double total) {
    return 10.0 * std::log10(noise_power_linear_mw + total);
}

// Bitwise identical to `_get_spectral_efficiency_from_sinr`
// (scenario_base.py:1433): first-match ascending scan, last entry as the
// catch-all (the Python table's last threshold is +inf, so this loop only
// ever falls through to the post-loop default for a non-finite sinr_db).
double spectral_efficiency_from_sinr(
    double sinr_db,
    const double* thresholds,
    const double* efficiencies,
    py::ssize_t table_size) {
    for (py::ssize_t index = 0; index < table_size; ++index) {
        if (sinr_db < thresholds[index]) {
            return efficiencies[index];
        }
    }
    return efficiencies[table_size - 1];
}

py::tuple step_communication_batch(
    const DoubleArray& uav_positions,
    const DoubleArray& user_positions,
    const DoubleArray& ground_bs_positions,
    double carrier_frequency,
    double los_a,
    double los_b,
    double eta_los,
    double eta_nlos,
    double tx_power,
    double ground_bs_tx_power,
    double noise_power_linear_mw,
    double interference_radius,
    bool use_fdma,
    double aclr_linear,
    double bandwidth,
    double min_sinr,
    const DoubleArray& mcs_thresholds,
    const DoubleArray& mcs_efficiencies) {
    const py::buffer_info uav_info = uav_positions.request();
    const py::buffer_info user_info = user_positions.request();
    const py::buffer_info bs_info = ground_bs_positions.request();
    const py::buffer_info threshold_info = mcs_thresholds.request();
    const py::buffer_info efficiency_info = mcs_efficiencies.request();
    require_rank(uav_info, 3, "uav_positions");
    require_rank(user_info, 3, "user_positions");
    require_rank(bs_info, 3, "ground_bs_positions");
    require_rank(threshold_info, 1, "mcs_thresholds");
    require_rank(efficiency_info, 1, "mcs_efficiencies");

    const py::ssize_t batch = uav_info.shape[0];
    const py::ssize_t uavs = uav_info.shape[1];
    const py::ssize_t users = user_info.shape[1];
    const py::ssize_t bases = bs_info.shape[1];
    const py::ssize_t table_size = threshold_info.shape[0];
    if (uav_info.shape[2] != 3 || user_info.shape[2] != 3 ||
        bs_info.shape[2] != 3) {
        throw std::invalid_argument(
            "all position trailing dimensions must be 3");
    }
    if (user_info.shape[0] != batch || bs_info.shape[0] != batch) {
        throw std::invalid_argument("batch dimensions do not match");
    }
    if (table_size < 1 || efficiency_info.shape[0] != table_size) {
        throw std::invalid_argument(
            "mcs_thresholds and mcs_efficiencies must share one non-empty length");
    }
    if (!(carrier_frequency > 0.0)) {
        throw std::invalid_argument("invalid communication configuration");
    }

    DoubleArray access_path_loss({batch, uavs, users});
    DoubleArray air_path_loss({batch, uavs, uavs});
    DoubleArray base_path_loss({batch, uavs, bases});
    DoubleArray user_ipn_dbm({batch, uavs, users});
    DoubleArray uav_uav_ipn_dbm({batch, uavs, uavs});
    DoubleArray uav_bs_ipn_dbm({batch, uavs, bases});
    DoubleArray bs_uav_ipn_dbm({batch, uavs});
    DoubleArray cap_uav_uav({batch, uavs, uavs});
    DoubleArray cap_uav_bs({batch, uavs, bases});
    DoubleArray cap_bs_uav({batch, uavs, bases});

    const auto* uav_data = static_cast<const double*>(uav_info.ptr);
    const auto* user_data = static_cast<const double*>(user_info.ptr);
    const auto* bs_data = static_cast<const double*>(bs_info.ptr);
    const auto* threshold_data = static_cast<const double*>(threshold_info.ptr);
    const auto* efficiency_data = static_cast<const double*>(efficiency_info.ptr);

    auto* access_data = static_cast<double*>(access_path_loss.request().ptr);
    auto* air_data = static_cast<double*>(air_path_loss.request().ptr);
    auto* base_data = static_cast<double*>(base_path_loss.request().ptr);
    auto* user_ipn_data = static_cast<double*>(user_ipn_dbm.request().ptr);
    auto* uav_uav_ipn_data = static_cast<double*>(uav_uav_ipn_dbm.request().ptr);
    auto* uav_bs_ipn_data = static_cast<double*>(uav_bs_ipn_dbm.request().ptr);
    auto* bs_uav_ipn_data = static_cast<double*>(bs_uav_ipn_dbm.request().ptr);
    auto* cap_uav_uav_data = static_cast<double*>(cap_uav_uav.request().ptr);
    auto* cap_uav_bs_data = static_cast<double*>(cap_uav_bs.request().ptr);
    auto* cap_bs_uav_data = static_cast<double*>(cap_bs_uav.request().ptr);

    const double frequency_term = 20.0 * std::log10(carrier_frequency);
    // Bitwise identical to `self.bandwidth / self.n_uavs` -- the Python
    // capacity function uses this divisor for EVERY link type (uav-uav,
    // uav-bs, bs-uav), never just the two endpoints of the link in question.
    const double bandwidth_term =
        use_fdma ? bandwidth / static_cast<double>(uavs) : bandwidth;

    {
        py::gil_scoped_release release;
        for (py::ssize_t b = 0; b < batch; ++b) {
            const double* uav_batch = uav_data + static_cast<std::size_t>(b * uavs * 3);
            const double* user_batch = user_data + static_cast<std::size_t>(b * users * 3);
            const double* bs_batch = bs_data + static_cast<std::size_t>(b * bases * 3);

            double* access_batch = access_data + static_cast<std::size_t>(b * uavs * users);
            double* air_batch = air_data + static_cast<std::size_t>(b * uavs * uavs);
            double* base_batch = base_data + static_cast<std::size_t>(b * uavs * bases);
            double* user_ipn_batch = user_ipn_data + static_cast<std::size_t>(b * uavs * users);
            double* uav_uav_ipn_batch = uav_uav_ipn_data + static_cast<std::size_t>(b * uavs * uavs);
            double* uav_bs_ipn_batch = uav_bs_ipn_data + static_cast<std::size_t>(b * uavs * bases);
            double* bs_uav_ipn_batch = bs_uav_ipn_data + static_cast<std::size_t>(b * uavs);
            double* cap_uav_uav_batch = cap_uav_uav_data + static_cast<std::size_t>(b * uavs * uavs);
            double* cap_uav_bs_batch = cap_uav_bs_data + static_cast<std::size_t>(b * uavs * bases);
            double* cap_bs_uav_batch = cap_bs_uav_data + static_cast<std::size_t>(b * uavs * bases);

            // 1: access_path_loss[i, j] = A2G(uav_i, user_j)
            for (py::ssize_t i = 0; i < uavs; ++i) {
                const double* uav_i = uav_batch + static_cast<std::size_t>(i * 3);
                for (py::ssize_t j = 0; j < users; ++j) {
                    const double* user_j = user_batch + static_cast<std::size_t>(j * 3);
                    access_batch[i * users + j] = air_to_ground_path_loss(
                        uav_i, user_j, frequency_term, los_a, los_b, eta_los, eta_nlos);
                }
            }

            // 2: air_path_loss[i, k] = A2A(uav_i, uav_k), including the
            // diagonal (distance clamps to 1e-6 there, as today).
            for (py::ssize_t i = 0; i < uavs; ++i) {
                const double* uav_i = uav_batch + static_cast<std::size_t>(i * 3);
                for (py::ssize_t k = 0; k < uavs; ++k) {
                    const double* uav_k = uav_batch + static_cast<std::size_t>(k * 3);
                    air_batch[i * uavs + k] = air_to_air_path_loss(uav_i, uav_k, frequency_term);
                }
            }

            // 3: base_path_loss[i, g] = A2G(uav_i, bs_g)
            for (py::ssize_t i = 0; i < uavs; ++i) {
                const double* uav_i = uav_batch + static_cast<std::size_t>(i * 3);
                for (py::ssize_t g = 0; g < bases; ++g) {
                    const double* bs_g = bs_batch + static_cast<std::size_t>(g * 3);
                    base_batch[i * bases + g] = air_to_ground_path_loss(
                        uav_i, bs_g, frequency_term, los_a, los_b, eta_los, eta_nlos);
                }
            }

            // 4: user_ipn_dbm[i, j] -- replicates `_compute_uav_to_user_sinr`
            // (scenario_base.py:5300) op for op: interferers k != i, ascending,
            // gated on distance(uav_k, user_j), summed LEFT-TO-RIGHT.
            for (py::ssize_t i = 0; i < uavs; ++i) {
                for (py::ssize_t j = 0; j < users; ++j) {
                    const double* user_j = user_batch + static_cast<std::size_t>(j * 3);
                    double total = 0.0;
                    for (py::ssize_t k = 0; k < uavs; ++k) {
                        if (k == i) {
                            continue;
                        }
                        const double* uav_k = uav_batch + static_cast<std::size_t>(k * 3);
                        if (distance3(uav_k, user_j) > interference_radius) {
                            continue;
                        }
                        const double pl = access_batch[k * users + j];
                        double p = std::pow(10.0, (tx_power - pl) / 10.0);
                        p *= 1.0;  // the deterministic MAC-layer weight
                        if (use_fdma) {
                            p *= aclr_linear;
                        }
                        total += p;
                    }
                    user_ipn_batch[i * users + j] =
                        interference_plus_noise_dbm(noise_power_linear_mw, total);
                }
            }

            // 5: uav_uav_ipn_dbm[s, r] -- replicates `_compute_link_sinr`
            // (scenario_base.py:4638) with tx_type=rx_type="uav": interferers
            // k != s and k != r, gated on distance(uav_k, uav_r). The
            // diagonal (s == r) reduces to the single exclusion k != s and is
            // computed here but never consumed downstream.
            for (py::ssize_t s = 0; s < uavs; ++s) {
                for (py::ssize_t r = 0; r < uavs; ++r) {
                    const double* uav_r = uav_batch + static_cast<std::size_t>(r * 3);
                    double total = 0.0;
                    for (py::ssize_t k = 0; k < uavs; ++k) {
                        if (k == s || k == r) {
                            continue;
                        }
                        const double* uav_k = uav_batch + static_cast<std::size_t>(k * 3);
                        if (distance3(uav_k, uav_r) > interference_radius) {
                            continue;
                        }
                        const double pl = air_batch[k * uavs + r];
                        double p = std::pow(10.0, (tx_power - pl) / 10.0);
                        p *= 1.0;
                        if (use_fdma) {
                            p *= aclr_linear;
                        }
                        total += p;
                    }
                    uav_uav_ipn_batch[s * uavs + r] =
                        interference_plus_noise_dbm(noise_power_linear_mw, total);
                }
            }

            // 6: uav_bs_ipn_dbm[i, g] -- link (tx=uav_i, rx=bs_g): interferers
            // k != i (rx is not a uav, so no rx exclusion), gated on
            // distance(uav_k, bs_g), path loss is A2G of the interferer to
            // the bs (base_path_loss[k, g]).
            for (py::ssize_t i = 0; i < uavs; ++i) {
                for (py::ssize_t g = 0; g < bases; ++g) {
                    const double* bs_g = bs_batch + static_cast<std::size_t>(g * 3);
                    double total = 0.0;
                    for (py::ssize_t k = 0; k < uavs; ++k) {
                        if (k == i) {
                            continue;
                        }
                        const double* uav_k = uav_batch + static_cast<std::size_t>(k * 3);
                        if (distance3(uav_k, bs_g) > interference_radius) {
                            continue;
                        }
                        const double pl = base_batch[k * bases + g];
                        double p = std::pow(10.0, (tx_power - pl) / 10.0);
                        p *= 1.0;
                        if (use_fdma) {
                            p *= aclr_linear;
                        }
                        total += p;
                    }
                    uav_bs_ipn_batch[i * bases + g] =
                        interference_plus_noise_dbm(noise_power_linear_mw, total);
                }
            }

            // 7: bs_uav_ipn_dbm[r] -- link (tx=bs_g, rx=uav_r). Independent of
            // g: the source exclusion is only k != r, and both the distance
            // gate and the interferer path loss (A2A = air_path_loss[k, r])
            // are relative to uav_r alone, never to any bs position. Hence
            // one value per r, not one per (r, g).
            for (py::ssize_t r = 0; r < uavs; ++r) {
                const double* uav_r = uav_batch + static_cast<std::size_t>(r * 3);
                double total = 0.0;
                for (py::ssize_t k = 0; k < uavs; ++k) {
                    if (k == r) {
                        continue;
                    }
                    const double* uav_k = uav_batch + static_cast<std::size_t>(k * 3);
                    if (distance3(uav_k, uav_r) > interference_radius) {
                        continue;
                    }
                    const double pl = air_batch[k * uavs + r];
                    double p = std::pow(10.0, (tx_power - pl) / 10.0);
                    p *= 1.0;
                    if (use_fdma) {
                        p *= aclr_linear;
                    }
                    total += p;
                }
                bs_uav_ipn_batch[r] =
                    interference_plus_noise_dbm(noise_power_linear_mw, total);
            }

            // 8: cap_uav_uav[s, r] -- replicates `_get_link_capacity`
            // (scenario_base.py:4440). Diagonal never consumed.
            for (py::ssize_t s = 0; s < uavs; ++s) {
                for (py::ssize_t r = 0; r < uavs; ++r) {
                    const double sinr_db =
                        (tx_power - air_batch[s * uavs + r]) - uav_uav_ipn_batch[s * uavs + r];
                    if (sinr_db < min_sinr) {
                        cap_uav_uav_batch[s * uavs + r] = 0.0;
                    } else {
                        const double se = spectral_efficiency_from_sinr(
                            sinr_db, threshold_data, efficiency_data, table_size);
                        cap_uav_uav_batch[s * uavs + r] = se * bandwidth_term;
                    }
                }
            }

            // 9: cap_uav_bs[i, g]
            for (py::ssize_t i = 0; i < uavs; ++i) {
                for (py::ssize_t g = 0; g < bases; ++g) {
                    const double sinr_db =
                        (tx_power - base_batch[i * bases + g]) - uav_bs_ipn_batch[i * bases + g];
                    if (sinr_db < min_sinr) {
                        cap_uav_bs_batch[i * bases + g] = 0.0;
                    } else {
                        const double se = spectral_efficiency_from_sinr(
                            sinr_db, threshold_data, efficiency_data, table_size);
                        cap_uav_bs_batch[i * bases + g] = se * bandwidth_term;
                    }
                }
            }

            // 10: cap_bs_uav[r, g] -- indexed [r, g] because the Python cache
            // key order is ("ground_bs", g, "uav", r): node1 (bs, g) is the
            // transmitter, node2 (uav, r) is the receiver, and this backend
            // stores the result by receiver-then-transmitter to match how the
            // wiring reads it back.
            for (py::ssize_t r = 0; r < uavs; ++r) {
                for (py::ssize_t g = 0; g < bases; ++g) {
                    const double sinr_db =
                        (ground_bs_tx_power - base_batch[r * bases + g]) - bs_uav_ipn_batch[r];
                    if (sinr_db < min_sinr) {
                        cap_bs_uav_batch[r * bases + g] = 0.0;
                    } else {
                        const double se = spectral_efficiency_from_sinr(
                            sinr_db, threshold_data, efficiency_data, table_size);
                        cap_bs_uav_batch[r * bases + g] = se * bandwidth_term;
                    }
                }
            }
        }
    }

    return py::make_tuple(
        std::move(access_path_loss),
        std::move(air_path_loss),
        std::move(base_path_loss),
        std::move(user_ipn_dbm),
        std::move(uav_uav_ipn_dbm),
        std::move(uav_bs_ipn_dbm),
        std::move(bs_uav_ipn_dbm),
        std::move(cap_uav_uav),
        std::move(cap_uav_bs),
        std::move(cap_bs_uav));
}

}  // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, module) {
    module.doc() = "HMASD deterministic batched UAV communication backend";
    module.def(
        "step_communication_batch",
        &step_communication_batch,
        py::arg("uav_positions"),
        py::arg("user_positions"),
        py::arg("ground_bs_positions"),
        py::arg("carrier_frequency"),
        py::arg("los_a"),
        py::arg("los_b"),
        py::arg("eta_los"),
        py::arg("eta_nlos"),
        py::arg("tx_power"),
        py::arg("ground_bs_tx_power"),
        py::arg("noise_power_linear_mw"),
        py::arg("interference_radius"),
        py::arg("use_fdma"),
        py::arg("aclr_linear"),
        py::arg("bandwidth"),
        py::arg("min_sinr"),
        py::arg("mcs_thresholds"),
        py::arg("mcs_efficiencies"));
}
