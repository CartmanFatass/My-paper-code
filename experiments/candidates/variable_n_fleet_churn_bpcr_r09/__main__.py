from __future__ import annotations
import argparse
from datetime import datetime,timezone
from pathlib import Path
from .runner import concrete_phase_main

def main()->None:
    parser=argparse.ArgumentParser();parser.add_argument("--phase",choices=("TRAIN","EVALUATE"),required=True);parser.add_argument("--lease",type=Path,required=True);args=parser.parse_args();concrete_phase_main(args.lease,args.phase,now=datetime.now(timezone.utc))
if __name__=="__main__":main()
