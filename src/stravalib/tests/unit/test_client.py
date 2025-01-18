import stravalib


def test_client_protocol_initialization():
    """Test that instantiating Client sets corresponding values in protocol."""
    client = stravalib.Client(
        access_token="access_123",
        token_expires=123456,
        refresh_token="refresh_123",
    )

    assert client.protocol.access_token == "access_123"
    assert client.protocol.token_expires == 123456
    assert client.protocol.refresh_token == "refresh_123"
