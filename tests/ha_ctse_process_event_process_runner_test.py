from __future__ import annotations

import inspect

import ha_ctse_process.event_process_runner as event_process_runner
import ha_ctse_process.standalone_train_runner as standalone_train_runner
import ha_ctse_process.train as train


MOVED_DEFINITIONS = (
    "_iteration5_semantic_checkpoint",
    "_restore_iteration5_vector_checkpoint",
    "_open_iteration5_window",
    "_apply_iteration5_transaction_hooks",
    "_evaluate_iteration5_spatial_model",
    "_run_iteration5_process_semantics_branch",
)


def test_iteration5_runner_has_one_true_owner_and_train_dispatches_it() -> None:
    runner_source = inspect.getsource(event_process_runner)
    train_source = inspect.getsource(train)

    assert "ha_ctse_process.train" not in runner_source
    for name in MOVED_DEFINITIONS:
        assert f"def {name}(" in runner_source
        assert f"def {name}(" not in train_source

    assert (
        standalone_train_runner._run_iteration5_process_semantics_branch
        is event_process_runner._run_iteration5_process_semantics_branch
    )
    assert "return _run_iteration5_process_semantics_branch(config, args, writer)" in (
        inspect.getsource(standalone_train_runner.train_loop)
    )
