"""Read the bound terminal data-bank record without numerical imports or queries."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
sys.dont_write_bytecode=True
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import contract as c
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import evidence as e


def read(root,digest):
    root=Path(root).resolve(strict=True);manifest=c.read_bound(root/'artifact-manifest.json',digest)
    for name,expected in manifest['files'].items():c.verify_file(c.relative(root,name),expected)
    launch=json.loads((root/'launch-manifest.json').read_bytes());witness=None
    if (root/'process-exit.json').exists():
        witness=json.loads((root/'process-exit.json').read_bytes())
        if (witness['status']!='exited' or type(witness['exit_code']) is not int
            or witness['process_identity']!=launch['runner_process']['identity']
            or witness['supervisor_identity']!=launch['process']['identity']):raise ValueError('native terminal identity mismatch')
    if 'summary.json' not in manifest['files']:
        return {'status':'partial_terminal_summary_missing','native_exit_code':None if witness is None else witness['exit_code'],
            'verified_artifacts':len(manifest['files']),'completion':'unknown; no complete bank certification'}
    if 'shared-counters.bin' not in manifest['files']:raise ValueError('required final counter artifact not bound')
    config=json.loads((root/'config.json').read_bytes()) if 'config.json' in manifest['files'] else None
    summary=json.loads((root/'summary.json').read_bytes())
    if (summary['launch_sha']!=manifest['launch_sha'] or summary['launch_sha']!=launch['sha']
        or summary['input_sha256']!=manifest['input_sha256'] or summary['scientific_source_sha']!=c.SCIENCE_SHA
        or summary['scientific_input_sha256']!=c.SCIENCE_INPUT):raise ValueError('terminal scientific/launch/input identity mismatch')
    if config and (config['launch_sha']!=manifest['launch_sha'] or config['input_sha256']!=manifest['input_sha256']
        or config['counter_schema']!=list(e.COUNTERS)):raise ValueError('configuration source/input/counter schema mismatch')
    block=(root/'shared-counters.bin').read_bytes()
    if len(block)!=e.BLOCK_BYTES:raise ValueError('final counter block schema mismatch')
    final={name:e.Q.unpack_from(block,8*i)[0] for i,name in enumerate(e.COUNTERS)}
    reported=summary['bill'].get('counters',summary['bill'].get('shared',{}).get('counters'))
    if final!=reported:raise ValueError('bound final counter block/summary mismatch')
    complete=summary['status']=='complete_compatible_bank' and config is not None and witness is not None and witness['exit_code']==0
    if complete:
        required={'producer_worlds_completed':16512,'reader_worlds_completed':16512,'producer_shards_completed':258,
            'reader_shards_completed':258,'compatibility_worlds':2501,'compatibility_labels':430980,
            'hosts':33028,'raw_constructions':33024,'static_calls':2*summary['producer_labels']+16}
        if any(final[k]!=v for k,v in required.items()) or any(final[k] for k in ('fits','native_steps','model_forwards','gpu_seconds','matching_calls')):
            raise ValueError('complete bank counter/denominator mismatch')
        for stage in ('producer','reader'):
            for index in range(258):
                for filename in ('context.json','config.json','summary.json','process-exit.json','artifact-manifest.json'):
                    if f'raw/process/{stage}/{index:04d}/{filename}' not in manifest['files']:raise ValueError('unbound required complete child witness')
        for index in range(258):
            split,local,_=c.shard(index)
            for kind in ('bank','label-reader'):
                if f'raw/{kind}/{split}/{local:04d}.npz' not in manifest['files']:raise ValueError('unbound required complete bank/reader shard')
    return {'status':'complete_compatible_bank' if complete else 'partial_or_terminal_unconfirmed','summary':summary,
        'native_exit_code':None if witness is None else witness['exit_code'],'verified_artifacts':len(manifest['files']),
        'trust':'byte-bound saved data/full-reader evidence; no host/physics/model replay; exit or old progress alone does not certify a bank',
        'final_counter_block_matches_summary':True,'resource_checks_total':final['resource_checks']+final['parent_resource_checks'],
        'imports':c.guard(parent=True)}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-root',required=True,type=Path)
    p.add_argument('--artifact-manifest-sha256',required=True)
    args=p.parse_args(argv);sys.stdout.buffer.write(c.encoded(read(args.run_root,args.artifact_manifest_sha256)))


if __name__=='__main__':main()
