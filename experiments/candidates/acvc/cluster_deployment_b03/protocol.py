"""Prospective identity for one independent same-law cluster deployment B."""
from experiments.candidates.acvc.cluster_deployment_b01 import protocol as shared

OBJECT = "ACVC_CLUSTER_DEPLOYMENT_B03"
CARD = "docs/research/candidates/acvc/ACVC_CLUSTER_DEPLOYMENT_B03_SCIENCE_CARD_20260914.md"
MASTER = 21937
EVALUATION_NAMESPACE = 31937
ARMS = ("C", "F", "dwell")
PLANNING_SECONDS = dict(whole_supervised_task=300, cumulative_runtime_support=1200, complete_charge=1500)
make_cluster = shared.make_cluster


def final_panel(rows):
    return shared.final_panel(rows, master=MASTER, evaluation_namespace=EVALUATION_NAMESPACE)


def publish(output, process_start):
    return shared.publish(output, process_start, master=MASTER,
                          evaluation_namespace=EVALUATION_NAMESPACE)
