# NEXTRON App Builder Foundation

## Goal

NEXTRON will gain an on-device Android app-builder subsystem while preserving the existing X-100 multi-AI orchestration brain.

## Reference architecture

The open-source VibeApp project demonstrates a practical Android-native pipeline: resource processing, Java compilation, DEX conversion, APK packaging, signing, project management, and AI-assisted build repair. We inspected its public source and are using those capabilities as an architectural reference.

VibeApp is GPL-3.0. This branch therefore does **not** copy VibeApp source files. NEXTRON's initial builder contracts and orchestration code are independently written. Any future source incorporation must be reviewed for license compliance and attribution before distribution.

## NEXTRON architecture

```text
NEXTRON X-100 Brain
        |
        v
Task analysis / model routing / agent selection
        |
        v
NEXTRON App Builder
  |-- Project workspace
  |-- Source/resource generation
  |-- Build adapter
  |     |-- resource compilation
  |     |-- source compilation
  |     |-- DEX
  |     |-- APK packaging
  |     `-- APK signing
  |-- Build diagnostics
  `-- AI repair loop
```

## Current implementation

`core/app_builder/` contains NEXTRON-owned contracts for:

- build requests and generated project files;
- structured build stages and diagnostics;
- build artifacts and results;
- a provider-neutral pipeline with bounded repair attempts.

The Android compiler adapter is intentionally not hard-coded yet. This lets us add and test the on-device toolchain independently from the X-100 routing layer.

## VibeApp mapping

| VibeApp concept | NEXTRON direction |
|---|---|
| Agent loop | Existing X-100 orchestration + future builder agent |
| Project manager/workspace | NEXTRON App Builder workspace |
| BuildPipeline | `core/app_builder/pipeline.py` |
| BuildResult/BuildStage | `core/app_builder/contracts.py` |
| Build failure analyzer | Future NEXTRON diagnostic adapter |
| Resource compiler | Future Android toolchain adapter |
| D8 conversion | Future Android toolchain adapter |
| APK packaging | Future Android toolchain adapter |
| APK signing | Future Android toolchain adapter |

## Phase 1 target

The first end-to-end milestone is:

> Natural-language app request -> NEXTRON generates a minimal Android project -> on-device adapter builds it -> structured diagnostics are returned -> AI repair can retry -> signed APK is produced.

No changes are made to `main` by this foundation branch.
