# Multi-Brain Integration

NEXTRON now routes the build request through three specialist brains (coder, reasoner, researcher) in parallel, synthesizes their outputs, and feeds the consensus into the existing structured `AIPlanner` before Android generation and Gradle packaging.

The integration is isolated from `main` until CI validation passes.
