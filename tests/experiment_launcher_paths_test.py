"""Proof-sized command construction checks for the relocated launcher."""

from pathlib import Path

from experiments.launchers import run_experiment_parallel as launcher


def test_launcher_command_resolves_train_entrypoint_from_module_location():
    command = launcher.build_command("hmasd", ["--extra"], 10)

    expected_train_path = (
        Path(launcher.__file__).resolve().parents[2] / "train_multiproc_config_1.py"
    )
    assert command == [
        "python",
        str(expected_train_path),
        "--scenario",
        str(launcher.SCENARIO),
        "--log_dir",
        launcher.LOG_DIR,
        "--exp_name",
        "scenario4_final_results/hmasd",
        "--seed",
        "10",
        "--extra",
    ]
    assert Path(command[1]).is_file()
    assert not (Path(launcher.__file__).resolve().parents[2] / "run_experiment_parallel.py").exists()
