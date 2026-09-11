$fixtureCommand = @'
import datetime
import json
from pathlib import Path
import subprocess
import shutil
import time

root = Path('C:/Projects/HMASD-worktrees/dm-n5-continue-20260904')
output = root / 'temp/directions/metric_ground_transport_allocation/exp/conditional_pooling_implementation_20260911_8211'
source_sha = '4be7f07a3f9dab19b21e5f70705e605fdbd1feec'
scratch = root / 'temp/directions/metric_ground_transport_allocation/test/cond_pooling_20260911_8211'
command = ['C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
           'scripts/run_mgtap_conditional_pooling_fixture.py', '--seed', '8211',
           '--output', str(output), '--source-sha', source_sha]
receipt = {'source_sha': source_sha, 'command': command, 'execution_node': 'local_windows',
           'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'complete_command_cap_seconds': 60, 'child_timeout_seconds': 55}
start = time.monotonic()
try:
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=55)
    receipt.update({'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
                    'timed_out': False})
except subprocess.TimeoutExpired as error:
    receipt.update({'returncode': 124, 'timed_out': True, 'error': str(error),
                    'stdout': (error.stdout or b'').decode('utf-8', errors='replace'),
                    'stderr': (error.stderr or b'').decode('utf-8', errors='replace')})
    if scratch.exists():
        receipt['partial_readout_files'] = {path.name: path.read_text(encoding='utf-8')
                                            for path in scratch.glob('*.json')}
        output.mkdir(parents=True, exist_ok=True)
        receipt_path = output / 'COMMAND_RECEIPT.json'
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        assert json.loads(receipt_path.read_text(encoding='utf-8')) == receipt
        assert scratch.resolve().is_relative_to((root / 'temp').resolve())
        shutil.rmtree(scratch)
finally:
    receipt['wall_through_child_exit_and_timeout_cleanup_seconds'] = time.monotonic() - start
    receipt['scratch_absent'] = not scratch.exists()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'COMMAND_RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))
raise SystemExit(receipt['returncode'])
'@
python -c $fixtureCommand
exit $LASTEXITCODE
