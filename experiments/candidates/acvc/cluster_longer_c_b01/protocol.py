"""A fresh 1024-episode C fit under the existing clustered scene law."""
from experiments.candidates.acvc.cluster_deployment_b01 import protocol as shared

OBJECT = "ACVC_CLUSTER_LONGER_C_B01"
CARD = "docs/research/candidates/acvc/ACVC_CLUSTER_LONGER_C_B01_SCIENCE_CARD_20260914.md"
MASTER = 22319
EVALUATION_NAMESPACE = 32319
ARMS = ("C", "F", "dwell")
TRAIN_EPISODES = 1024
PLANNING_SECONDS = dict(whole_supervised_task=450, cumulative_runtime_support=1800, complete_charge=2250)
make_cluster = shared.make_cluster


def final_panel(rows):
    return shared.final_panel(rows, master=MASTER, evaluation_namespace=EVALUATION_NAMESPACE)


def publish(output, process_start):
    return shared.publish(output, process_start, master=MASTER,
                          evaluation_namespace=EVALUATION_NAMESPACE)
