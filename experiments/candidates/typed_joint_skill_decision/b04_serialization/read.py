"""Read a terminal serialization record without invoking its target encoder."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.dont_write_bytecode=True
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiments.candidates.typed_joint_skill_decision.b04_serialization import records


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root',type=Path,required=True)
    parser.add_argument('--input-manifest',type=Path,required=True)
    parser.add_argument('--input-manifest-sha256',required=True)
    args=parser.parse_args(argv)
    value=records.manifest(args.input_manifest,args.input_manifest_sha256)
    print(records.json_bytes(records.read_records(args.run_root,value,ROOT,args.input_manifest_sha256)).decode(),end='')


if __name__=='__main__':main()
