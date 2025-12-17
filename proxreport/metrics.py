from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import time
from typing import Optional, Tuple


@dataclass(frozen=True)
class DiskStat:
    mountpoint: str
    total_bytes: int
    used_bytes: int
    free_bytes: int


@dataclass(frozen=True)
class HostSnapshot:
    hostname: str
    now_ts: float
    uptime_seconds: Optional[float]

    cpu_count: int
    cpu_usage_percent: Optional[float]
    load1: Optional[float]
    load5: Optional[float]
    load15: Optional[float]

    mem_total_kb: Optional[int]
    mem_available_kb: Optional[int]

    disks: Tuple[DiskStat, ...]


class CpuSampler:
    def __init__(self) -> None:
        self._prev_total: Optional[int] = None
        self._prev_idle: Optional[int] = None

    def sample(self) -> Optional[float]:
        # Returns CPU usage since last call, in percent.
        try:
            total, idle = _read_proc_stat_total_idle()
        except Exception:
            return None

        if self._prev_total is None or self._prev_idle is None:
            self._prev_total, self._prev_idle = total, idle
            return None

        delta_total = total - self._prev_total
        delta_idle = idle - self._prev_idle
        self._prev_total, self._prev_idle = total, idle

        if delta_total <= 0:
            return None

        busy = max(0, delta_total - delta_idle)
        return (busy / delta_total) * 100.0


_CPU_SAMPLER = CpuSampler()


def snapshot(mountpoints: Tuple[str, ...]) -> HostSnapshot:
    hostname = os.uname().nodename if hasattr(os, "uname") else "unknown"
    now_ts = time.time()

    cpu_count = os.cpu_count() or 1
    cpu_usage = _CPU_SAMPLER.sample()

    load1 = load5 = load15 = None
    try:
        l1, l5, l15 = os.getloadavg()
        load1, load5, load15 = float(l1), float(l5), float(l15)
    except Exception:
        pass

    mem_total_kb, mem_avail_kb = _read_meminfo()
    disks = tuple(_disk_stat(mp) for mp in mountpoints)

    return HostSnapshot(
        hostname=hostname,
        now_ts=now_ts,
        uptime_seconds=_read_uptime_seconds(),
        cpu_count=cpu_count,
        cpu_usage_percent=cpu_usage,
        load1=load1,
        load5=load5,
        load15=load15,
        mem_total_kb=mem_total_kb,
        mem_available_kb=mem_avail_kb,
        disks=disks,
    )


def _read_uptime_seconds() -> Optional[float]:
    try:
        raw = Path("/proc/uptime").read_text(encoding="utf-8").strip()
        first = raw.split()[0]
        return float(first)
    except Exception:
        return None


def _read_proc_stat_total_idle() -> Tuple[int, int]:
    # /proc/stat first line: cpu  user nice system idle iowait irq softirq steal ...
    line = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0]
    parts = line.split()
    if parts[0] != "cpu":
        raise ValueError("unexpected /proc/stat format")
    fields = [int(x) for x in parts[1:]]
    if len(fields) < 4:
        raise ValueError("unexpected /proc/stat field count")

    user, nice, system, idle = fields[0], fields[1], fields[2], fields[3]
    iowait = fields[4] if len(fields) > 4 else 0
    irq = fields[5] if len(fields) > 5 else 0
    softirq = fields[6] if len(fields) > 6 else 0
    steal = fields[7] if len(fields) > 7 else 0

    idle_all = idle + iowait
    non_idle = user + nice + system + irq + softirq + steal
    total = idle_all + non_idle

    return total, idle_all


def _read_meminfo() -> Tuple[Optional[int], Optional[int]]:
    # Returns (MemTotal_kB, MemAvailable_kB)
    try:
        data = Path("/proc/meminfo").read_text(encoding="utf-8")
        total = avail = None
        for line in data.splitlines():
            if line.startswith("MemTotal:"):
                total = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                avail = int(line.split()[1])
        return total, avail
    except Exception:
        return None, None


def _disk_stat(mountpoint: str) -> DiskStat:
    st = os.statvfs(mountpoint)
    total = st.f_frsize * st.f_blocks
    free = st.f_frsize * st.f_bavail
    used = max(0, total - free)
    return DiskStat(
        mountpoint=mountpoint,
        total_bytes=int(total),
        used_bytes=int(used),
        free_bytes=int(free),
    )
