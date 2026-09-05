
def test_failover_to_backup_provider(monkeypatch):
    # Setup primary provider (will fail)
    primary_provider = OpenAICompatibleProvider(
        name="primary",
        base_url="https://api.primary-groq.com/openai/v1",
        api_key_env="TEST_PRIMARY_KEY"
    )
    
    # Setup backup provider (should succeed)
    backup_provider = OpenAICompatibleProvider(
        name="backup",
        base_url="https://api.backup-openai.com/v1", 
        api_key_env="TEST_BACKUP_KEY"
    )

    # Need a higher-level orchestrator class instance that manages these
    # orchestrator = Orchestrator(providers=[primary_provider, backup_provider])
    
    # Simulate primary failure via monkeypatching its network request
    # monkeypatch.setattr(primary_provider, "create_completion", lambda *args, **kwargs: raise_api_error...)

    # assert orchestrator.create_completion(...) calls backup_provider
