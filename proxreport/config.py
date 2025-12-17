from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import configparser


DEFAULT_CONFIG_PATH = "/etc/proxreport/config.ini"


@dataclass(frozen=True)
class Thresholds:
    cpu_warn: int = 70
    cpu_crit: int = 90
    ram_warn: int = 70
    ram_crit: int = 90
    disk_warn: int = 75
    disk_crit: int = 90


@dataclass(frozen=True)
class CapacityProfile:
    name: str
    vcpus: int
    ram_mb: int
    disk_gb: int


@dataclass(frozen=True)
class CapacityConfig:
    reserve_cores: int = 1
    reserve_ram_mb: int = 1024
    reserve_disk_gb: int = 10
    standard: CapacityProfile = CapacityProfile("standard", 2, 4096, 32)
    light: CapacityProfile = CapacityProfile("light", 1, 1024, 16)


@dataclass(frozen=True)
class ServerConfig:
    http_port: int = 8080
    https_port: int = 8443
    certfile: str = "/etc/proxreport/tls/cert.pem"
    keyfile: str = "/etc/proxreport/tls/key.pem"
    users_file: str = "/etc/proxreport/users.txt"
    autorefresh_seconds: int = 10


@dataclass(frozen=True)
class AppConfig:
    server: ServerConfig = ServerConfig()
    thresholds: Thresholds = Thresholds()
    mountpoints: tuple[str, ...] = ("/",)
    capacity: CapacityConfig = CapacityConfig()


def _getint(cp: configparser.ConfigParser, section: str, key: str, default: int) -> int:
    try:
        return cp.getint(section, key)
    except Exception:
        return default


def _getstr(cp: configparser.ConfigParser, section: str, key: str, default: str) -> str:
    try:
        val = cp.get(section, key)
        return val.strip() if val is not None else default
    except Exception:
        return default


def _get_mountpoints(cp: configparser.ConfigParser) -> tuple[str, ...]:
    raw = _getstr(cp, "storage", "mountpoints", "/")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return tuple(parts) if parts else ("/",)


def load_config(path: str) -> AppConfig:
    cp = configparser.ConfigParser()

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {path}")

    cp.read(path)

    server = ServerConfig(
        http_port=_getint(cp, "server", "http_port", ServerConfig.http_port),
        https_port=_getint(cp, "server", "https_port", ServerConfig.https_port),
        certfile=_getstr(cp, "server", "certfile", ServerConfig.certfile),
        keyfile=_getstr(cp, "server", "keyfile", ServerConfig.keyfile),
        users_file=_getstr(cp, "server", "users_file", ServerConfig.users_file),
        autorefresh_seconds=_getint(cp, "server", "autorefresh_seconds", ServerConfig.autorefresh_seconds),
    )

    thresholds = Thresholds(
        cpu_warn=_getint(cp, "thresholds", "cpu_warn", Thresholds.cpu_warn),
        cpu_crit=_getint(cp, "thresholds", "cpu_crit", Thresholds.cpu_crit),
        ram_warn=_getint(cp, "thresholds", "ram_warn", Thresholds.ram_warn),
        ram_crit=_getint(cp, "thresholds", "ram_crit", Thresholds.ram_crit),
        disk_warn=_getint(cp, "thresholds", "disk_warn", Thresholds.disk_warn),
        disk_crit=_getint(cp, "thresholds", "disk_crit", Thresholds.disk_crit),
    )

    capacity = CapacityConfig(
        reserve_cores=_getint(cp, "capacity", "reserve_cores", CapacityConfig.reserve_cores),
        reserve_ram_mb=_getint(cp, "capacity", "reserve_ram_mb", CapacityConfig.reserve_ram_mb),
        reserve_disk_gb=_getint(cp, "capacity", "reserve_disk_gb", CapacityConfig.reserve_disk_gb),
        standard=CapacityProfile(
            name="standard",
            vcpus=_getint(cp, "profile_standard", "vcpus", CapacityConfig.standard.vcpus),
            ram_mb=_getint(cp, "profile_standard", "ram_mb", CapacityConfig.standard.ram_mb),
            disk_gb=_getint(cp, "profile_standard", "disk_gb", CapacityConfig.standard.disk_gb),
        ),
        light=CapacityProfile(
            name="light",
            vcpus=_getint(cp, "profile_light", "vcpus", CapacityConfig.light.vcpus),
            ram_mb=_getint(cp, "profile_light", "ram_mb", CapacityConfig.light.ram_mb),
            disk_gb=_getint(cp, "profile_light", "disk_gb", CapacityConfig.light.disk_gb),
        ),
    )

    return AppConfig(
        server=server,
        thresholds=thresholds,
        mountpoints=_get_mountpoints(cp),
        capacity=capacity,
    )
