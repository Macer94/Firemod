from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Device:
    serial: str
    state: str
    model: str = ""
    transport: str = ""


@dataclass(frozen=True)
class DeviceInfo:
    serial: str
    model: str
    manufacturer: str
    fire_os: str
    android: str
    sdk: int
    available_mb: int
    total_mb: int
    free_storage: str
    disabled_count: int
    boot_id: str

    @property
    def is_fire_tv(self) -> bool:
        return self.manufacturer.lower() == "amazon" and self.model.startswith("AFT")


@dataclass(frozen=True)
class Package:
    name: str
    label: str
    system: bool
    disabled: bool
    hidden: bool
    protected: bool
    note: str = ""


@dataclass
class Plan:
    animations: str | None = None
    privacy: bool = False
    screensaver: bool = False
    launcher: bool = False
    accelerator: bool = False
    packages: list[str] = field(default_factory=list)
    enable_packages: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not any((self.animations is not None, self.privacy, self.screensaver,
                        self.launcher, self.accelerator, self.packages, self.enable_packages))


@dataclass
class Outcome:
    done: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    snapshot: str = ""
