from pathlib import Path

from core.app_builder.contracts import BuildRequest, BuildStage, BuildStatus
from core.app_builder.toolchain.gradle_backend import GradleAndroidAdapter


def request(tmp_path: Path) -> BuildRequest:
    return BuildRequest(
        project_id="demo",
        project_name="demo",
        package_name="com.nextron.demo",
        working_directory=str(tmp_path),
        source_files={"com/nextron/demo/MainActivity.kt": "package com.nextron.demo\n"},
    )


def test_gradle_prefers_project_wrapper(tmp_path: Path):
    wrapper = tmp_path / "gradlew"
    wrapper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    command = GradleAndroidAdapter()._command(tmp_path, "debug")
    assert command[0] == str(wrapper)
    assert command[1] == "assembleDebug"
    assert "--no-daemon" in command


def test_gradle_missing_backend_returns_failure(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    result = GradleAndroidAdapter("missing-gradle").build(request(tmp_path))
    assert result.status is BuildStatus.FAILED
    assert result.failed_stage is BuildStage.COMPILE
    assert "not found" in (result.error_message or "")


def test_gradle_finds_latest_apk(tmp_path: Path):
    old = tmp_path / "app/build/outputs/apk/debug/old.apk"
    new = tmp_path / "app/build/outputs/apk/debug/new.apk"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"old")
    new.write_bytes(b"new")
    assert GradleAndroidAdapter._find_apk(tmp_path, request(tmp_path)) == new
