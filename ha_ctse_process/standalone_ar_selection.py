"""Autoregressive roster-selection helpers for the standalone process agent."""

from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F

from ha_ctse_process.standalone_segments import Segment


class StandaloneARSelectionMixin:
    def _ar_prefix_dim(self) -> int:
        return int(getattr(self.high, "ar_prefix_dim", 0))

    def _empty_ar_prefix(self) -> torch.Tensor:
        return torch.zeros(1, self._ar_prefix_dim(), dtype=torch.float32, device=self.device)

    def _updated_ar_prefix(self, prefix: torch.Tensor, skill: int) -> torch.Tensor:
        updated = prefix.clone()
        if 0 <= int(skill) < int(self.n_skills):
            updated[0, int(skill)] += 1.0 / float(max(self.n_agents, 1))
        return updated

    def _roster_age_scale(self) -> float:
        max_candidate = max(int(value) for value in self.duration_candidates) if self.duration_candidates else 1
        return float(max(max_candidate, 1))

    def _build_roster_ar_prefix(
        self,
        agent_id: int,
        active_skills,
        skill_ages,
        active_mask,
        processed_new_skills=None,
    ) -> torch.Tensor:
        dim = self._ar_prefix_dim()
        prefix = torch.zeros(1, dim, dtype=torch.float32, device=self.device)
        if dim <= 0:
            return prefix
        active_skills_t = torch.as_tensor(active_skills, dtype=torch.long, device=self.device).reshape(-1)
        skill_ages_t = torch.as_tensor(skill_ages, dtype=torch.float32, device=self.device).reshape(-1)
        active_mask_t = torch.as_tensor(active_mask, dtype=torch.bool, device=self.device).reshape(-1)
        n_agents = min(int(self.n_agents), int(active_skills_t.numel()), int(skill_ages_t.numel()), int(active_mask_t.numel()))
        scale = 1.0 / float(max(self.n_agents, 1))
        age_scale = self._roster_age_scale()
        identity_offset = int(self.n_skills)
        age_offset = identity_offset + int(self.n_agents) * int(self.n_skills)
        for other_id in range(n_agents):
            if int(other_id) == int(agent_id) or not bool(active_mask_t[other_id].item()):
                continue
            skill = int(active_skills_t[other_id].item())
            if skill < 0 or skill >= int(self.n_skills):
                continue
            prefix[0, skill] += scale
            if identity_offset + other_id * self.n_skills + skill < dim:
                prefix[0, identity_offset + other_id * self.n_skills + skill] = scale
            if age_offset + other_id * self.n_skills + skill < dim:
                age_norm = float(torch.clamp(skill_ages_t[other_id], min=0.0).item()) / age_scale
                prefix[0, age_offset + other_id * self.n_skills + skill] = scale * min(age_norm, 1.0)
        for skill in processed_new_skills or []:
            skill = int(skill)
            if 0 <= skill < int(self.n_skills):
                prefix[0, skill] += scale
        return prefix

    def _build_shuffled_roster_ar_prefix(
        self,
        agent_id: int,
        active_skills,
        skill_ages,
        active_mask,
        processed_new_skills=None,
    ) -> torch.Tensor:
        skills = np.asarray(active_skills, dtype=np.int64).reshape(-1).copy()
        mask = np.asarray(active_mask, dtype=np.bool_).reshape(-1).copy()
        ages = np.asarray(skill_ages, dtype=np.float32).reshape(-1).copy()
        n = min(skills.size, mask.size, ages.size, int(self.n_agents))
        candidate = [idx for idx in range(n) if idx != int(agent_id) and bool(mask[idx])]
        if len(candidate) > 1:
            original_skills = skills[candidate].copy()
            original_ages = ages[candidate].copy()
            skills[candidate] = np.roll(original_skills, 1)
            ages[candidate] = np.roll(original_ages, 1)
        return self._build_roster_ar_prefix(
            agent_id=agent_id,
            active_skills=skills,
            skill_ages=ages,
            active_mask=mask,
            processed_new_skills=processed_new_skills,
        )

    def _segment_ar_prefix_tensor(self, segments: list[Segment]) -> torch.Tensor | None:
        ar_prefix_dim = self._ar_prefix_dim()
        if ar_prefix_dim <= 0:
            return None
        ar_prefix_np = np.zeros((len(segments), ar_prefix_dim), dtype=np.float32)
        for idx, segment in enumerate(segments):
            if segment.ar_prefix_start is None:
                if (
                    self.ar_prefix_mode == "roster"
                    and segment.roster_active_skills_start is not None
                    and segment.roster_active_ages_start is not None
                    and segment.roster_active_mask_start is not None
                ):
                    rebuilt = self._build_roster_ar_prefix(
                        agent_id=int(segment.agent_id),
                        active_skills=segment.roster_active_skills_start,
                        skill_ages=segment.roster_active_ages_start,
                        active_mask=segment.roster_active_mask_start,
                    )
                    prefix = rebuilt.detach().cpu().numpy().reshape(-1)
                    ar_prefix_np[idx, : min(ar_prefix_dim, prefix.size)] = prefix[: min(ar_prefix_dim, prefix.size)]
                continue
            else:
                prefix = np.asarray(segment.ar_prefix_start, dtype=np.float32).reshape(-1)
                ar_prefix_np[idx, : min(ar_prefix_dim, prefix.size)] = prefix[: min(ar_prefix_dim, prefix.size)]
                continue
        return torch.as_tensor(ar_prefix_np, dtype=torch.float32, device=self.device)

    def _roster_selection_metrics(self, segments: list[Segment]) -> dict[str, float]:
        selected: list[int] = []
        same_flags: list[float] = []
        active_counts: list[int] = []
        roster_skill_counts = np.zeros(int(self.n_skills), dtype=np.float64)
        for segment in segments:
            if segment.roster_active_skills_start is None or segment.roster_active_mask_start is None:
                continue
            skills = np.asarray(segment.roster_active_skills_start, dtype=np.int64).reshape(-1)
            mask = np.asarray(segment.roster_active_mask_start, dtype=np.bool_).reshape(-1)
            n = min(skills.size, mask.size, int(self.n_agents))
            skill = int(segment.skill)
            coactive: list[int] = []
            for other_id in range(n):
                if other_id == int(segment.agent_id) or not bool(mask[other_id]):
                    continue
                other_skill = int(skills[other_id])
                if 0 <= other_skill < int(self.n_skills):
                    coactive.append(other_skill)
                    roster_skill_counts[other_skill] += 1.0
            if coactive and 0 <= skill < int(self.n_skills):
                selected.append(skill)
                active_counts.append(len(coactive))
                same_flags.append(1.0 if skill in coactive else 0.0)
        if not selected:
            return {
                "selection_independence_available": 0.0,
                "selection_same_skill_rate": 0.0,
                "selection_independence_null_rate": 0.0,
                "selection_independence_deficit": 0.0,
            }
        total_roster = float(np.sum(roster_skill_counts))
        if total_roster <= 0:
            probs = np.ones(int(self.n_skills), dtype=np.float64) / float(max(self.n_skills, 1))
        else:
            probs = roster_skill_counts / total_roster
        expected = []
        for skill, active_count in zip(selected, active_counts):
            p = float(probs[int(skill)])
            expected.append(1.0 - (1.0 - p) ** int(max(active_count, 1)))
        same_rate = float(np.mean(np.asarray(same_flags, dtype=np.float64)))
        null_rate = float(np.mean(np.asarray(expected, dtype=np.float64))) if expected else 0.0
        return {
            "selection_independence_available": 1.0,
            "selection_same_skill_rate": same_rate,
            "selection_independence_null_rate": null_rate,
            "selection_independence_deficit": same_rate - null_rate,
        }

    @staticmethod
    def _categorical_kl(logits_p: torch.Tensor, logits_q: torch.Tensor) -> torch.Tensor:
        log_p = F.log_softmax(logits_p.float(), dim=-1)
        log_q = F.log_softmax(logits_q.float(), dim=-1)
        p = torch.exp(log_p)
        return torch.sum(p * (log_p - log_q), dim=-1)
