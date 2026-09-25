"""Immutable identities for the accepted B01 finite panel."""
from __future__ import annotations

SOURCE_COMMIT = "424bbe4db1351db70d73560ece913150c2b20ed4"
WORLD_BASE = 92_525_000
WORLDS = tuple(range(WORLD_BASE, WORLD_BASE + 32))
HORIZON = 500
N = 6
RUNTIME_SEED = 92_525_051
ANALYSIS_SEED = 92_525_999
BOOTSTRAP_DRAWS = 10_000
CELL_ORDER = tuple((i, j) for i in (1, 2, 3) for j in (1, 2, 3))
CHECKPOINT_ROOT = "/home/fires/hmasd-retained-runs/agent_count_generalization"
SOURCE = {
    1: {"seed": 1_016_101, "tag": "s1_ordered_roster_confirmation_b20_b1_s1016101",
        "checkpoint_sha256": "89e92ad2f435564593a7823940d1a3ceab7e03f9ae7dc7eb697368b2a2c69763",
        "config_sha256": "e4d4826979c9785753700bf0739c2a855e66da7b6a5fd208bc8e474af8887a93",
        "summary_sha256": "f1786c6b7d96f23877c247d6cca99fef6b9ce84508d6d3b3030140ca4ff37ae5"},
    2: {"seed": 1_017_101, "tag": "s1_ordered_roster_confirmation_b20_b2_s1017101",
        "checkpoint_sha256": "ca2ad80b3a61f6d57ef95bfbd0351852e6d2a519460dda962665048723187f70",
        "config_sha256": "da0467f5712f3a6a91dd40abbab50fd07b47494b0a2e3c7fa7bb600bd4c27e9c",
        "summary_sha256": "232ea569cf7124738314cf7247f93dafbec34b40937b93b9d941383abe691c2f"},
    3: {"seed": 1_018_101, "tag": "s1_ordered_roster_confirmation_b20_b3_s1018101",
        "checkpoint_sha256": "026bc2bafcdf6a6ab8e03be6cd415150ae3a13a156ee6afbfbb00f826d5d02a5",
        "config_sha256": "52a5ba668a7058e56052bf05f1b22dbf7c0077f35b0074377358e5a553c47dfb",
        "summary_sha256": "230f0d29534a269eff0ab533c30842d6c7264643caaacdd5aacaa520a0ff7c6c"},
}

# SHA256 of exact files at SOURCE_COMMIT; usable on nodes without that Git object.
SOURCE_DEPENDENCY_SHA256 = {
    'experiments/candidates/agent_count_generalization/ordered_roster_confirmation_b20/runner.py': '52b6c9fea35dd92ee6b82332d837bbb2abaabd60d0f8f6dcbf450e78eaca230d',
    'experiments/candidates/agent_count_generalization/ordered_roster_confirmation_b20/__init__.py': 'ff51619a2b00faf51f09275f54cc10a2d88209b97f69e074e10308674b960f3d',
    'experiments/candidates/agent_count_generalization/ordered_roster_confirmation_b20/bindings.py': '8707d1cea9c6d984ca0e9a8f54e2debcd478c50ea31d0251d7c9ab590374dfe7',
    'experiments/candidates/agent_count_generalization/ordered_roster_confirmation_b20/reducer.py': '1008c73f7a943b6378282f4486683782a5e3ff948e5e1a52faa5fc141bd9370a',
    'scripts/run_agent_count_ordered_roster_confirmation_b20.py': 'dbab544dd7c17d9bbda2fd0b5c5eb795dd8c3934f754f1dc50861756470a03e7',
    'experiments/candidates/agent_count_generalization/local_ordinary_b16/runner.py': 'b693393b8c0298cfe6b51483f7a937d94f506f86f17c932f842f697e0974b4f5',
    'experiments/candidates/agent_count_generalization/bounded_confirmation_b15/runner.py': '861ebd6362baa99eeea0a04fbce04195d189f7fb71e52eec294d2dbc399335f7',
    'experiments/candidates/agent_count_generalization/action_law_b03/runner.py': 'd9ed78a5dd6faeb1017747d46a428dc61d40929133dd17478348841bb1a03ddb',
    'experiments/candidates/agent_count_generalization/training_condition_b11/runner.py': 'beb7c1dbb9ddb8c78f989c630b0bb66de4703a861d99ac6d5c3a1ea34d940abb',
    'experiments/candidates/agent_count_generalization/configuration.py': 'dd2f03dfcebf71e28d43cc5fe58b0808815fc8c93934d356a8cf777cd6c6bd24',
    'experiments/candidates/agent_count_generalization/runner.py': '21bdaa502ada60a8693bcae0100c1542d048ef94382bdb0b40d3731cad4988d7',
    'experiments/candidates/agent_count_generalization/models.py': 'a92cd142a1b310fce404e52abe9728d54834e4193a281b79b969c9779d082e32',
    'experiments/candidates/agent_count_generalization/adapter.py': 'b59d7028771b5acc4148f7dd90b5480c3143ae88580bb1b8154944831e2c0fbc',
    'hmasd/agent.py': '243ae9e5a68c1bf17efa80cb3cace9b2d04c655fa3c5cdf80f9b738dac8d36b3',
    'hmasd/utils.py': '24018171879485afd5547e03b052333f51986ac1ee57cca6354fc8c8c50c6d47',
    'experiments/candidates/agent_count_generalization/__init__.py': 'd326fbd9929a0bc21a5d8ed36e6ffbfcc9fc338648ec9ba4c020c41b160d997e',
    'experiments/candidates/agent_count_generalization/action_law_b02/__init__.py': 'a8d0ac10f48514e0acf64500eb7b4d2acc27e50526e4362b99c6712639e5a53d',
    'experiments/candidates/agent_count_generalization/action_law_b02/probe.py': '9ed9bc4bac4a292420a49e6fbd8f243bbb914423f76066c1266c11aaf8808e65',
    'experiments/candidates/agent_count_generalization/action_law_b03/__init__.py': 'd0d4a27305dea608f2e56af6f4dbf51c04fb5b4a7c29b735147b979d35de856e',
    'experiments/candidates/agent_count_generalization/bounded_confirmation_b15/__init__.py': 'e477996178d9e7ba736990b06987931792022289caa066c44a4640f0901466e3',
    'experiments/candidates/agent_count_generalization/local_ordinary_b16/__init__.py': 'ace63e9cab740946cd4069b0c4106b8d40c2641a3303bc9ba14694c8693e08ea',
    'experiments/candidates/agent_count_generalization/ordinary_control_b13/__init__.py': '97533d39e14fdfd978d0536af13fc10b48837c2c225fbfb96b7236acbb4e8e2a',
    'experiments/candidates/agent_count_generalization/ordinary_control_b13/runner.py': 'ba5270a08eb3cab464ab7b0ac169585bc0ba5c9d75edbf6e14539e6eb45235b9',
    'experiments/candidates/agent_count_generalization/training_condition_b11/__init__.py': 'd74fce80396e25d7ecbf7be340c87e391e7390945ef2b5b9a32d19972137a1cc',
    'experiments/candidates/agent_count_generalization/initial_policy_b08/__init__.py': 'fb9bbcc20c1a7642c1a07037f41a5e4500c933b5f922868c1f414938dedf3795',
    'experiments/candidates/agent_count_generalization/initial_policy_b08/runner.py': '856ae19df50a95f58ae32a4c5d2952238fa47aac7fa8629b43e48733e2081b75',
    'configs/config_1.py': 'f55b5f148c2664334b455305dea094591799eb0c0544237f7bb717bd1401ccb8',
    'hmasd/baselines.py': 'efc506f96c0140042eb7a0dd17e797386248f20676f8be0c9b08d952d1aa4106',
    'hmasd/networks.py': 'e358deb1d0ecb8c6bccf12d9be620ed57e00c7278b4c61670b50ae278c783955',
    'envs/pettingzoo/env_adapter.py': '8b42c1c3e7ef44cb814f79225b4af944b1018ad764dfeb17e9e1cc294df79d40',
    'envs/pettingzoo/scenario1.py': 'e5b3eb7d755a7d7866cc7cd01531383bee821f0c6d72a81a3d4fa9cb5954939e',
    'envs/pettingzoo/uav_env.py': 'f50d74cdba92d5ef976c8ba53d2697fc72742683fcb746b404b8c8807f463803',
    'scripts/hmasd_admission.py': '0faa5d53fba5af9b1a2fc4979bde5bd50bcbcaac2dbef938e90a64680156cf4d',
}
