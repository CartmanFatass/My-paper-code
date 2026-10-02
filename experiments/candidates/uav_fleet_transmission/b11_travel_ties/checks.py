"""One metered local finite-check attempt; no native or real RF construction allowed."""
from __future__ import annotations
import argparse
import contextlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def main():
    wall,cpu=time.perf_counter(),time.process_time()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--attempt",required=True,type=int)
    args=parser.parse_args()
    for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):
        os.environ[name]="1"
    from experiments.candidates.uav_fleet_transmission.b11_travel_ties.contract import (
        OBJECT,source_binding,identity,sha256,write_json,sum_counts)
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    stem=f"attempt_{args.attempt:02d}"
    for ext in (".json",".stdout.txt",".xml"):
        if (out/(stem+ext)).exists():raise FileExistsError(out/(stem+ext))
    prior_paths=sorted(out.glob("attempt_*.json"))
    if args.attempt!=len(prior_paths)+1:raise ValueError("attempts must be explicit and contiguous")
    before=source_binding()
    testdir=ROOT/"tests/experiments/candidates/uav_fleet_transmission/b11_travel_ties"
    tests={str(p.relative_to(ROOT)):sha256(p) for p in sorted(testdir.glob("test_*.py"))}
    import pytest
    with (out/(stem+".stdout.txt")).open("w") as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        code=int(pytest.main(["-q",str(testdir),"--junitxml="+str(out/(stem+".xml"))]))
    suite=ET.parse(out/(stem+".xml")).getroot()
    counts={}
    for prop in suite.iter("property"):
        if prop.attrib.get("name")=="b11_scripted_mock_counts":counts=json.loads(prop.attrib["value"])
    after=source_binding()
    record=dict(object=OBJECT,attempt=args.attempt,exit_code=code,
        status="passed" if code==0 and before==after else "failed",
        cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-wall,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        source_binding=before,test_sources=tests,actual_counts=counts,
        actual_native_steps=0,actual_native_resets=0,actual_private_models=counts.get("model_constructions",0),
        actual_rf_calls=counts.get("model_rf_calls",0),fits=0,
        tests=sum(int(x.attrib.get("tests",0)) for x in suite.iter("testsuite")),
        artifacts={stem+ext:identity(out/(stem+ext)) for ext in (".stdout.txt",".xml")})
    if record["actual_private_models"] or record["actual_rf_calls"]:
        record["status"]="failed";code=1
    write_json(out/(stem+".json"),record)
    attempts=[json.loads(p.read_text()) for p in prior_paths]+[record]
    total=sum_counts(a["actual_counts"] for a in attempts)
    summary=dict(object=OBJECT,status=record["status"],source_binding=after,test_sources=tests,
        cpu_seconds=sum(a["cpu_seconds"] for a in attempts),wall_seconds=sum(a["wall_seconds"] for a in attempts),
        attempts=attempts,actual_counts=total,actual_native_steps=0,actual_native_resets=0,
        actual_private_models=sum(a["actual_private_models"] for a in attempts),
        actual_rf_calls=sum(a["actual_rf_calls"] for a in attempts),fits=0,
        unmeasured_support="source authoring, static parsing, hashing/publication and transport outside this metered check process; not zero CPU")
    if total.get("candidate_forecasts",0)>576 or total.get("proposals",0)>732:
        summary["status"]="failed";code=1
    write_json(out/"checks.json",summary)
    print(json.dumps({k:summary[k] for k in ("status","cpu_seconds","actual_counts","actual_native_steps","actual_rf_calls")}))
    raise SystemExit(code if summary["status"]=="passed" else 1)


if __name__=="__main__":main()
