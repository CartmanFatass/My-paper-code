import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


PROCESS_OUTCOME_FIELDS = (
    "delta_coverage_ratio",
    "delta_effective_connected_users",
    "delta_system_throughput_mbps",
    "delta_qos_satisfaction",
    "delta_backhaul_margin",
    "delta_energy_ratio",
    "delta_distance_to_nearest_charger",
    "charging_progress",
    "return_pressure_change",
    "fallback_obs_delta_l2",
    "fallback_obs_delta_mean_abs",
    "fallback_reward_return",
)


class MaskedRunningMeanStd:
    """Per-dimension running normalizer that updates only available fields."""

    def __init__(self, shape, eps=1e-8):
        self.shape = tuple(shape) if isinstance(shape, (tuple, list)) else (int(shape),)
        self.eps = float(eps)
        self.mean = np.zeros(self.shape, dtype=np.float64)
        self.var = np.ones(self.shape, dtype=np.float64)
        self.count = np.zeros(self.shape, dtype=np.float64)
        self._m2 = np.zeros(self.shape, dtype=np.float64)

    def update(self, values, mask):
        values = np.asarray(values, dtype=np.float64).reshape(self.shape)
        mask = np.asarray(mask, dtype=np.bool_).reshape(self.shape)
        finite_mask = mask & np.isfinite(values)
        for idx in np.ndindex(self.shape):
            if not finite_mask[idx]:
                continue
            value = values[idx]
            old_count = self.count[idx]
            new_count = old_count + 1.0
            delta = value - self.mean[idx]
            self.mean[idx] += delta / new_count
            delta2 = value - self.mean[idx]
            self._m2[idx] += delta * delta2
            self.count[idx] = new_count
            self.var[idx] = self._m2[idx] / max(new_count - 1.0, 1.0)

    def normalize(self, values, mask):
        values = np.asarray(values, dtype=np.float32).reshape(self.shape)
        mask = np.asarray(mask, dtype=np.bool_).reshape(self.shape)
        normalized = np.zeros(self.shape, dtype=np.float32)
        std = np.sqrt(np.maximum(self.var, self.eps)).astype(np.float32)
        normalized[mask] = (values[mask] - self.mean.astype(np.float32)[mask]) / std[mask]
        return normalized


class SkillProcessOutcomeExtractor:
    """Extracts masked process outcome vectors from closed skill segments."""

    FIELD_NAMES = PROCESS_OUTCOME_FIELDS

    def __init__(self, normalize=True):
        self.normalize_enabled = bool(normalize)
        self.normalizer = MaskedRunningMeanStd(len(self.FIELD_NAMES))

    @property
    def num_outcomes(self):
        return len(self.FIELD_NAMES)

    @staticmethod
    def _numeric_scalar(value):
        if value is None:
            return None
        try:
            arr = np.asarray(value, dtype=np.float64)
        except (TypeError, ValueError):
            return None
        if arr.size == 0:
            return None
        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            return None
        return float(np.mean(finite))

    def _metric_series(self, segment, aliases):
        values = []
        for info in segment.get("reward_info_seq", []):
            if not isinstance(info, dict):
                continue
            for key in aliases:
                if key in info:
                    scalar = self._numeric_scalar(info.get(key))
                    if scalar is not None:
                        values.append(scalar)
                    break
        return values

    def _delta(self, segment, aliases, sign=1.0):
        values = self._metric_series(segment, aliases)
        if len(values) < 2:
            return 0.0, False
        return float(sign) * float(values[-1] - values[0]), True

    def _mean(self, segment, aliases, sign=1.0):
        values = self._metric_series(segment, aliases)
        if not values:
            return 0.0, False
        return float(sign) * float(np.mean(values)), True

    def extract_raw(self, segment):
        vector = np.zeros(self.num_outcomes, dtype=np.float32)
        mask = np.zeros(self.num_outcomes, dtype=np.bool_)
        field_to_idx = {name: idx for idx, name in enumerate(self.FIELD_NAMES)}

        def set_field(name, result):
            value, available = result
            idx = field_to_idx[name]
            if available and np.isfinite(value):
                vector[idx] = float(value)
                mask[idx] = True

        set_field("delta_coverage_ratio", self._delta(segment, ("coverage_ratio",)))
        set_field(
            "delta_effective_connected_users",
            self._delta(segment, ("effective_connected_users", "connected_users")),
        )
        set_field(
            "delta_system_throughput_mbps",
            self._delta(
                segment,
                (
                    "system_throughput_mbps",
                    "effective_end_to_end_throughput_mbps",
                    "capacity_limited_throughput_mbps",
                ),
            ),
        )
        set_field(
            "delta_qos_satisfaction",
            self._delta(
                segment,
                ("qos_satisfaction_ratio", "qos_met_fraction", "demand_satisfaction_ratio"),
            ),
        )
        backhaul_delta = self._delta(segment, ("min_serving_backhaul_bottleneck_mbps", "backhaul_margin"))
        if not backhaul_delta[1]:
            backhaul_delta = self._delta(segment, ("backhaul_margin_penalty_raw",), sign=-1.0)
        set_field("delta_backhaul_margin", backhaul_delta)

        energy_delta = self._delta(segment, ("battery_min_ratio", "battery_mean_ratio"))
        if not energy_delta[1]:
            energy_delta = self._delta(segment, ("normalized_propulsion_energy",), sign=-1.0)
        set_field("delta_energy_ratio", energy_delta)
        set_field(
            "delta_distance_to_nearest_charger",
            self._delta(segment, ("distance_to_nearest_charger", "nearest_charger_distance")),
        )

        charging_progress = self._delta(segment, ("episode_energy_charged_wh", "energy_charged_wh"))
        if not charging_progress[1]:
            charging_progress = self._mean(segment, ("charging_uav_count", "effective_charging_session_count"))
        set_field("charging_progress", charging_progress)

        return_pressure = self._delta(segment, ("return_constraint_cost",), sign=-1.0)
        if not return_pressure[1]:
            return_pressure = self._delta(segment, ("return_risk_penalty",), sign=-1.0)
        set_field("return_pressure_change", return_pressure)

        obs_seq = segment.get("obs_seq", [])
        next_obs_seq = segment.get("next_obs_seq", [])
        if obs_seq and next_obs_seq and len(obs_seq) == len(next_obs_seq):
            deltas = [
                np.asarray(next_obs, dtype=np.float32) - np.asarray(obs, dtype=np.float32)
                for obs, next_obs in zip(obs_seq, next_obs_seq)
            ]
            if deltas:
                stacked = np.stack([delta.reshape(-1) for delta in deltas], axis=0)
                set_field("fallback_obs_delta_l2", (float(np.mean(np.linalg.norm(stacked, axis=1))), True))
                set_field("fallback_obs_delta_mean_abs", (float(np.mean(np.abs(stacked))), True))

        reward_seq = segment.get("reward_seq", [])
        if reward_seq:
            reward_arr = np.asarray(reward_seq, dtype=np.float32)
            set_field("fallback_reward_return", (float(np.sum(reward_arr)), True))

        return vector, mask

    def transform_segment(self, segment, update=True):
        vector, mask = self.extract_raw(segment)
        if self.normalize_enabled and update:
            self.normalizer.update(vector, mask)
        normalized = (
            self.normalizer.normalize(vector, mask)
            if self.normalize_enabled
            else vector.copy()
        )
        return {
            "outcome_vector": vector,
            "outcome_mask": mask,
            "outcome_normalized": normalized,
            "outcome_field_names": self.FIELD_NAMES,
        }


class SkillProcessEncoder(nn.Module):
    """Masked sequence encoder for executed skill-lifetime segments."""

    def __init__(self, obs_dim, action_dim, hidden_dim=64, embedding_dim=64):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        self.embedding_dim = int(embedding_dim)
        input_dim = self.obs_dim * 2 + self.action_dim + 1
        self.step_encoder = nn.Sequential(
            nn.Linear(input_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.embedding_dim),
            nn.ReLU(),
        )
        self.output_layer = nn.Sequential(
            nn.Linear(self.embedding_dim, self.embedding_dim),
            nn.LayerNorm(self.embedding_dim),
        )

    def forward(self, obs_seq, action_seq, next_obs_seq=None, reward_seq=None, mask_seq=None):
        if next_obs_seq is None:
            next_obs_seq = obs_seq
        if action_seq.dim() == 2:
            action_seq = action_seq.unsqueeze(-1)
        if reward_seq is None:
            reward_seq = torch.zeros(
                obs_seq.shape[0],
                obs_seq.shape[1],
                1,
                dtype=obs_seq.dtype,
                device=obs_seq.device,
            )
        elif reward_seq.dim() == 2:
            reward_seq = reward_seq.unsqueeze(-1)
        if mask_seq is None:
            mask_seq = torch.ones(
                obs_seq.shape[0],
                obs_seq.shape[1],
                dtype=obs_seq.dtype,
                device=obs_seq.device,
            )
        mask = mask_seq.to(dtype=obs_seq.dtype).unsqueeze(-1)
        delta_obs = next_obs_seq - obs_seq
        features = torch.cat([obs_seq, action_seq, delta_obs, reward_seq], dim=-1)
        step_emb = self.step_encoder(features)
        pooled = (step_emb * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
        return self.output_layer(pooled)


class SkillOutcomePredictor(nn.Module):
    """Predicts masked process outcome vectors from segment embeddings."""

    def __init__(self, segment_dim, outcome_dim):
        super().__init__()
        self.head = nn.Linear(int(segment_dim), int(outcome_dim))

    def forward(self, segment_embedding):
        return self.head(segment_embedding)

    @staticmethod
    def masked_mse_loss(predicted, target, mask):
        mask = mask.to(dtype=predicted.dtype)
        squared = (predicted - target).pow(2) * mask
        return squared.sum() / mask.sum().clamp_min(1.0)


class SkillProcessContrastiveHead(nn.Module):
    """InfoNCE-style alignment between segment embeddings and executed skills."""

    def __init__(self, segment_dim, num_skills, embedding_dim=None, temperature=0.1):
        super().__init__()
        self.segment_dim = int(segment_dim)
        self.num_skills = int(num_skills)
        self.embedding_dim = int(embedding_dim or segment_dim)
        self.temperature = float(temperature)
        self.segment_proj = nn.Linear(self.segment_dim, self.embedding_dim)
        self.skill_embedding = nn.Embedding(self.num_skills, self.embedding_dim)

    def logits(self, segment_embedding):
        segment_z = F.normalize(self.segment_proj(segment_embedding), dim=-1)
        skill_z = F.normalize(self.skill_embedding.weight, dim=-1)
        return segment_z @ skill_z.t() / max(self.temperature, 1e-6)

    def forward(self, segment_embedding, executed_skill_labels):
        labels = executed_skill_labels.to(dtype=torch.long, device=segment_embedding.device)
        logits = self.logits(segment_embedding)
        loss = F.cross_entropy(logits, labels)
        accuracy = (logits.argmax(dim=-1) == labels).float().mean()
        return {
            "logits": logits,
            "loss": loss,
            "accuracy": accuracy,
        }


def process_positive_skill_labels(segments):
    """Return executed active skill labels; candidate/no-edit fields are ignored."""
    labels = []
    for segment in segments:
        labels.append(int(segment["skill"]))
    return np.asarray(labels, dtype=np.int64)


def duration_only_baseline_accuracy(duration_targets, skill_labels):
    """Majority-vote skill accuracy using only duration buckets."""
    durations = np.asarray(duration_targets).reshape(-1)
    skills = np.asarray(skill_labels).reshape(-1)
    valid = np.isfinite(durations) & np.isfinite(skills)
    durations = durations[valid].astype(np.int64)
    skills = skills[valid].astype(np.int64)
    if durations.size == 0:
        return 0.0
    correct = 0
    for duration in np.unique(durations):
        bucket_skills = skills[durations == duration]
        values, counts = np.unique(bucket_skills, return_counts=True)
        majority = values[np.argmax(counts)]
        correct += int(np.sum(bucket_skills == majority))
    return float(correct) / float(durations.size)
