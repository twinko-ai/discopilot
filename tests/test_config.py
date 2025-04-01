def test_server_restriction():
    """Test server restriction configuration."""
    # Test with no server IDs (unrestricted)
    config = Config()
    config.server_ids = []
    assert config.is_server_restricted is False
    
    # Test with server IDs (restricted)
    config.server_ids = [123456789012345678]
    assert config.is_server_restricted is True 