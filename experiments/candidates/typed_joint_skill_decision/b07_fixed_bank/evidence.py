"""Reuse B05 exclusive evidence/counter layout with B07's selected smaller stops."""
from __future__ import annotations
import time
from experiments.candidates.typed_joint_skill_decision.b05_data_bank import evidence as old
from . import contract as c

CAPS={k:c.LIMITS[k] for k in ('static_calls','hosts','raw_constructions','fits','native_steps','model_forwards','gpu_seconds')}
CAPS.update(rng_streams=16512,matching_calls=0,audit_episodes=0,main_episodes=0,
            producer_worlds_attempted=0,producer_shards_completed=0,permutation_reads=0,
            spawn_attempts=258,reader_worlds_attempted=16512)


class Shared(old.Shared):
    def charge(self,name,n=1):
        if type(n) is not int or n<0:raise ValueError('nonnegative integer counter charge')
        if name in CAPS and self.get(name)+n>CAPS[name]:
            old.Q.pack_into(self.buffer,8*old.INDEX['refused_effects'],self.get('refused_effects')+1)
            raise RuntimeError('B07 hard effect cap before invocation: '+name)
        # B07 bounds are a subset of the unchanged B05 bounds.
        super().charge(name,n)


class Budget(old.Budget):
    def check(self,pending=0,sample_disk=True):
        self.shared.charge('resource_checks' if self.child else 'parent_resource_checks')
        usage=old.cpu();wall=old.process_wall()
        cpu_limit=115 if self.child else c.LIMITS['cpu_seconds']-10
        wall_limit=230 if self.child else c.LIMITS['wall_seconds']-10
        if usage['unmeasured_live_pids']:raise RuntimeError('live child CPU unmeasured; no zero substitution')
        if usage['total_seconds']>=cpu_limit or wall>=wall_limit:raise RuntimeError('B07 finite CPU/wall boundary')
        now=time.monotonic()
        if sample_disk and (now-self.last>=2 or self.pending+pending>=8*1024**2):
            self.disk_peak=max(self.disk_peak,self.fixed+old.allocated(self.mutable,set(self.frozen)));self.last=now;self.pending=0
        if self.disk_peak+self.pending+pending+2*1024**2>c.LIMITS['normal_disk_bytes']:raise RuntimeError('B07 normal scoped disk boundary')
        self.pending+=pending

    def snapshot(self):
        result=super().snapshot()
        result.update(limits=c.LIMITS,core_reserve_bytes=c.LIMITS['core_reserve_bytes'])
        return result

    def finalization_space(self,amount):
        actual=self.fixed+old.allocated(self.mutable,set(self.frozen));self.disk_peak=max(self.disk_peak,actual)
        if actual+amount+65536>c.LIMITS['normal_disk_bytes']:raise RuntimeError('B07 final metadata exceeds scoped disk cap')

# Unchanged B05 evidence helpers; no source mutation or global replacement.
from experiments.candidates.typed_joint_skill_decision.b05_data_bank.evidence import (
 COUNTERS,NATIVE,LAUNCH_FILES,Q,BLOCK_BYTES,process_identity,process_wall,cpu,allocated,
 durable,replace_json,Store,Trace,merge_child,failure_artifacts,journal_bounds)
