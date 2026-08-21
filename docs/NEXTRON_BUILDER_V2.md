# NEXTRON Builder v2

## Goal

Turn NEXTRON into an AI-native Android app builder while keeping the existing multi-AI orchestration brain independent from the build implementation.

## Architecture

1. **NEXTRON Brain** — task analysis, model routing, agents, evaluation and fallback.
2. **Workspace** — project files, snapshots, diagnostics and Git operations.
3. **Builder Agent** — converts natural-language requirements into project changes.
4. **Toolchain Registry** — selects the best build backend available on the device.
5. **Direct Android backend** — AAPT2/resource processing, compilation, DEX, packaging and signing.
6. **Gradle backend** — fallback for projects requiring the Android/Gradle ecosystem.
7. **Repair loop** — structured build failure → AI diagnosis → patch → rebuild.
8. **Provenance** — every external project/component is recorded with source and license.

## Source strategy

- VibeApp: architecture/reference for AI app generation and build repair. GPL-3.0; do not copy source into the NEXTRON core without deliberate GPL compliance.
- BRB Build: reference/direct-source candidate for the direct on-device Android toolchain; Apache-2.0.
- AndCode: reference/direct-source candidate for workspace, terminal, Git and agent UX; MIT, with dependency-specific review.
- AndroidKris IDE: Kotlin/Compose IDE reference; dependency/license review required.
- BlackLogics: visual/block builder reference; GPL-3.0 current source.
- Vibra Code: AI builder/preview reference; AGPL-3.0.

## Implementation phases

### Phase A — Foundation
- Modular toolchain registry.
- Structured build contracts.
- Provenance registry.
- Direct Android adapter.
- Repair-aware build pipeline.

### Phase B — Real project generation
- Android project templates.
- Kotlin source generation.
- Compose project template.
- Resource/manifest generation.
- Workspace snapshots.

### Phase C — Kotlin/Compose build
- Kotlin compiler discovery/caching.
- Compose compiler/toolchain compatibility.
- Gradle backend for dependency-heavy projects.
- Direct backend for self-contained projects.

### Phase D — Agent loop
- Read compiler diagnostics.
- Map diagnostics to files/lines.
- Generate bounded patches.
- Rebuild and score results.
- Preserve rollback snapshots.

### Phase E — Product
- Project browser.
- Code editor.
- Build console.
- APK output/install action.
- GitHub sync.
- Optional visual/block builder.

## Safety rule

`main` remains the stable branch. Builder v2 changes are developed and validated on `feature/nextron-builder-v2` before merge.
