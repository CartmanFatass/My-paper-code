"""Example only: nonempty [row, agent] finite terms; a bool decision mask.

Use only when the contract says to sum eligible agent terms and average ALL
rows. This is not the mean over eligible decisions, nor a full PPO objective.
"""
import torch


def row_mean_of_agent_sum(terms, decision_mask):
    return torch.where(decision_mask, terms, 0).sum(dim=-1).mean()
