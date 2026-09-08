"""Only the two process boundaries commissioned by P16."""

import ctypes
import os
import signal
import subprocess
import time
from ctypes import wintypes as w


def remaining(deadline, clock=time.monotonic):
    seconds = deadline - clock()
    if seconds <= 0:
        raise TimeoutError("P16 work deadline exhausted")
    return seconds


class WindowsJob:
    """Own one suspended child and all its descendants before any child code runs.

    The owning controller alone holds the non-inheritable job handle. Windows
    closes it on controller loss and terminates the job, including grandchildren.
    """

    def __init__(self, argv):
        if os.name != "nt":
            raise RuntimeError("P16 local acquisition requires Windows")
        k = self.k = ctypes.WinDLL("kernel32", use_last_error=True)

        class Basic(ctypes.Structure):
            _fields_ = [("per_process", ctypes.c_int64), ("per_job", ctypes.c_int64),
                        ("flags", w.DWORD), ("min_ws", ctypes.c_size_t),
                        ("max_ws", ctypes.c_size_t), ("active", w.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", w.DWORD),
                        ("scheduling", w.DWORD)]

        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in
                        ("read", "write", "other", "read_bytes", "write_bytes", "other_bytes")]

        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", IO),
                        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                        ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]

        class Startup(ctypes.Structure):
            _fields_ = [("cb", w.DWORD), ("reserved", w.LPWSTR), ("desktop", w.LPWSTR),
                        ("title", w.LPWSTR), ("x", w.DWORD), ("y", w.DWORD),
                        ("width", w.DWORD), ("height", w.DWORD), ("xchars", w.DWORD),
                        ("ychars", w.DWORD), ("fill", w.DWORD), ("flags", w.DWORD),
                        ("show", w.WORD), ("reserved_size", w.WORD),
                        ("reserved_ptr", ctypes.POINTER(ctypes.c_byte)),
                        ("stdin", w.HANDLE), ("stdout", w.HANDLE), ("stderr", w.HANDLE)]

        class Process(ctypes.Structure):
            _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE),
                        ("pid", w.DWORD), ("tid", w.DWORD)]

        class StartupEx(ctypes.Structure):
            _fields_ = [("startup", Startup), ("attributes", ctypes.c_void_p)]

        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        k.CreateJobObjectW.restype = w.HANDLE
        k.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        k.InitializeProcThreadAttributeList.argtypes = [ctypes.c_void_p, w.DWORD, w.DWORD,
                                                       ctypes.POINTER(ctypes.c_size_t)]
        k.UpdateProcThreadAttribute.argtypes = [ctypes.c_void_p, w.DWORD, ctypes.c_size_t,
                                               ctypes.c_void_p, ctypes.c_size_t,
                                               ctypes.c_void_p, ctypes.c_void_p]
        k.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
        k.CreateProcessW.argtypes = [w.LPCWSTR, w.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                                    w.BOOL, w.DWORD, ctypes.c_void_p, w.LPCWSTR,
                                    ctypes.POINTER(Startup), ctypes.POINTER(Process)]
        k.ResumeThread.argtypes = [w.HANDLE]
        k.ResumeThread.restype = w.DWORD
        k.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        k.WaitForSingleObject.restype = w.DWORD
        k.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
        k.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
        k.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
        k.CloseHandle.argtypes = [w.HANDLE]
        self.job = k.CreateJobObjectW(None, None)
        self.process = None
        if not self.job:
            raise ctypes.WinError(ctypes.get_last_error())
        info = Extended()
        info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        si, pi = StartupEx(), Process()
        si.startup.cb = ctypes.sizeof(si)
        size = ctypes.c_size_t()
        attributes = None
        try:
            if not k.SetInformationJobObject(self.job, 9, ctypes.byref(info), ctypes.sizeof(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            command = ctypes.create_unicode_buffer(subprocess.list2cmdline([str(a) for a in argv]))
            k.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
            attributes = ctypes.create_string_buffer(size.value)
            if not k.InitializeProcThreadAttributeList(attributes, 1, 0, ctypes.byref(size)):
                attributes = None
                raise ctypes.WinError(ctypes.get_last_error())
            job_list = (w.HANDLE * 1)(self.job)
            # PROC_THREAD_ATTRIBUTE_JOB_LIST assigns the job atomically at creation.
            if not k.UpdateProcThreadAttribute(attributes, 0, 0x0002000D, job_list,
                                               ctypes.sizeof(job_list), None, None):
                raise ctypes.WinError(ctypes.get_last_error())
            si.attributes = ctypes.cast(attributes, ctypes.c_void_p)
            # EXTENDED_STARTUPINFO_PRESENT | CREATE_SUSPENDED | CREATE_NO_WINDOW.
            if not k.CreateProcessW(None, command, None, None, False, 0x08080004,
                                    None, None, ctypes.cast(ctypes.byref(si), ctypes.POINTER(Startup)),
                                    ctypes.byref(pi)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.process, self.pid = pi.process, pi.pid
            self.thread = pi.thread
        except BaseException:
            self.close()
            raise
        finally:
            if attributes is not None:
                k.DeleteProcThreadAttributeList(attributes)

    def resume(self):
        if self.k.ResumeThread(self.thread) == 0xFFFFFFFF:
            raise ctypes.WinError(ctypes.get_last_error())
        self.k.CloseHandle(self.thread)
        self.thread = None

    def wait(self, seconds):
        result = self.k.WaitForSingleObject(self.process, max(0, int(seconds * 1000)))
        if result == 258:
            raise TimeoutError("P16 local job reached its work cutoff")
        if result != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        code = w.DWORD()
        if not self.k.GetExitCodeProcess(self.process, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value

    def close(self):
        if self.job:
            self.k.TerminateJobObject(self.job, 1)
            self.k.CloseHandle(self.job)
            self.job = None
        if self.process:
            self.k.CloseHandle(self.process)
            self.process = None
        if getattr(self, "thread", None):
            self.k.CloseHandle(self.thread)
            self.thread = None



def boottime():
    return time.clock_gettime(time.CLOCK_BOOTTIME)


class LinuxLimit:
    """One-shot absolute BOOTTIME limit for a remote helper, including its I/O.

    Only the detached setup uses a new process group. Short supervisor/tmux
    clients are directly bounded, and the receiver has no child process.
    """

    def __init__(self, deadline):
        self.child = None
        self.group = False
        self.old_alarm = signal.signal(signal.SIGALRM, self.expire)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        libc = self.libc = ctypes.CDLL(None, use_errno=True)

        class Event(ctypes.Structure):
            # Linux x86_64 sigevent: sigval, signo, notify, 48-byte union.
            _fields_ = [("value", ctypes.c_void_p), ("signo", ctypes.c_int),
                        ("notify", ctypes.c_int), ("padding", ctypes.c_byte * 48)]

        class Timespec(ctypes.Structure):
            _fields_ = [("seconds", ctypes.c_long), ("nanoseconds", ctypes.c_long)]

        class TimerSpec(ctypes.Structure):
            _fields_ = [("interval", Timespec), ("value", Timespec)]

        libc.timer_create.argtypes = [ctypes.c_int, ctypes.POINTER(Event), ctypes.POINTER(ctypes.c_void_p)]
        libc.timer_settime.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(TimerSpec), ctypes.c_void_p]
        libc.timer_delete.argtypes = [ctypes.c_void_p]
        self.timer = ctypes.c_void_p()
        event = Event()
        event.signo = signal.SIGALRM  # SIGEV_SIGNAL == 0.
        if libc.timer_create(time.CLOCK_BOOTTIME, ctypes.byref(event), ctypes.byref(self.timer)):
            raise OSError(ctypes.get_errno(), "P16 absolute timer_create failed")
        spec = TimerSpec()
        spec.value.seconds = int(deadline)
        spec.value.nanoseconds = int((deadline - int(deadline)) * 1_000_000_000)
        # TIMER_ABSTIME prevents bootstrap or scheduling delay from restarting time.
        if libc.timer_settime(self.timer, 1, ctypes.byref(spec), None):
            libc.timer_delete(self.timer)
            raise OSError(ctypes.get_errno(), "P16 absolute timer_settime failed")

    def kill_child(self):
        if self.child is not None:
            try:
                if self.group:
                    os.killpg(self.child.pid, signal.SIGKILL)
                elif self.child.poll() is None:
                    self.child.kill()
            except ProcessLookupError:
                pass

    def expire(self, signum, frame):
        self.kill_child()
        os._exit(124)

    def run(self, argv, deadline, group=False, **kwargs):
        remaining(deadline, boottime)
        # An alarm cannot land between process creation and ownership assignment.
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
        try:
            self.group = group
            self.child = subprocess.Popen(
                argv, start_new_session=group,
                preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM}),
                **kwargs)
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        try:
            return self.child.wait(timeout=remaining(deadline, boottime))
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("P16 remote work deadline exhausted") from exc
        finally:
            self.kill_child()
            self.child.wait()
            self.child = None

    def close(self):
        self.kill_child()
        self.libc.timer_delete(self.timer)
        signal.signal(signal.SIGALRM, self.old_alarm)
