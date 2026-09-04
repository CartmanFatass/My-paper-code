from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import bounded_worker_map


def test_one_two_four_worker_scheduling_is_order_and_work_deterministic():
    tasks = tuple(range(97))

    def direct_work(index: int):
        return {"task": index, "slots": 12 * (1 + index % 4), "word": (index * 7919) % 65537}

    results = {workers: bounded_worker_map(direct_work, tasks, workers=workers) for workers in (1, 2, 4)}
    assert results[1] == results[2] == results[4]
    assert sum(row["slots"] for row in results[1]) == sum(row["slots"] for row in results[4])
