# NEXTRON Multi-Brain Integration

The Multi-Brain layer is now wired into the real NEXTRON build path.

Flow:
1. User request enters `core.nextron.main()`.
2. Coder, Reasoner, and Researcher brains run concurrently.
3. A reasoning-capable provider synthesizes the specialist outputs.
4. The existing `AIPlanner` converts the consensus into the structured app plan.
5. Kotlin/Compose generation and Gradle APK build continue unchanged.

This keeps the stable Android builder on `main` while the multi-brain integration is isolated on the feature branch.
