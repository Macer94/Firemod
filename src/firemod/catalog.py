"""A deliberately small optional-system-app list; unknown system apps remain protected."""

LABELS = {
    "com.netflix.ninja": "Netflix", "com.amazon.firetv.youtube": "YouTube",
    "com.amazon.firebat": "Prime Video", "com.amazon.avod": "Prime Video services",
    "com.disney.disneyplus": "Disney+", "com.plexapp.android": "Plex",
    "it.rainet.androidtv": "RaiPlay", "it.mediaset.infinitytv1": "Mediaset Infinity",
    "com.amazon.spiderpork": "Amazon Silk", "com.mgmedia.androidApp": "CHILI",
    "com.luncher.launcher": "Luncher", "org.firemod.home": "Firemod Home helper",
    "it.massi.firehome": "Existing custom Home helper",
    "com.amazon.tv.launcher": "Amazon Home", "com.amazon.firehomestarter": "Amazon Home starter",
    "com.amazon.venezia": "Amazon Appstore", "com.amazon.ftv.profilepicker": "Amazon profiles",
    "com.amazon.vizzini": "Alexa", "com.amazon.client.metrics": "Amazon usage metrics",
    "com.amazon.kso.blackbird": "Amazon advertising service",
    "com.amazon.bueller.photos": "Amazon Photos", "com.amazon.bueller.music": "Amazon Music",
    "com.amazon.ftv.screensaver": "Amazon screensaver",
}

# These can be selected explicitly. Firmware may refuse; Firemod records the refusal.
OPTIONAL_SYSTEM = {
    "com.amazon.client.metrics": "Usage telemetry; may be firmware-protected.",
    "com.amazon.kso.blackbird": "Advertising service; may be firmware-protected.",
    "com.amazon.bueller.photos": "Only disable if you do not use Amazon Photos.",
    "com.amazon.bueller.music": "Only disable if you do not use Amazon Music.",
    "com.amazon.vizzini": "Disables Alexa and voice commands if the firmware allows it.",
}

ALWAYS_KEEP = {
    "android",
    "org.firemod.home", "it.massi.firehome", "com.luncher.launcher",
    "com.amazon.tv.launcher", "com.amazon.firehomestarter", "com.amazon.ftv.profilepicker",
    "com.amazon.venezia", "com.amazon.firebat", "com.amazon.avod",
}


def protected(package: str, system: bool) -> bool:
    return package in ALWAYS_KEEP or (system and package not in OPTIONAL_SYSTEM)
