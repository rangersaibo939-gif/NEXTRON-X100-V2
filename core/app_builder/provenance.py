"""Open-source provenance records for NEXTRON Builder components."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ComponentProvenance:
    name: str
    source: str
    license: str
    usage: str


SOURCE_MAP: List[ComponentProvenance] = [
    ComponentProvenance(
        "VibeApp",
        "https://github.com/Skykai521/VibeApp",
        "GPL-3.0",
        "Architecture/reference for AI app generation and build-repair workflows; no source copied into core.",
    ),
    ComponentProvenance(
        "BRB Build",
        "https://github.com/rune-lynx/brb-build",
        "Apache-2.0",
        "Reference candidate for direct on-device Android compilation and signing.",
    ),
    ComponentProvenance(
        "AndCode",
        "https://github.com/yuga-hashimoto/and-code",
        "MIT",
        "Reference candidate for workspace, agent, terminal and Git workflows; third-party dependencies remain separately licensed.",
    ),
    ComponentProvenance(
        "AndroidKris IDE",
        "https://github.com/Krisofts/androidkris-ide",
        "GPLv3 / dependency-specific",
        "Reference for Kotlin/Compose IDE architecture; source integration requires dependency/license review.",
    ),
    ComponentProvenance(
        "BlackLogics",
        "https://github.com/NexusTeamOfficial/BlackLogics-Open-Source",
        "GPL-3.0",
        "Reference for visual/block-based builder concepts; no current GPL source copied into core.",
    ),
    ComponentProvenance(
        "Vibra Code",
        "https://github.com/sa4hnd/vibra-code",
        "AGPL-3.0",
        "Reference for AI app-builder UX and provider abstraction; no AGPL source copied into core.",
    ),
]
