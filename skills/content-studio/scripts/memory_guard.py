#!/usr/bin/env python3
"""Run a heavy local model job (music, video, image, a large LLM) under a memory cap, so it fails instead of the computer.

Usage:
  python3 memory_guard.py [--max-gb 20] [--min-free-gb 30] [--min-disk-gb 20] [--floor-gb 6] -- <command> [args…]

  or from Python (the script's own folder on sys.path):
  from memory_guard import run_guarded
  sys.exit(run_guarded([sys.executable, "job.py", …], max_gb=20))

Before it starts, it refuses (exit 75) when the computer has less than --min-free-gb of memory available or less
than --min-disk-gb free on the disk that holds swap. While the job runs it reads the memory footprint of the job and
every process it started, twice a second, and kills the whole job (exit 137) when that passes --max-gb, or when the
computer's available memory falls under --floor-gb. At the end it prints one JSON line to stderr:
  {"guard": "ok" | "killed" | "refused", "peak_gb": …, "max_gb": …, "why": …, "seconds": …}

Why: a local music model sizes itself for the whole unified memory of an Apple Silicon Mac. On a 64 GB Mac that was
already running a local language model it reached 54 GB in about two minutes, and with the disk nearly full swap
could not grow; the Mac stopped answering and the hardware watchdog reset it, three times in two days (Nov 2026).
macOS has no cgroups and ignores `ulimit -v`, so a cap has to watch from outside and kill. A failed take is cheap;
a reset loses every open window.

Footprint is the process's physical footprint on macOS (what Activity Monitor shows as Memory, GPU buffers
included), resident size on Linux, working set or private bytes on Windows. Standard library only.
"""
import argparse
import ctypes
import json
import os
import shutil
import signal
import subprocess
import sys
import time

GB = 1024 ** 3
REFUSED, KILLED = 75, 137


# --- reading memory ---------------------------------------------------------------------------------------------

class _RusageInfoV2(ctypes.Structure):
    _fields_ = [("ri_uuid", ctypes.c_uint8 * 16)] + [(n, ctypes.c_uint64) for n in (
        "ri_user_time", "ri_system_time", "ri_pkg_idle_wkups", "ri_interrupt_wkups", "ri_pageins", "ri_wired_size",
        "ri_resident_size", "ri_phys_footprint", "ri_proc_start_abstime", "ri_proc_exit_abstime",
        "ri_child_user_time", "ri_child_system_time", "ri_child_pkg_idle_wkups", "ri_child_interrupt_wkups",
        "ri_child_pageins", "ri_child_elapsed_abstime", "ri_diskio_bytesread", "ri_diskio_byteswritten")]


_libproc = None
if sys.platform == "darwin":
    try:
        _libproc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        _libproc.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
    except OSError:
        _libproc = None


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32)] + [(n, ctypes.c_size_t) for n in (
        "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
        "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_uint32), ("dwMemoryLoad", ctypes.c_uint32)] + [(n, ctypes.c_uint64) for n in (
        "ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile", "ullTotalVirtual", "ullAvailVirtual",
        "ullAvailExtendedVirtual")]


def _windows_footprint(pid):
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(0x1000 | 0x0010, False, pid)  # QUERY_LIMITED_INFORMATION | VM_READ
    if not h:
        return 0
    try:
        c = _ProcessMemoryCounters()
        c.cb = ctypes.sizeof(c)
        if ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(c), c.cb):
            return max(c.WorkingSetSize, c.PrivateUsage)
        return 0
    finally:
        k32.CloseHandle(h)


def footprint(pid):
    """Bytes the process holds: physical footprint on macOS, resident size on Linux, the larger of working set and
    private bytes on Windows; 0 when it is gone."""
    if sys.platform == "win32":
        return _windows_footprint(pid)
    if _libproc is not None:
        info = _RusageInfoV2()
        if _libproc.proc_pid_rusage(pid, 2, ctypes.byref(info)) == 0:
            return max(info.ri_phys_footprint, info.ri_resident_size)
        return 0
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    return 0


def descendants(root):
    """The pid and every process under it. `ps -o pid=,ppid=` only: never the command lines (they can hold secrets).
    On Windows only the job's own process is watched (the job is the model process itself)."""
    if sys.platform == "win32":
        return [root]
    try:
        out = subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return [root]
    kids = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2:
            kids.setdefault(int(parts[1]), []).append(int(parts[0]))
    seen, todo = [], [root]
    while todo:
        p = todo.pop()
        if p not in seen:
            seen.append(p)
            todo.extend(kids.get(p, []))
    return seen


def available():
    """Bytes the computer can hand out without swapping: free + inactive + speculative + purgeable pages on macOS,
    MemAvailable on Linux, available physical memory on Windows; None when unknown."""
    if sys.platform == "win32":
        m = _MemoryStatusEx()
        m.dwLength = ctypes.sizeof(m)
        return m.ullAvailPhys if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) else None
    if sys.platform == "darwin":
        try:
            out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        page = 4096
        pages = {}
        for line in out.splitlines():
            if "page size of" in line:
                page = int(line.split("page size of")[1].split()[0])
            elif ":" in line:
                k, v = line.split(":", 1)
                try:
                    pages[k.strip()] = int(v.strip().rstrip("."))
                except ValueError:
                    pass
        keys = ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable")
        return sum(pages.get(k, 0) for k in keys) * page
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    return None


def swap_disk_free():
    """Free bytes on the volume that holds swap (on macOS it shares its container with the data volume)."""
    for path in ("/System/Volumes/VM", "/System/Volumes/Data", os.environ.get("SystemDrive", "") + "\\", "/"):
        if os.path.isdir(path):
            return shutil.disk_usage(path).free
    return None


# --- the guard --------------------------------------------------------------------------------------------------

def _report(**kw):
    print(json.dumps({k: (round(v / GB, 1) if k.endswith("_gb") and isinstance(v, int) else v) for k, v in kw.items()}),
          file=sys.stderr, flush=True)


def preflight(min_free_gb=30.0, min_disk_gb=20.0):
    """None when the job may start, else the reason it may not."""
    avail = available()
    if avail is not None and avail < min_free_gb * GB:
        return (f"only {avail / GB:.1f} GB of memory is available and this job needs {min_free_gb:g} GB free to start: "
                "close other heavy jobs (a local language model, a video render) or wait until they are done")
    disk = swap_disk_free()
    if disk is not None and disk < min_disk_gb * GB:
        return (f"only {disk / GB:.1f} GB is free on the disk that holds swap; under {min_disk_gb:g} GB a memory spike "
                "can freeze the computer instead of slowing it: free disk space first")
    return None


def _kill(pids, pgid, child=None):
    if sys.platform == "win32":
        if child is not None:
            child.kill()
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pgid)], capture_output=True)
        return
    try:
        os.killpg(pgid, signal.SIGKILL)
    except OSError:
        pass
    for p in pids:
        try:
            os.kill(p, signal.SIGKILL)
        except OSError:
            pass


def run_guarded(cmd, max_gb=20.0, min_free_gb=30.0, min_disk_gb=20.0, floor_gb=6.0, interval=0.5, env=None):
    """Run cmd under the cap; return its exit code, REFUSED (75) or KILLED (137). Prints the JSON report to stderr."""
    started = time.time()
    why = preflight(min_free_gb, min_disk_gb)
    if why:
        _report(guard="refused", peak_gb=0, max_gb=max_gb, why=why, seconds=0)
        return REFUSED
    child = subprocess.Popen(cmd, env=env, start_new_session=sys.platform != "win32")
    pgid = child.pid
    peak, outcome, why = 0, "ok", None

    def forward(sig, _frame):
        _kill(descendants(child.pid), pgid, child)
        sys.exit(128 + sig)

    for name in ("SIGINT", "SIGTERM", "SIGHUP"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), forward)
    while child.poll() is None:
        pids = descendants(child.pid)
        used = sum(footprint(p) for p in pids)
        peak = max(peak, used)
        if used > max_gb * GB:
            outcome, why = "killed", f"the job reached {used / GB:.1f} GB, over the {max_gb:g} GB cap"
        else:
            avail = available()
            if avail is not None and avail < floor_gb * GB:
                outcome, why = "killed", (f"the computer had only {avail / GB:.1f} GB left (floor {floor_gb:g} GB) "
                                          f"while the job held {used / GB:.1f} GB")
        if outcome == "killed":
            _kill(pids, pgid, child)
            child.wait()
            break
        time.sleep(interval)
    code = KILLED if outcome == "killed" else child.returncode
    _report(guard=outcome, peak_gb=peak, max_gb=max_gb, why=why, seconds=round(time.time() - started), exit=code)
    return code


def main():
    if "--" not in sys.argv:
        sys.exit(__doc__)
    split = sys.argv.index("--")
    a = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    a.add_argument("--max-gb", type=float, default=20.0, help="kill the job above this footprint (default 20)")
    a.add_argument("--min-free-gb", type=float, default=30.0, help="refuse to start under this much available memory")
    a.add_argument("--min-disk-gb", type=float, default=20.0, help="refuse to start under this much free disk")
    a.add_argument("--floor-gb", type=float, default=6.0, help="kill the job when the computer's available memory "
                                                              "falls under this")
    a.add_argument("--interval", type=float, default=0.5)
    o = a.parse_args(sys.argv[1:split])
    cmd = sys.argv[split + 1:]
    if not cmd:
        sys.exit("give the command after --")
    sys.exit(run_guarded(cmd, o.max_gb, o.min_free_gb, o.min_disk_gb, o.floor_gb, o.interval))


if __name__ == "__main__":
    main()
