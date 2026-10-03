"""Whole-purchase CPU/wall accounting, including active decision processes."""
import os
import math
from pathlib import Path
import resource
import time


class BudgetExceeded(RuntimeError):
    pass


def process_cpu(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    except FileNotFoundError:
        return 0.0
    return (int(fields[11]) + int(fields[12])) / os.sysconf('SC_CLK_TCK')


class Meter:
    LIMITS = {'actual_constructor_attempts': 1708, 'actual_constructors': 1708,
              'actual_native_attempts': 2049600, 'actual_native_steps': 2049600,
              'R_native_attempts': 4424000, 'R_native_complete': 4424000,
              'R_initial_attempts': 2100, 'R_initial_complete': 2100,
              'R_tape_attempts': 8400, 'R_g_attempts': 222180,
              'R_g_reserved_candidate_ticks': 205312800,
              'reader_native_physical_attempts': 2051308,
              'reader_R_prefix_physical_attempts': 4424000,
              'reader_R_initial_physical_attempts': 2100,
              'reader_G_reserved_candidate_ticks': 292844160,
              'reader_neural_attempted_rows': 24480,
              'reader_scorer_constructor_attempts': 6}
    def __init__(self, prior, operation_start):
        self.prior = prior
        self.start = operation_start
        self.live = set()
        self.counts = {}
        self.prior_cpu = float(prior['cumulative_cpu_seconds'])
        self.prior_wall = float(prior['aggregate_operation_wall_seconds'])
        if (not math.isfinite(self.prior_cpu) or not math.isfinite(self.prior_wall)
                or self.prior_cpu < 0 or self.prior_wall < 0):
            raise ValueError('negative prior cost')

    def add(self, name, amount=1):
        if not isinstance(amount, int) or amount < 0:
            raise ValueError('nonnegative integer exposure count required')
        self.counts[name] = self.counts.get(name, 0) + amount
        if name in self.LIMITS and self.counts[name] > self.LIMITS[name]:
            raise RuntimeError('selected exposure ceiling exceeded: ' + name)

    def report(self):
        own = resource.getrusage(resource.RUSAGE_SELF)
        dead = resource.getrusage(resource.RUSAGE_CHILDREN)
        live = sum(process_cpu(pid) for pid in tuple(self.live))
        cpu = own.ru_utime + own.ru_stime + dead.ru_utime + dead.ru_stime + live
        wall = time.monotonic() - self.start
        return {'phase_cpu_seconds': cpu, 'phase_wall_seconds': wall,
                'self_user_seconds': own.ru_utime, 'self_system_seconds': own.ru_stime,
                'reaped_child_cpu_seconds': dead.ru_utime + dead.ru_stime,
                'active_child_cpu_seconds': live, 'live_child_pids': sorted(self.live),
                'cumulative_cpu_seconds': self.prior_cpu + cpu,
                'aggregate_operation_wall_seconds': self.prior_wall + wall,
                'self_peak_rss_kib': own.ru_maxrss, 'child_peak_rss_kib': dead.ru_maxrss,
                'gpu_seconds': 0, 'counts': dict(self.counts),
                'cpu_limit_seconds': 50 * 3600, 'wall_limit_seconds': 72 * 3600}

    def check(self):
        report = self.report()
        if (report['cumulative_cpu_seconds'] >= 50 * 3600
                or report['aggregate_operation_wall_seconds'] >= 72 * 3600):
            raise BudgetExceeded('selected cumulative CPU/operation wall ceiling reached')
        return report
