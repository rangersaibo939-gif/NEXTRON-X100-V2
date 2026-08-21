"""Modular Android toolchain selection for NEXTRON Builder v2."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Protocol

from ..contracts import BuildRequest, BuildResult


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

    @staticmethod
    def _needs_gradle(request: BuildRequest) -> bool:
        """Kotlin/Compose and Gradle project files require the Gradle backend."""
        source_files = getattr(request, "source_files", {}) or {}
        resource_files = getattr(request, "resource_files", {}) or {}
        paths = list(source_files) + list(resource_files)
        return any(path.endswith(".kt") or path.endswith(".kts") for path in paths)

    def select(self, request: BuildRequest) -> Optional[ToolchainAdapter]:
        # Kotlin/Compose must never be sent to the Java-only direct backend.
        if self._needs_gradle(request):
            gradle = self.capabilities.get(ToolchainBackend.GRADLE)
            if (
                gradle
                and gradle.supports_kotlin
                and ToolchainBackend.GRADLE in self.adapters
            ):
                return self.adapters[ToolchainBackend.GRADLE]

        # Prefer the deterministic direct backend for self-contained Java apps.
        direct = self.capabilities.get(ToolchainBackend.DIRECT_ANDROID)
        if direct and ToolchainBackend.DIRECT_ANDROID in self.adapters:
            if request.source_files and direct.supports_java:
                return self.adapters[ToolchainBackend.DIRECT_ANDROID]

        gradle = self.adapters.get(ToolchainBackend.GRADLE)
        if gradle:
            return gradle
        return None
