"""B06 inclusive chain accounting and exact owned allocated-disk inventory."""
import os
from pathlib import Path
import stat

from experiments.candidates.uav_decision_generalization.b05_request_schedule.costs import (
    BudgetExceeded, Meter as InheritedMeter,
)
from . import contract as c


def allocated_inventory(roots):
    """Count every owned physical inode once; never follow a directory symlink."""
    seen, records, total = set(), [], 0
    for root in dict.fromkeys(str(Path(path).absolute()) for path in roots):
        pending, charged, files = [Path(root)], 0, 0
        while pending:
            path = pending.pop()
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            identity = (info.st_dev, info.st_ino)
            if identity in seen:
                continue
            seen.add(identity)
            value = info.st_blocks * 512
            charged += value
            files += 1
            if stat.S_ISDIR(info.st_mode):
                with os.scandir(path) as entries:
                    pending.extend(Path(entry.path) for entry in entries)
        records.append({'path': root, 'allocated_bytes': charged, 'unique_inodes': files})
        total += charged
    return {'allocated_bytes': total, 'unique_inodes': len(seen), 'roots': records,
            'symlink_targets_followed': False, 'physical_inodes_deduplicated': True}


def acquisition_limits():
    result = {'worker_acquisition_neural_attempted_rows': 1663200,
              'worker_acquisition_neural_rows': 1663200}
    for phase in ('bank_worker', 'bank_reader'):
        for name, limit in {'file_hash_attempts': 2174, 'file_hashes': 2174,
                            'label_attempts': 2100, 'label_contexts': 2100}.items():
            result['b06_' + phase + '_' + name] = limit
    for phase in ('constant_acquisition', 'constant_verification'):
        for name, limit in {'system_attempts': 1, 'systems': 1, 'system_attempted_action_rows': 8400,
                            'system_action_rows': 8400, 'solve_attempts': 1, 'solves': 1}.items():
            result['b06_' + phase + '_' + name] = limit
    for fit in range(3):
        for name in ('scorer_constructor_attempts', 'scorer_constructors'):
            result[f'b06_fit{fit}_{name}'] = 1
        for name in ('update_attempts', 'updates', 'forward_attempts', 'forward_calls',
                     'backward_attempts', 'backwards', 'clip_attempts', 'clips',
                     'optimizer_attempts', 'optimizer_steps'):
            result[f'b06_fit{fit}_{name}'] = 2112
        for name in ('forward_attempted_rows', 'forward_rows'):
            result[f'b06_fit{fit}_{name}'] = 537600
        for stage in ('initial', 'final'):
            for prefix in ('', 'reader_'):
                for name, limit in {'forward_attempts': 33, 'forward_calls': 33,
                                    'forward_attempted_rows': 8400, 'forward_rows': 8400}.items():
                    result[f'b06_{prefix}fit{fit}_{stage}_bank_{name}'] = limit
            for name in ('checkpoint_load_attempts', 'checkpoint_loads',
                         'scorer_constructor_attempts', 'scorer_constructors'):
                result[f'b06_reader_load_fit{fit}_{stage}_{name}'] = 1
    return result


class Meter(InheritedMeter):
    LIMITS = {
        'actual_constructor_attempts': 224, 'actual_constructors': 224,
        'actual_native_attempts': 268800, 'actual_native_steps': 268800,
        'R_native_attempts': 5201920, 'R_native_complete': 5201920,
        'R_initial_attempts': 3840, 'R_initial_complete': 3840,
        'R_tape_attempts': 9600, 'R_tape_draws': 9600, 'R_tape_uniforms': 222720,
        'R_clone_attempts': 33408, 'R_clones': 33408,
        'R_g_attempts': 261888, 'R_g_complete': 261888,
        'R_g_reserved_candidate_ticks': 238540800,
        'R_g_complete_candidate_ticks': 238540800,
        'R_cohorts_complete': 9600, 'R_cohorts_reused': 5760,
        'reader_native_physical_attempts': 269024,
        'reader_R_prefix_physical_attempts': 5201920,
        'reader_R_initial_physical_attempts': 3840,
        'reader_G_attempts': 271488, 'reader_G_reserved_candidate_ticks': 246912000,
        'reader_neural_attempted_rows': 73440,
        'reader_neural_rows': 73440,
        'reader_scorer_constructor_attempts': 6,
        'reader_scorer_constructors': 6,
        **acquisition_limits(),
    }

    def __init__(self, prior, operation_start, *, disk_roots):
        super().__init__(prior, operation_start)
        self.disk_roots = tuple(Path(path) for path in disk_roots)
        self.disk = None
        self.finalizing = False

    def reserve(self, name, amount=1):
        self.check()
        self.add(name, amount)

    def add(self, name, amount=1):
        super().add(name, amount)
        # Only worker acquisition phases contribute here. The reader's Audit
        # explicitly accounts its own bank/deployment aggregate exactly once.
        if name.startswith(('b06_fit0_', 'b06_fit1_', 'b06_fit2_')):
            if name.endswith('_forward_attempted_rows'):
                super().add('worker_acquisition_neural_attempted_rows', amount)
            elif name.endswith('_forward_rows'):
                super().add('worker_acquisition_neural_rows', amount)

    def report(self):
        result = super().report()
        result.update(cpu_stop_seconds=c.CPU_STOP_SECONDS, cpu_limit_seconds=c.CPU_LIMIT_SECONDS,
                      wall_stop_seconds=c.WALL_STOP_SECONDS, wall_limit_seconds=c.WALL_LIMIT_SECONDS,
                      disk_stop_bytes=c.DISK_STOP_BYTES, disk_limit_bytes=c.DISK_LIMIT_BYTES,
                      disk=self.disk, finalization_only=self.finalizing,
                      unknown_unmetered_support_is_zero=False)
        return result

    def check(self):
        report = self.report()
        if self.finalizing:
            raise BudgetExceeded('B06 has entered finalization; no further science')
        if (report['cumulative_cpu_seconds'] >= c.CPU_STOP_SECONDS or
                report['aggregate_operation_wall_seconds'] >= c.WALL_STOP_SECONDS):
            self.finalizing = True
            raise BudgetExceeded('B06 science stop reached; finalization reserve is not new effects')
        return report

    def check_disk(self, *, anticipated_bytes=0, finalization=False):
        """Call before each bounded allocation and after its durable publication.

        Actual/native decision children update already allocated fixed-size
        memmaps. No filesystem walk is inserted into every physical recurrence.
        A bounded writer reserves its maximum new allocation before entering.
        """
        if type(anticipated_bytes) is not int or anticipated_bytes < 0:
            raise ValueError('nonnegative integer prospective disk allocation required')
        self.disk = allocated_inventory(self.disk_roots)
        limit = c.DISK_LIMIT_BYTES if finalization else c.DISK_STOP_BYTES
        if self.disk['allocated_bytes'] + anticipated_bytes > limit:
            self.finalizing = True
            raise BudgetExceeded('B06 owned allocated disk bound reached')
        return dict(self.disk)

    def begin_finalization(self):
        self.finalizing = True
