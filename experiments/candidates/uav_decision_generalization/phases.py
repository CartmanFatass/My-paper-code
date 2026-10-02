"""Shared admitted phase bindings, immutable external manifests and failure retention."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import traceback
from . import contract as c
from .data import Bill, Store, hash_file


def load_bound_json(path, expected):
    if hash_file(path) != expected:
        raise ValueError("external JSON digest changed")
    return json.loads(path.read_bytes())

def accepted_store(script_file, args, admission, paths):
    root = Path(script_file).resolve().parents[3]
    output = args.out_dir.absolute()
    if (args.launch_sha != admission["sha"] or str(output) != paths.get("output_root")
            or output.resolve() != output or str(root) != paths.get("source_root")):
        raise ValueError("admitted source/output/sha binding mismatch")
    launch = json.loads((output/"launch-manifest.json").read_bytes())
    if any(launch.get(k) != v for k,v in {"source_root":str(root),"output_root":str(output),
        "direction":c.DIRECTION,"sha":admission["sha"],"command_sha256":admission["command_sha256"]}.items()):
        raise ValueError("launcher manifest differs from admitted phase")
    prior = load_bound_json(args.budget_ledger,args.budget_ledger_sha256)
    bill = Bill(prior,output,source_root=root)
    return Store(output,bill),admission,prior,root


def dataset_locator(path,sha):
    value = load_bound_json(path,sha)
    if set(value) != {"root","manifest_sha256","summary_sha256"}:
        raise ValueError("invalid immutable dataset/learning locator")
    root = Path(value["root"])
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("locator root must be canonical absolute")
    if hash_file(root/"summary.json") != value["summary_sha256"]:
        raise ValueError("locator terminal summary changed")
    return root,value


def save_torch(store,relative,value,*,kind):
    import torch
    # Parameter/cache payload sizes are small and known. Reserve tensors plus
    # serialization overhead conservatively before writing a new scientific file.
    def size(item):
        if torch.is_tensor(item):
            return item.numel()*item.element_size()
        if isinstance(item,dict):
            return sum(size(x) for x in item.values())
        if isinstance(item,(tuple,list)):
            return sum(size(x) for x in item)
        return 0
    store.bill.check(disk=True,pending_bytes=size(value)+1024*1024)
    path = store.locate(relative)
    with path.open("xb") as stream:
        torch.save(value,stream)
        stream.flush()
        os.fsync(stream.fileno())
    store.bill.observe_file(path)
    return store.record_file(path,kind=kind)


def assert_prior(prior,summary):
    previous = summary["bill"]
    if prior["prior_counters"] != previous["cumulative_counters"]:
        raise ValueError("phase counters do not continue exact previous cumulative bill")
    if (prior["prior_cpu_seconds"] < previous["cumulative_cpu_seconds"]
            or prior["prior_gpu_seconds"] < previous["cumulative_gpu_seconds"]):
        raise ValueError("phase underprices prior CPU/GPU work")


def verify_sources(root):
    for relative,expected in c.SOURCE_SHA256.items():
        if hash_file(root/relative) != expected:
            raise ValueError(f'frozen native source changed: {relative}')


def parser(description, inputs):
    p=argparse.ArgumentParser(description=description)
    p.add_argument('--seed',type=int,required=True,choices=(0,))
    p.add_argument('--launch-sha',required=True)
    p.add_argument('--out','--out-dir',dest='out_dir',type=Path,required=True)
    for name in ('budget-ledger',*inputs):
        p.add_argument('--'+name,type=Path,required=True)
        p.add_argument('--'+name+'-sha256',required=True)
    return p


def failure(store,exc):
    status=store.status('failed_partial',exception_type=type(exc).__name__,exception=str(exc))
    (store.output/'failure.json').write_bytes(c.encode_json({**status,'traceback':traceback.format_exc()}))


def bound_dataset(path,sha,*,old=False,training_only=False):
    from . import models
    root,locator=dataset_locator(path,sha)
    return Dataset(root,locator,old=old,training_only=training_only),locator


class Dataset:
    """Manifest verifies all bytes; only selected train/fresh records are materialized."""
    def __init__(self,root,locator,*,old=False,training_only=False):
        from . import models
        self.root,self.locator=root,locator
        self.manifest_sha256=locator['manifest_sha256']
        self.files=models.verify_manifest(root,self.manifest_sha256)
        self.summary=self.json('summary.json');self.config=self.json('config.json')
        expected=c.ORIGINAL_CONTRACT_SHA256 if old else c.digest(c.frozen_contract())
        if self.summary['status']!='complete' or self.summary['contract_sha256']!=expected:
            raise ValueError('incomplete or mismatched input contract')
        if old and self.summary['source_sha256']!=c.SOURCE_SHA256:
            raise ValueError('old native source mismatch')
        self.records=[]
        for a in c.worlds('train' if training_only else 'fresh'):
            prefix=f"prepared/b{a['block']}/{a['split']}/{a['world']}"
            features=self.json(prefix+'/features.json');c.validate_features(features)
            provenance=self.json(prefix+'/provenance.json')
            labels=self.json(f"worlds/b{a['block']}/{a['split']}/{a['world']}/labels.json")
            identity=c.digest(features)
            if provenance['address']!=a or labels['address']!=a or any(v!=identity for v in (provenance['feature_sha256'],labels['feature_sha256'])):
                raise ValueError('input address/feature binding mismatch')
            slots=sorted(p['construction_slot'] for p in features['plans'])
            if labels['slot_order']!=slots or len(labels['Q'])!=len(slots) or labels['soft_targets']!=c.soft_targets(labels['Q']):
                raise ValueError('label mask/target mismatch')
            if old:
                codec=self.json(prefix+'/codec.json')
                if codec['feature_sha256']!=identity:
                    raise ValueError('old prepared feature identity changed')
            self.records.append({'address':a,'features':features,'provenance':provenance,'labels':labels})
    def json(self,relative):
        if relative not in self.files:
            raise ValueError(f'unbound scientific input: {relative}')
        return json.loads((self.root/relative).read_bytes())
    def split(self,block,split):
        return [r for r in self.records if r['address']['block']==block and r['address']['split']==split]


def phase_input(path,sha,prior=None):
    from . import models
    root,locator=dataset_locator(path,sha)
    files=models.verify_manifest(root,locator['manifest_sha256'])
    for name in ('summary.json','config.json'):
        if name not in files:
            raise ValueError('missing phase binding')
    summary=json.loads((root/'summary.json').read_bytes())
    config=json.loads((root/'config.json').read_bytes())
    if summary['status']!='complete' or summary['contract_sha256']!=c.digest(c.frozen_contract()):
        raise ValueError('incomplete/mismatched sequential phase')
    if prior is not None:
        assert_prior(prior,summary)
    return root,locator,files,summary,config


def require_file(files,relative):
    if relative not in files:
        raise ValueError(f'unbound checkpoint/endpoint: {relative}')


def verify_old_learning(path,sha,native_locator):
    from . import models
    root,locator=dataset_locator(path,sha)
    files=models.verify_manifest(root,locator['manifest_sha256'])
    for name in ('summary.json','config.json'):
        require_file(files,name)
    summary=json.loads((root/'summary.json').read_bytes())
    if summary['status']!='complete' or summary['contract_sha256']!=c.ORIGINAL_CONTRACT_SHA256 or summary['dataset_manifest_sha256']!=native_locator['manifest_sha256']:
        raise ValueError('original frozen N dataset/contract mismatch')
    return root,locator,files


def load_old_n(root,files,block):
    import torch
    from . import models
    relative=f'fits/b{block}/N/final.pt';require_file(files,relative)
    state=torch.load(root/relative,map_location='cpu',weights_only=True)
    if models.parameter_digest(state)!=c.N_FINAL_DIGESTS[block]:
        raise ValueError('frozen N parameter identity mismatch')
    return state


def source_identity(root):
    package=root/'experiments/candidates/uav_decision_generalization'
    return {str(p.relative_to(root)):hash_file(p) for p in sorted(package.glob('*.py'))}


def register_external_roots(store,*roots,category="inherited_evidence"):
    for root in roots:
        if str(root) not in store.bill.root_categories[category]:
            store.bill.root_categories[category].append(str(root))
        if not any(root.is_relative_to(existing) for existing in store.bill.roots):
            store.bill.roots.append(root)
    store.bill.refresh_disk()
    store.bill.check(disk=True)


def verify_phase_source(config,root):
    if config.get('direction_source_sha256')!=source_identity(root):
        raise ValueError('sequential direction source bytes changed')


def verify_numerical_versions():
    import torch
    import numpy as np
    if torch.__version__!='2.7.0+cu118' or np.__version__!='1.26.3':
        raise RuntimeError('frozen numerical dependency versions unavailable')
    return {'torch_version':torch.__version__,'numpy_version':np.__version__}
