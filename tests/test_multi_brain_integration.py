def test_multi_brain_module_imports():
    from core.multi_brain import MultiBrainOrchestrator

    assert MultiBrainOrchestrator.ROLE_CAPABILITIES["coder"] == "coding"
    assert MultiBrainOrchestrator.ROLE_CAPABILITIES["reasoner"] == "reasoning"
    assert MultiBrainOrchestrator.ROLE_CAPABILITIES["researcher"] == "research"
