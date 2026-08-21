# NEXTRON V2 autonomous builder

The `nextron-autonomous` GitHub Actions workflow is the long-running worker for the V2 builder.

## What it does

1. Runs on pushes to `feature/nextron-builder-v2` and every 30 minutes.
2. Runs Python compilation/tests.
3. Generates a fresh Kotlin/Compose Android project from `AndroidProjectGenerator`.
4. Builds that generated project with Gradle 9.7 on a GitHub-hosted runner.
5. Sends the repository snapshot and validation output to OpenRouter.
6. Lets the model propose a unified patch.
7. Applies the patch, validates again, and repeats up to five iterations.
8. Commits successful changes back to `feature/nextron-builder-v2` with the `[nextron-agent]` marker.
9. The marker prevents the agent's own commit from recursively starting another run.

## Required secret

Create a repository Actions secret named `OPENROUTER_API_KEY` containing an OpenRouter API key. GitHub Actions secrets are encrypted and are only exposed to workflows that explicitly reference them.

Repository: `rangersaibo939-gif/NEXTRON-X100-V2`

Path: **Settings → Secrets and variables → Actions → New repository secret**

Secret name: `OPENROUTER_API_KEY`

The workflow uses the OpenRouter-compatible `/api/v1/chat/completions` endpoint and the `openrouter/auto` model router.

## Safety boundary

The autonomous worker is limited to the working feature branch. It receives only repository source/configuration files, never local Termux secrets. It is instructed not to modify workflow permissions, credentials, or unrelated files.

The worker does not merge into `main` automatically. V2 changes remain on `feature/nextron-builder-v2` for review.
