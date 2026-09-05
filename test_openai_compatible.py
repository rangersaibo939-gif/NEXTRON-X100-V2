
    # orchestrator = Orchestrator(providers=[primary_provider, backup_provider])
    
    # Simulate primary failure via monkeypatching its network request
    # monkeypatch.setattr(primary_provider, "create_completion", lambda *args, **kwargs: raise_api_error...)

    # assert orchestrator.create_completion(...) calls backup_provider
