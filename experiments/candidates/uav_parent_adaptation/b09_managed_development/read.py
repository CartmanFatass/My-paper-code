#!/usr/bin/env python3
"""Complete bounded B09 saved-data reading; no host or optimizer execution."""
import argparse
import json
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.read import identity
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.read import equal, regenerate_bundle, require
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.read import error_summary
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.reading import episode_metrics
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.verify_coordinator import coordinator_counts, verify_coordinator
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.verify_local import local_counts
from experiments.candidates.uav_parent_adaptation.b09_managed_development.assets import load_inputs
from experiments.candidates.uav_parent_adaptation.b09_managed_development.contract import (
    ASSETS, BASE_PINS, FROZEN, OBJECT, Protocol, arm_parts, base_arm, source_identities, validate_counts,
)
from experiments.candidates.uav_parent_adaptation.b09_managed_development.reading import cost_totals, read_comparisons
from experiments.candidates.uav_parent_adaptation.b09_managed_development.verify_learning import LearningAudit
from experiments.candidates.uav_parent_adaptation.b09_managed_development.verify_local import verify_local, verify_critic_inputs


def read_batch(out, *, permit_fixture=False, check=lambda: None):
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    out = Path(out).resolve()
    progress_path = out / 'reader-progress.json'
    if progress_path.exists() or (out / 'reading.json').exists():
        raise FileExistsError('B09 reader already attempted; reconcile paid work, never repeat')
    calls = dict(environment_steps=0, full_C_ranking_queries=0, optimizer_steps=0,
                 regenerated_tape_integers=0, episode_metric_reconstructions=0,
                 metric_one_step_clip_agent_ops=0, new_head_attempts=0, new_head_completed=0,
                 transfer_head_attempts=0, transfer_head_completed=0, bstar_applications=0,
                 critic_input_rows=0, critic_forward_rows=0, target_formula_rows=0,
                 checkpoint_files=0, update_records=0, critic_initialization_reconstructions=0,
                 **local_counts(), **coordinator_counts())
    progress = dict(object=OBJECT, status='READING', completed_rows=0, current_row=None, reader_calls=calls)

    def publish():
        progress.update(reader_wall_seconds=time.perf_counter() - start_wall,
                        reader_cpu_seconds=time.process_time() - start_cpu,
                        process_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        write_json(progress_path, progress)

    publish()
    try:
        check()
        summary_path, config_path = out / 'summary.json', out / 'config.json'
        summary, config = json.loads(summary_path.read_text()), json.loads(config_path.read_text())
        progress['inputs'] = dict(summary=file_identity(summary_path), config=file_identity(config_path))
        require(summary['object'] == OBJECT and summary['status'] == 'COMPLETE', 'complete B09 collection required')
        protocol = Protocol.from_dict(summary['protocol'])
        production = summary['scientific_invocation']
        require(production or permit_fixture, 'fixture reading must be explicit')
        require(not production or protocol == FROZEN, 'changed production exposure')
        for key in config:
            require(summary[key] == config[key], 'config/summary binding ' + key)
        require(summary['expected'] == protocol.expected(), 'complete expected-cost contract')
        require(summary['source_sha256'] == source_identities(ROOT), 'reader/dependency source identity')
        if production:
            require(torch.get_num_threads() == torch.get_num_interop_threads() == 1, 'reader single-thread contract')
            for name, binding in ASSETS.items():
                require(all(summary['inputs'][name][key] == value for key, value in binding.items()), 'bound original input ' + name)
        else:
            for name, binding in ASSETS.items():
                require(all(summary['inputs'][name][key] != binding[key] for key in ('sha256', 'state_sha256')),
                        'synthetic fixture acquired a production asset')
        input_dir = Path(summary['inputs']['S']['path']).parent
        require(all(Path(value['path']).parent == input_dir for value in summary['inputs'].values()), 'one declared staged input directory')
        actor, transfers, inputs = load_inputs(input_dir, ASSETS if production else summary['inputs'])
        require(inputs == summary['inputs'] == summary['input_preflight'], 'staged file identities')
        require(state_digest(actor.state_dict()) == summary['asset_after_state_sha256'], 'unchanged worker backbone')
        validate_counts(summary)
        require(cost_totals(summary['rows']) == summary['costs'], 'complete worker cost aggregation')
        expected_rows = [(kind + '_S2', world, 0, 'training', group)
                         for group, kind, worlds in protocol.training_schedule() for world in worlds]
        expected_rows += [(arm, world, tape, 'final', None) for arm, world, tape in protocol.schedule()]
        require([(r['arm'], r['world'], r['tape'], r['phase'], r['group']) for r in summary['rows']] == expected_rows,
                'complete ordered on-policy/final schedule')
        learning = LearningAudit(out, summary, protocol, calls)
        bundles = {}
        for worlds, tapes in ((protocol.train_worlds, (0,)), (protocol.worlds, protocol.tapes)):
            for world in worlds:
                for tape in tapes:
                    check()
                    calls['regenerated_tape_integers'] += protocol.horizon // 4 * 11
                    bundles[world, tape] = regenerate_bundle(protocol, world, tape)
        provision = summary['tape_provision']
        require(provision['unique_integers'] == calls['regenerated_tape_integers'] == summary['expected']['unique_tape_integers'],
                'once-per-address private/public tape generation')
        require(provision['unique_bytes'] == calls['regenerated_tape_integers'] * 8
                and provision['unique_bundles'] == len(bundles)
                and not provision['public_stream_used'] and not provision['policy_has_future_entries_or_roots']
                and provision['online_payload_bytes'] == 0, 'tape storage/information contract')
        audits, initials = [], {}
        for index, row in enumerate(summary['rows']):
            check()
            progress['current_row'] = {key: row[key] for key in ('arm', 'world', 'tape', 'phase', 'group')}
            if index % 16 == 0:
                publish()
            program, coordinator = arm_parts(row['arm'])
            require(row['policy_sha256'] == (summary['inputs']['S']['state_sha256'] if program not in ('C', 'Q_I')
                else BASE_PINS['experiments/candidates/uav_local_history/b01/controller.py']), 'row backbone/ordinary source identity')
            head = learning.head_for(row, transfers)
            with np.load(identity(out, row['raw']), allow_pickle=False) as archive:
                raw = {key: archive[key] for key in archive.files}
            local = verify_local(raw, row, protocol, actor, head, bundles.get((row['world'], row['tape'])), calls, check)
            verify_critic_inputs(raw, row, protocol, calls)
            learning.retain_targets(raw, row)
            # S2/T2 wire/search/arrival semantics are unchanged. The inherited
            # reader receives its legal local-family alias only; actual B09
            # policy identities are checked independently above.
            radio = verify_coordinator(raw, {**row, 'arm': base_arm(row['arm'])}, protocol, calls, check)
            calls['episode_metric_reconstructions'] += 1
            calls['metric_one_step_clip_agent_ops'] += protocol.horizon * 5 + protocol.horizon // 4 * 20
            for key, value in episode_metrics(raw, base_arm(row['arm'])).items():
                equal(row[key], value, 'native/exposure metric ' + key, 1e-12)
            equal(row['mean_height_m'], raw['positions'][1:, :, 2].mean(), 'native mean height', 1e-12)
            digest = array_digest(raw['positions'][0], raw['initial_users'], raw['observations'][0])
            require(initials.setdefault(row['world'], digest) == digest, 'common reset geometry/observation')
            audits.append(dict(**progress['current_row'], local=local,
                independently_checked_candidate_pairs=sum(len(r['independently_checked_pairs']) for r in radio['rounds']),
                forecast_error_summary=error_summary(radio['forecast_errors_by_offset'])))
            progress['completed_rows'] = index + 1
            if (index + 1) % 16 == 0:
                publish()
                print('B09_READER', index + 1, 'of', len(summary['rows']), flush=True)
        learning_result = learning.finish()
        e = summary['expected']
        for prefix, expected in (('S_forward', e['reader_s_forward_rows']), ('S_helper', e['reader_s_helper_calls']),
                                 ('new_head', e['new_head_rows_ceiling']), ('transfer_head', e['transfer_head_rows_ceiling']),
                                 ('native_formula', e['reader_native_observation_formula_checks'])):
            require(calls[prefix + '_attempts'] == calls[prefix + '_completed'] == expected, 'complete reader ' + prefix)
        require(calls['bstar_applications'] == e['bstar_rows_ceiling'], 'complete paid temperature2 replay')
        require(calls['critic_input_rows'] == calls['target_formula_rows'] == e['target_rows'], 'complete baseline/return provenance')
        require(calls['candidate_reduction_attempts'] == calls['candidate_reduction_completed']
                <= e['reader_candidate_state_reductions_ceiling'], 'bounded candidate-state reader work')
        require(calls['full_C_ranking_queries'] == calls['environment_steps'] == calls['optimizer_steps']
                == calls['critic_forward_rows'] == 0, 'unselected reader work')
        require(state_digest(actor.state_dict()) == summary['inputs']['S']['state_sha256'], 'reader backbone mutation')
        require(source_identities(ROOT) == summary['source_sha256'], 'reader source drift')
        comparisons = read_comparisons(summary['rows'], protocol)
        require(comparisons == summary['comparisons'], 'all paired final arithmetic')
        for key, path in (('summary', summary_path), ('config', config_path)):
            require(file_identity(path) == progress['inputs'][key], 'reader input changed')
        result = dict(object=OBJECT, status='VERIFIED', launch_sha=summary['launch_sha'], inputs=progress['inputs'],
            source_sha256=summary['source_sha256'], assets=summary['inputs'], actual=summary['actual'],
            worker_costs=summary['costs'], reader_calls=calls, learning=learning_result,
            audits=audits, comparisons=comparisons,
            reader_wall_seconds=time.perf_counter() - start_wall, reader_cpu_seconds=time.process_time() - start_cpu,
            process_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            scope='Every native endpoint and report/terminal observation formula, all local helper/backbone/head/I-decoder '
            'rows including training, source/asset/group identities, finite pre-action critic inputs and native-return '
            'targets verified. All saved S2/T2 search and delivery arithmetic; at most five actually scored candidate '
            'pairs per round. Parameter movement and optimizer counts/provenance checked. No native rerun, full C '
            'reranking, critic forward replay, optimizer replay or all-unselected-candidate physics claim. One training '
            'realization per arm; two tapes averaged within final world clusters. Timing includes prior reader writes; '
            'final self-writes excluded.')
        write_json(out / 'reading.json', result)
        progress.update(status='VERIFIED', current_row=None)
        publish()
        return result
    except BaseException:
        progress.update(status='INCOMPLETE', error=traceback.format_exc())
        publish()
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    result = read_batch(args.out)
    print('B09_READ_COMPLETE', result['status'], flush=True)


if __name__ == '__main__':
    main()
