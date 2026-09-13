"""Prospective identity for one independent same-law cluster deployment B."""
from experiments.candidates.acvc.cluster_deployment_b01 import protocol as shared

OBJECT = "ACVC_CLUSTER_DEPLOYMENT_B02"
CARD = "docs/research/candidates/acvc/ACVC_CLUSTER_DEPLOYMENT_B02_SCIENCE_CARD_20260913.md"
MASTER = 21493
EVALUATION_NAMESPACE = 31493
ARMS = ("C", "F", "dwell")
CAPS = dict(whole_supervised_task=600, cumulative_runtime_support=600, complete_charge=1200)
make_cluster = shared.make_cluster


def final_panel(rows):
    return shared.final_panel(rows, master=MASTER, evaluation_namespace=EVALUATION_NAMESPACE)


def publish(output, process_start):
    return shared.publish(output, process_start, master=MASTER,
                          evaluation_namespace=EVALUATION_NAMESPACE)
