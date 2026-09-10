"""Bind this already-open session as CM; never start a second CM."""
from pathlib import Path
import subprocess
import sys
runner = Path(__file__).resolve().parents[2] / '_shared/cm_tasks/runner.py'
raise SystemExit(subprocess.call([sys.executable, '-B', str(runner), 'begin', '--mode', 'direct', *sys.argv[1:]]))
