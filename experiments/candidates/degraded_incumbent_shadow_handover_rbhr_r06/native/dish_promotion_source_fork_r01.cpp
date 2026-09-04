#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

#ifdef _WIN32
#define DISH_PSF_EXPORT extern "C" __declspec(dllexport)
#else
#define DISH_PSF_EXPORT extern "C"
#endif

namespace {

constexpr std::uint32_t kAbiVersion = 1;
constexpr std::int32_t kPostArrivalPreCas = 1;
constexpr std::int32_t kBranchObservationReadyPreForward = 2;
constexpr std::size_t kHiddenCopies = 4;
constexpr std::size_t kHiddenWidth = 128;
constexpr std::size_t kHiddenValues = kHiddenCopies * kHiddenWidth;
constexpr std::size_t kActorWidth = 54;
constexpr std::size_t kActorValues = kHiddenCopies * kActorWidth;
constexpr std::size_t kCriticWidth = 58;

struct DishPsfUavCausalFactsV1 {
  double position[2];
  double velocity[2];
  double held_action[2];
  double battery;
  std::int32_t camera_present;
  double camera_position[2];
  std::int32_t camera_missing;
  double filter_position[2];
  double filter_velocity[2];
  double filter_covariance[3];
  double radio_margin[3];
  std::int32_t source_present;
  double source_age;
  std::int32_t source_sequence;
  std::int32_t partner_present;
  double partner_age;
  double partner_position[2];
  double partner_velocity[2];
  double partner_action[2];
  double partner_battery;
  std::int32_t partner_camera_missing;
  std::int32_t partner_owner_bit;
  std::int32_t partner_d;
  std::int32_t partner_g1;
  std::int32_t partner_g5;
  std::int32_t local_d;
  std::int32_t local_g1;
  std::int32_t local_g5;
  std::int32_t prepare_latch;
  std::int32_t warmup_ticks;
  std::int32_t snapshot_present;
  double snapshot_age;
  std::int32_t snapshot_owner;
  std::int32_t snapshot_service_epoch;
  std::int32_t snapshot_next_payload_sequence;
  std::int32_t snapshot_k_epoch;
  std::int32_t snapshot_common_source_sequence;
  std::int32_t snapshot_record_version;
  std::int32_t readiness_present;
  double readiness_age;
  std::int32_t readiness_owner;
  std::int32_t readiness_service_epoch;
  std::int32_t readiness_next_payload_sequence;
  std::int32_t readiness_k_epoch;
  std::int32_t readiness_common_source_sequence;
  std::int32_t readiness_snapshot_version;
};

struct DishPsfCausalFactsV1 {
  DishPsfUavCausalFactsV1 uav[2];
  double base_position[2];
  double responder[4];
  std::int32_t k_active;
  std::int32_t countdown;
  std::int32_t renew;
  std::int32_t base_present;
  double base_age;
  double base_position_error;
  double base_first_margin;
  double base_second_margin;
  std::int32_t pending_switch;
  std::int32_t terminal;
};

struct DishPsfHostStateV1 {
  std::uint32_t abi_version;
  std::uint32_t struct_size;
  std::int32_t initialized;
  std::int32_t owner;
  std::int32_t application_tick;
  std::int32_t service_epoch;
  std::int32_t next_payload_sequence;
  std::int32_t k_epoch;
  std::int32_t intent_origin_tick;
  std::int32_t snapshot_version;
  std::int32_t readiness_version;
  std::int32_t lineage_lock[2];
  std::int32_t lineage_sequence[2];
  double controller_hidden[kHiddenValues];
  DishPsfCausalFactsV1 causal;
};

struct DishPsfPreparedTickV1 {
  std::uint32_t abi_version;
  std::uint32_t struct_size;
  std::int32_t phase;
  std::int32_t owner;
  std::int32_t application_tick;
  std::int32_t service_epoch;
  std::int32_t next_payload_sequence;
  std::int32_t k_epoch;
  std::int32_t intent_origin_tick;
  std::int32_t snapshot_version;
  std::int32_t readiness_version;
  std::int32_t snapshot_assimilation_requested;
  std::int32_t snapshot_recipient;
  std::int32_t lineage_lock[2];
  std::int32_t lineage_sequence[2];
  double controller_hidden[kHiddenValues];
  DishPsfCausalFactsV1 causal;
};

struct DishPsfRecurrentHandoffV1 {
  std::uint32_t abi_version;
  std::uint32_t struct_size;
  std::int32_t owner;
  std::int32_t service_epoch;
  std::int32_t next_payload_sequence;
  std::int32_t k_epoch;
  std::int32_t intent_origin_tick;
  std::int32_t snapshot_version;
  std::int32_t readiness_version;
  std::int32_t lineage_lock[2];
  std::int32_t lineage_sequence[2];
  double pre_bridge_hidden[kHiddenValues];
  double post_bridge_hidden[kHiddenValues];
};

struct DishPsfBranchStateV1 {
  std::int32_t owner;
  double hidden[kHiddenValues];
  double actor[kActorValues];
  double critic[kCriticWidth];
};

struct DishPsfForkOutputV1 {
  std::uint32_t abi_version;
  std::uint32_t struct_size;
  std::int32_t phase;
  std::int32_t forward_count;
  std::int32_t prepared_input_immutable;
  std::int32_t handoff_input_immutable;
  std::int32_t linearization_valid;
  DishPsfBranchStateV1 branches[3];
};

bool finite_recurrent(const double* values) {
  for (std::size_t index = 0; index < kHiddenValues; ++index) {
    if (!std::isfinite(values[index]) || values[index] < -1.0 || values[index] > 1.0) {
      return false;
    }
  }
  return true;
}

bool valid_parent(const DishPsfHostStateV1& parent) {
  return parent.abi_version == kAbiVersion &&
         parent.struct_size == sizeof(DishPsfHostStateV1) &&
         parent.initialized == 1 &&
         (parent.owner == 0 || parent.owner == 1) &&
         parent.application_tick > 0 &&
         parent.intent_origin_tick == parent.application_tick - 1 &&
         parent.service_epoch >= 0 &&
         parent.next_payload_sequence >= 0 &&
         parent.k_epoch >= 0 &&
         parent.snapshot_version >= 0 &&
         parent.readiness_version >= 0 &&
         parent.lineage_lock[0] == 1 && parent.lineage_lock[1] == 1 &&
         parent.lineage_sequence[0] >= 0 && parent.lineage_sequence[1] >= 0 &&
         finite_recurrent(parent.controller_hidden);
}

bool valid_prepared(const DishPsfPreparedTickV1& prepared) {
  return prepared.abi_version == kAbiVersion &&
         prepared.struct_size == sizeof(DishPsfPreparedTickV1) &&
         prepared.phase == kPostArrivalPreCas &&
         (prepared.owner == 0 || prepared.owner == 1) &&
         prepared.application_tick > 0 &&
         prepared.intent_origin_tick == prepared.application_tick - 1 &&
         prepared.service_epoch >= 0 &&
         prepared.next_payload_sequence >= 0 &&
         prepared.k_epoch >= 0 &&
         prepared.snapshot_version >= 0 &&
         prepared.readiness_version >= 0 &&
         prepared.snapshot_assimilation_requested == 1 &&
         prepared.snapshot_recipient == 1 - prepared.owner &&
         prepared.lineage_lock[0] == 1 && prepared.lineage_lock[1] == 1 &&
         prepared.lineage_sequence[0] >= 0 && prepared.lineage_sequence[1] >= 0 &&
         finite_recurrent(prepared.controller_hidden);
}

bool handoff_matches_linearization(const DishPsfPreparedTickV1& prepared,
                                   const DishPsfRecurrentHandoffV1& handoff) {
  return handoff.abi_version == kAbiVersion &&
         handoff.struct_size == sizeof(DishPsfRecurrentHandoffV1) &&
         handoff.owner == prepared.owner &&
         handoff.service_epoch == prepared.service_epoch &&
         handoff.next_payload_sequence == prepared.next_payload_sequence &&
         handoff.k_epoch == prepared.k_epoch &&
         handoff.intent_origin_tick == prepared.intent_origin_tick &&
         handoff.snapshot_version == prepared.snapshot_version &&
         handoff.readiness_version == prepared.readiness_version &&
         std::memcmp(handoff.lineage_lock, prepared.lineage_lock,
                     sizeof(handoff.lineage_lock)) == 0 &&
         std::memcmp(handoff.lineage_sequence, prepared.lineage_sequence,
                     sizeof(handoff.lineage_sequence)) == 0;
}

bool pre_bridge_matches_prepared(const DishPsfPreparedTickV1& prepared,
                                 const DishPsfRecurrentHandoffV1& handoff) {
  return std::memcmp(handoff.pre_bridge_hidden, prepared.controller_hidden,
                     sizeof(handoff.pre_bridge_hidden)) == 0;
}

bool bridge_change_matches_recipient(const DishPsfPreparedTickV1& prepared,
                                     const DishPsfRecurrentHandoffV1& handoff) {
  const std::int32_t permitted_copy =
      prepared.snapshot_assimilation_requested == 1 ? 2 * prepared.snapshot_recipient + 1 : -1;
  for (std::size_t copy = 0; copy < kHiddenCopies; ++copy) {
    if (static_cast<std::int32_t>(copy) == permitted_copy) {
      continue;
    }
    const double* pre = handoff.pre_bridge_hidden + copy * kHiddenWidth;
    const double* post = handoff.post_bridge_hidden + copy * kHiddenWidth;
    if (std::memcmp(pre, post, kHiddenWidth * sizeof(double)) != 0) {
      return false;
    }
  }
  return true;
}

void materialize_actor_row(double* row, const DishPsfPreparedTickV1& prepared,
                           const DishPsfBranchStateV1& branch, std::size_t copy) {
  const std::size_t physical = copy < 2 ? 0 : 1;
  const std::size_t copy_type = copy % 2;
  const DishPsfUavCausalFactsV1& self = prepared.causal.uav[physical];
  row[0] = copy_type == 0 ? 1.0 : 0.0;
  row[1] = copy_type == 1 ? 1.0 : 0.0;
  row[2] = static_cast<std::int32_t>(physical) == branch.owner ? 1.0 : 0.0;
  row[3] = 1.0;
  row[4] = self.position[0] - prepared.causal.base_position[0];
  row[5] = self.position[1] - prepared.causal.base_position[1];
  row[6] = self.velocity[0];
  row[7] = self.velocity[1];
  row[8] = self.held_action[0];
  row[9] = self.held_action[1];
  row[10] = self.battery;
  row[11] = static_cast<double>(self.camera_present);
  row[12] = self.camera_present ? self.camera_position[0] - self.position[0] : 0.0;
  row[13] = self.camera_present ? self.camera_position[1] - self.position[1] : 0.0;
  row[14] = static_cast<double>(self.camera_missing);
  row[15] = self.filter_position[0] - self.position[0];
  row[16] = self.filter_position[1] - self.position[1];
  row[17] = self.filter_velocity[0];
  row[18] = self.filter_velocity[1];
  row[19] = self.filter_covariance[0];
  row[20] = self.filter_covariance[1];
  row[21] = self.filter_covariance[2];
  row[22] = self.radio_margin[0];
  row[23] = self.radio_margin[1];
  row[24] = self.radio_margin[2];
  row[25] = static_cast<double>(self.source_present);
  row[26] = self.source_present ? self.source_age : 1.0e6;
  row[27] = static_cast<double>(self.partner_present);
  row[28] = self.partner_present ? self.partner_age : 1.0e6;
  if (self.partner_present) {
    row[29] = self.partner_position[0] - self.position[0];
    row[30] = self.partner_position[1] - self.position[1];
    row[31] = self.partner_velocity[0];
    row[32] = self.partner_velocity[1];
    row[33] = self.partner_action[0];
    row[34] = self.partner_action[1];
    row[35] = self.partner_battery;
    row[36] = static_cast<double>(self.partner_camera_missing);
    row[37] = static_cast<double>(self.partner_owner_bit);
  }
  row[38] = prepared.causal.k_active == 4 ? 1.0 : 0.0;
  row[39] = prepared.causal.k_active == 8 ? 1.0 : 0.0;
  row[40] = prepared.causal.k_active == 12 ? 1.0 : 0.0;
  row[41] = static_cast<double>(prepared.k_epoch);
  row[42] = static_cast<double>(prepared.causal.countdown);
  row[43] = static_cast<double>(prepared.causal.renew);
  if (static_cast<std::int32_t>(physical) == branch.owner) {
    row[44] = static_cast<double>(self.local_d);
    row[45] = static_cast<double>(self.local_g1);
    row[46] = static_cast<double>(self.local_g5);
  } else if (self.partner_present) {
    row[44] = static_cast<double>(self.partner_d);
    row[45] = static_cast<double>(self.partner_g1);
    row[46] = static_cast<double>(self.partner_g5);
  }
  row[47] = static_cast<double>(self.prepare_latch);
  row[48] = static_cast<double>(self.warmup_ticks > 20 ? 20 : self.warmup_ticks);
  row[49] = static_cast<double>(self.snapshot_present);
  row[50] = self.snapshot_present ? self.snapshot_age : 1.0e6;
  row[51] = static_cast<double>(self.readiness_present);
  row[52] = self.readiness_present ? self.readiness_age : 1.0e6;
  const std::int32_t post_epoch = prepared.service_epoch + 1;
  const std::int32_t named_common_sequence = self.snapshot_common_source_sequence;
  const bool source_lineage_current =
      prepared.causal.uav[0].source_present == 1 &&
      prepared.causal.uav[1].source_present == 1 &&
      prepared.causal.uav[0].source_sequence == named_common_sequence &&
      prepared.causal.uav[1].source_sequence == named_common_sequence &&
      prepared.lineage_sequence[0] == named_common_sequence &&
      prepared.lineage_sequence[1] == named_common_sequence;
  const bool snapshot_current = self.snapshot_present == 1 &&
                                self.snapshot_owner == branch.owner &&
                                self.snapshot_service_epoch == post_epoch &&
                                self.snapshot_k_epoch == prepared.k_epoch &&
                                source_lineage_current;
  const bool readiness_current = self.readiness_present == 1 &&
                                 self.readiness_owner == branch.owner &&
                                 self.readiness_service_epoch == post_epoch &&
                                 self.readiness_next_payload_sequence ==
                                     prepared.next_payload_sequence &&
                                 self.readiness_k_epoch == prepared.k_epoch &&
                                 self.readiness_common_source_sequence ==
                                     named_common_sequence &&
                                 self.readiness_snapshot_version == self.snapshot_record_version;
  row[53] = copy_type == 0 ? (snapshot_current && readiness_current ? 1.0 : 0.0)
                           : (snapshot_current ? 1.0 : 0.0);
}

void materialize_critic(double* row, const DishPsfPreparedTickV1& prepared,
                        const DishPsfBranchStateV1& branch) {
  std::memcpy(row, prepared.causal.responder, sizeof(prepared.causal.responder));
  for (std::size_t physical = 0; physical < 2; ++physical) {
    const DishPsfUavCausalFactsV1& self = prepared.causal.uav[physical];
    const std::size_t offset = 4 + 18 * physical;
    row[offset + 0] = self.position[0];
    row[offset + 1] = self.position[1];
    row[offset + 2] = self.velocity[0];
    row[offset + 3] = self.velocity[1];
    row[offset + 4] = self.held_action[0];
    row[offset + 5] = self.held_action[1];
    row[offset + 6] = self.battery;
    row[offset + 7] = static_cast<double>(self.camera_present);
    row[offset + 8] = self.camera_present ? self.camera_position[0] : 0.0;
    row[offset + 9] = self.camera_present ? self.camera_position[1] : 0.0;
    row[offset + 10] = static_cast<double>(self.camera_missing);
    row[offset + 11] = self.radio_margin[0];
    row[offset + 12] = self.radio_margin[1];
    row[offset + 13] = self.radio_margin[2];
    row[offset + 14] = static_cast<double>(self.source_present);
    row[offset + 15] = self.source_present ? self.source_age : 1.0e6;
    row[offset + 16] = self.source_present ? static_cast<double>(self.source_sequence) : 0.0;
    row[offset + 17] = static_cast<std::int32_t>(physical) == branch.owner ? 1.0 : 0.0;
  }
  row[40] = static_cast<double>(prepared.causal.base_present);
  row[41] = prepared.causal.base_present ? prepared.causal.base_age : 1.0e6;
  row[42] = prepared.causal.base_present ? prepared.causal.base_position_error : 1.0e6;
  row[43] = prepared.causal.base_present ? prepared.causal.base_first_margin : -1.0e6;
  row[44] = prepared.causal.base_present ? prepared.causal.base_second_margin : -1.0e6;
  row[45] = branch.owner == 0 ? 1.0 : 0.0;
  row[46] = branch.owner == 1 ? 1.0 : 0.0;
  row[47] = static_cast<double>(prepared.service_epoch + 1);
  row[48] = static_cast<double>(prepared.next_payload_sequence);
  row[49] = 1.0;
  row[50] = prepared.causal.k_active == 4 ? 1.0 : 0.0;
  row[51] = prepared.causal.k_active == 8 ? 1.0 : 0.0;
  row[52] = prepared.causal.k_active == 12 ? 1.0 : 0.0;
  row[53] = static_cast<double>(prepared.k_epoch);
  row[54] = static_cast<double>(prepared.causal.countdown);
  row[55] = static_cast<double>(prepared.causal.renew);
  row[56] = static_cast<double>(prepared.causal.pending_switch);
  row[57] = static_cast<double>(prepared.causal.terminal);
}

void materialize_observations(DishPsfBranchStateV1& branch,
                              const DishPsfPreparedTickV1& prepared) {
  std::memset(branch.actor, 0, sizeof(branch.actor));
  std::memset(branch.critic, 0, sizeof(branch.critic));
  for (std::size_t copy = 0; copy < kHiddenCopies; ++copy) {
    materialize_actor_row(branch.actor + copy * kActorWidth, prepared, branch, copy);
  }
  materialize_critic(branch.critic, prepared, branch);
}

void promote_transfer(DishPsfBranchStateV1& branch, std::int32_t old_owner,
                      bool use_shadow_source) {
  const std::int32_t new_owner = 1 - old_owner;
  const std::size_t old_incumbent = old_owner == 0 ? 0 : 2;
  const std::size_t old_shadow = old_owner == 0 ? 1 : 3;
  const std::size_t new_incumbent = new_owner == 0 ? 0 : 2;
  const std::size_t new_shadow = new_owner == 0 ? 1 : 3;
  const std::size_t promoted_source = use_shadow_source ? new_shadow : old_incumbent;

  std::memcpy(branch.hidden + new_incumbent * kHiddenWidth,
              branch.hidden + promoted_source * kHiddenWidth,
              kHiddenWidth * sizeof(double));
  std::memcpy(branch.hidden + old_shadow * kHiddenWidth,
              branch.hidden + old_incumbent * kHiddenWidth,
              kHiddenWidth * sizeof(double));
  branch.owner = new_owner;
}

}  // namespace

DISH_PSF_EXPORT std::uint32_t dish_psf_r01_abi_version() { return kAbiVersion; }
DISH_PSF_EXPORT std::size_t dish_psf_r01_host_state_v1_size() {
  return sizeof(DishPsfHostStateV1);
}
DISH_PSF_EXPORT std::size_t dish_psf_r01_prepared_tick_v1_size() {
  return sizeof(DishPsfPreparedTickV1);
}
DISH_PSF_EXPORT std::size_t dish_psf_r01_recurrent_handoff_v1_size() {
  return sizeof(DishPsfRecurrentHandoffV1);
}
DISH_PSF_EXPORT std::size_t dish_psf_r01_branch_state_v1_size() {
  return sizeof(DishPsfBranchStateV1);
}
DISH_PSF_EXPORT std::size_t dish_psf_r01_fork_output_v1_size() {
  return sizeof(DishPsfForkOutputV1);
}

DISH_PSF_EXPORT std::int32_t dish_psf_r01_test_two_owner_fixture(
    DishPsfHostStateV1* states, std::size_t count) {
  if (states == nullptr || count != 2) {
    return 1;
  }
  for (std::size_t lane = 0; lane < count; ++lane) {
    DishPsfHostStateV1 state{};
    state.abi_version = kAbiVersion;
    state.struct_size = sizeof(DishPsfHostStateV1);
    state.initialized = 1;
    state.owner = static_cast<std::int32_t>(lane);
    state.application_tick = 100;
    state.service_epoch = 7 + static_cast<std::int32_t>(lane);
    state.next_payload_sequence = 20 + static_cast<std::int32_t>(lane);
    state.k_epoch = 3;
    state.intent_origin_tick = 99;
    state.snapshot_version = 11 + static_cast<std::int32_t>(lane);
    state.readiness_version = 31 + static_cast<std::int32_t>(lane);
    state.lineage_lock[0] = 1;
    state.lineage_lock[1] = 1;
    const std::int32_t common_source_sequence = 60 + static_cast<std::int32_t>(lane);
    state.lineage_sequence[0] = common_source_sequence;
    state.lineage_sequence[1] = common_source_sequence;
    for (std::size_t index = 0; index < kHiddenValues; ++index) {
      state.controller_hidden[index] = -0.5 + static_cast<double>(index) / 2048.0;
    }
    state.causal.base_position[0] = 10.0;
    state.causal.base_position[1] = 20.0;
    state.causal.responder[0] = 1.0 + static_cast<double>(lane);
    state.causal.responder[1] = 2.0 + static_cast<double>(lane);
    state.causal.responder[2] = 0.1;
    state.causal.responder[3] = 0.2;
    state.causal.k_active = 8;
    state.causal.countdown = 3;
    state.causal.renew = 0;
    state.causal.base_present = lane == 0 ? 1 : 0;
    state.causal.base_age = lane == 0 ? 2.0 : 1.0e6;
    state.causal.base_position_error = lane == 0 ? 5.0 : 1.0e6;
    state.causal.base_first_margin = lane == 0 ? 7.0 : -1.0e6;
    state.causal.base_second_margin = lane == 0 ? 8.0 : -1.0e6;
    state.causal.pending_switch = 0;
    state.causal.terminal = 0;
    for (std::size_t physical = 0; physical < 2; ++physical) {
      DishPsfUavCausalFactsV1& facts = state.causal.uav[physical];
      const double lane_offset = 100.0 * static_cast<double>(lane);
      facts.position[0] = 20.0 + lane_offset + 10.0 * static_cast<double>(physical);
      facts.position[1] = 30.0 + lane_offset + 10.0 * static_cast<double>(physical);
      facts.velocity[0] = 1.0 + 0.1 * static_cast<double>(lane) + static_cast<double>(physical);
      facts.velocity[1] = 2.0 + 0.1 * static_cast<double>(lane) + static_cast<double>(physical);
      facts.held_action[0] = 0.1 + 0.1 * static_cast<double>(physical);
      facts.held_action[1] = 0.2 + 0.1 * static_cast<double>(physical);
      facts.battery = 80.0 - 5.0 * static_cast<double>(physical) - static_cast<double>(lane);
      facts.camera_present = physical == 0 ? 1 : 0;
      facts.camera_position[0] = facts.position[0] + 2.0;
      facts.camera_position[1] = facts.position[1] + 3.0;
      facts.camera_missing = facts.camera_present ? 0 : 1;
      facts.filter_position[0] = facts.position[0] + 0.5;
      facts.filter_position[1] = facts.position[1] + 0.75;
      facts.filter_velocity[0] = facts.velocity[0] + 0.1;
      facts.filter_velocity[1] = facts.velocity[1] + 0.1;
      facts.filter_covariance[0] = 0.25;
      facts.filter_covariance[1] = 0.05;
      facts.filter_covariance[2] = 0.4;
      facts.radio_margin[0] = 10.0 + static_cast<double>(physical);
      facts.radio_margin[1] = 11.0 + static_cast<double>(physical);
      facts.radio_margin[2] = 12.0 + static_cast<double>(physical);
      facts.source_present = 1;
      facts.source_age = 1.5 + 0.25 * static_cast<double>(physical);
      facts.source_sequence = common_source_sequence;
      facts.partner_present = physical == lane ? 1 : 0;
      facts.partner_age = facts.partner_present ? 0.1 : 1.0e6;
      if (facts.partner_present) {
        const std::size_t partner = 1 - physical;
        facts.partner_position[0] =
            20.0 + lane_offset + 10.0 * static_cast<double>(partner) + 7.0;
        facts.partner_position[1] =
            30.0 + lane_offset + 10.0 * static_cast<double>(partner) - 4.0;
        facts.partner_velocity[0] = 6.0 + static_cast<double>(physical);
        facts.partner_velocity[1] = 7.0 + static_cast<double>(physical);
        facts.partner_action[0] = 0.6;
        facts.partner_action[1] = 0.7;
        facts.partner_battery = 55.0;
        facts.partner_camera_missing = 1;
        facts.partner_owner_bit = 0;
        facts.partner_d = 1;
        facts.partner_g1 = 0;
        facts.partner_g5 = 1;
      }
      facts.local_d = physical == 0 ? 1 : 0;
      facts.local_g1 = 1;
      facts.local_g5 = physical == 0 ? 0 : 1;
      facts.prepare_latch = static_cast<std::int32_t>(physical);
      facts.warmup_ticks = 4 + static_cast<std::int32_t>(physical);
      const bool current_owner_record = physical == lane;
      const bool lane0_potential_owner_snapshot = lane == 0 && physical == 1;
      facts.snapshot_present = current_owner_record || lane0_potential_owner_snapshot ? 1 : 0;
      facts.snapshot_age = 1.0 + static_cast<double>(physical);
      facts.snapshot_owner = static_cast<std::int32_t>(physical);
      facts.snapshot_service_epoch = state.service_epoch + 1;
      facts.snapshot_next_payload_sequence = state.next_payload_sequence - 1;
      facts.snapshot_k_epoch = state.k_epoch;
      facts.snapshot_common_source_sequence = common_source_sequence;
      facts.snapshot_record_version = 100 + 10 * static_cast<std::int32_t>(lane) +
                                      static_cast<std::int32_t>(physical);
      facts.readiness_present = current_owner_record ? 1 : 0;
      facts.readiness_age = 2.0 + static_cast<double>(physical);
      facts.readiness_owner = static_cast<std::int32_t>(physical);
      facts.readiness_service_epoch = state.service_epoch + 1;
      facts.readiness_next_payload_sequence = state.next_payload_sequence;
      facts.readiness_k_epoch = state.k_epoch;
      facts.readiness_common_source_sequence = common_source_sequence;
      facts.readiness_snapshot_version = facts.snapshot_record_version;
    }
    states[lane] = state;
  }
  return 0;
}

DISH_PSF_EXPORT std::int32_t dish_psf_r01_begin_tick_batch(
    const DishPsfHostStateV1* parent, std::size_t count, DishPsfPreparedTickV1* out) {
  if (parent == nullptr || out == nullptr || count == 0) {
    return 1;
  }
  for (std::size_t lane = 0; lane < count; ++lane) {
    if (!valid_parent(parent[lane])) {
      return 2;
    }
  }
  for (std::size_t lane = 0; lane < count; ++lane) {
    const DishPsfHostStateV1 before = parent[lane];
    DishPsfPreparedTickV1 prepared{};
    prepared.abi_version = kAbiVersion;
    prepared.struct_size = sizeof(DishPsfPreparedTickV1);
    prepared.phase = kPostArrivalPreCas;
    prepared.owner = parent[lane].owner;
    prepared.application_tick = parent[lane].application_tick;
    prepared.service_epoch = parent[lane].service_epoch;
    prepared.next_payload_sequence = parent[lane].next_payload_sequence;
    prepared.k_epoch = parent[lane].k_epoch;
    prepared.intent_origin_tick = parent[lane].intent_origin_tick;
    prepared.snapshot_version = parent[lane].snapshot_version;
    prepared.readiness_version = parent[lane].readiness_version;
    prepared.snapshot_assimilation_requested = 1;
    prepared.snapshot_recipient = 1 - parent[lane].owner;
    std::memcpy(prepared.lineage_lock, parent[lane].lineage_lock,
                sizeof(prepared.lineage_lock));
    std::memcpy(prepared.lineage_sequence, parent[lane].lineage_sequence,
                sizeof(prepared.lineage_sequence));
    std::memcpy(prepared.controller_hidden, parent[lane].controller_hidden,
                sizeof(prepared.controller_hidden));
    prepared.causal = parent[lane].causal;
    if (std::memcmp(&before, &parent[lane], sizeof(before)) != 0) {
      return 3;
    }
    out[lane] = prepared;
  }
  return 0;
}

DISH_PSF_EXPORT std::int32_t dish_psf_r01_clone_prepared_batch(
    const DishPsfPreparedTickV1* prepared,
    const DishPsfRecurrentHandoffV1* post_arrival_assimilated,
    std::size_t count, DishPsfForkOutputV1* out) {
  if (prepared == nullptr || post_arrival_assimilated == nullptr || out == nullptr || count == 0) {
    return 1;
  }
  for (std::size_t lane = 0; lane < count; ++lane) {
    if (!valid_prepared(prepared[lane]) ||
        !handoff_matches_linearization(prepared[lane], post_arrival_assimilated[lane])) {
      return 2;
    }
    if (!finite_recurrent(post_arrival_assimilated[lane].pre_bridge_hidden) ||
        !finite_recurrent(post_arrival_assimilated[lane].post_bridge_hidden)) {
      return 3;
    }
    if (!pre_bridge_matches_prepared(prepared[lane], post_arrival_assimilated[lane])) {
      return 2;
    }
    if (!bridge_change_matches_recipient(prepared[lane], post_arrival_assimilated[lane])) {
      return 4;
    }
  }

  for (std::size_t lane = 0; lane < count; ++lane) {
    const DishPsfPreparedTickV1 prepared_before = prepared[lane];
    const DishPsfRecurrentHandoffV1 handoff_before = post_arrival_assimilated[lane];
    DishPsfForkOutputV1 fork{};
    fork.abi_version = kAbiVersion;
    fork.struct_size = sizeof(DishPsfForkOutputV1);
    fork.phase = kBranchObservationReadyPreForward;
    fork.forward_count = 0;
    fork.linearization_valid = 1;

    for (std::size_t branch_index = 0; branch_index < 3; ++branch_index) {
      fork.branches[branch_index].owner = prepared[lane].owner;
      std::memcpy(fork.branches[branch_index].hidden,
                  post_arrival_assimilated[lane].post_bridge_hidden,
                  sizeof(fork.branches[branch_index].hidden));
    }
    promote_transfer(fork.branches[1], prepared[lane].owner, false);
    promote_transfer(fork.branches[2], prepared[lane].owner, true);
    for (DishPsfBranchStateV1& branch : fork.branches) {
      materialize_observations(branch, prepared[lane]);
    }

    fork.prepared_input_immutable =
        std::memcmp(&prepared_before, &prepared[lane], sizeof(prepared_before)) == 0 ? 1 : 0;
    fork.handoff_input_immutable =
        std::memcmp(&handoff_before, &post_arrival_assimilated[lane], sizeof(handoff_before)) == 0
            ? 1
            : 0;
    if (fork.prepared_input_immutable != 1 || fork.handoff_input_immutable != 1) {
      return 4;
    }
    out[lane] = fork;
  }
  return 0;
}
