"""Modular Android toolchain selection for NEXTRON Builder v2.

This is NEXTRON-owned orchestration code. Concrete backends can wrap
compatible open-source implementations without coupling the core to them.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Protocol

from .contracts import BuildRequest, BuildResult


class ToolchainBackend(str, Enum):
    DIRECT_ANDROID = "direct_android"
    GRADLE = "gradle"


class ToolchainAdapter(Protocol):
    def build(self, request: BuildRequest) -> BuildResult:
        ...


@dataclass(frozen=True)
class ToolchainCapabilities:
    backend: ToolchainBackend
    supports_kotlin: bool
    supports_compose: bool
    supports_java: bool
    supports_resources: bool
    supports_signing: bool


@dataclass
class ToolchainRegistry:
    """Registry that lets NEXTRON choose the best available build backend."""

    adapters: Dict[ToolchainBackend, ToolchainAdapter]
    capabilities: Dict[ToolchainBackend, ToolchainCapabilities]

    def register(
        self,
        backend: ToolchainBackend,
        adapter: ToolchainAdapter,
        capabilities: ToolchainCapabilities,
    ) -> None:
        self.adapters[backend] = adapter
        self.capabilities[backend] = capabilities

    def select(self, request: BuildRequest) -> Optional[ToolchainAdapter]:
        # Prefer a direct on-device backend for small/self-contained projects.
        direct = self.capabilities.get(ToolchainBackend.DIRECT_ANDROID)
        if direct and ToolchainBackend.DIRECT_ANDROID in self.adapters:
            if request.source_files and direct.supports_java:
                return self.adapters[ToolchainBackend.DIRECT_ANDROID]

        gradle = self.adapters.get(ToolchainBackend.GRADLE)
        if gradle:
            return gradle
        return None
