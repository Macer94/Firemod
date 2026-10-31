from pathlib import Path

from .models import DeviceInfo, Package


class DemoEngine:
    """Read-only fixtures for UI previews and smoke tests. Never opens ADB."""

    def inspect(self):
        return DeviceInfo("DEMO", "AFTT", "Amazon", "Fire OS 5.2.9.5", "5.1.1", 22,
                          183, 874, "2.6G", 0, "demo-boot")

    def packages(self):
        return [Package("com.netflix.ninja", "Netflix", False, False, False, False),
                Package("com.amazon.firetv.youtube", "YouTube", False, False, False, False),
                Package("com.disney.disneyplus", "Disney+", False, False, False, False),
                Package("com.plexapp.android", "Plex", False, False, False, False),
                Package("it.rainet.androidtv", "RaiPlay", False, False, False, False),
                Package("com.amazon.client.metrics", "Amazon usage metrics", True, False, False, False,
                        "Usage telemetry; firmware may refuse."),
                Package("com.amazon.tv.launcher", "Amazon Home", True, False, False, True),
                Package("com.amazon.tv.settings.v2", "Amazon settings", True, False, False, True)]

    def snapshots(self) -> list[Path]:
        return []

    def bridge_status(self):
        return True
