from __future__ import annotations

import pytest

from clockify_unofficial_cli.auth.credentials import ApiKeyCredential
from clockify_unofficial_cli.auth.credentials import decode
from clockify_unofficial_cli.auth.credentials import encode


@pytest.mark.parametrize(
    ("api_key", "expected"),
    [("abcdefgh1234", "********1234"), ("abc", "***")],
)
def test_masked_hides_all_but_last_four_characters(api_key: str, expected: str) -> None:
    # Arrange
    credential = ApiKeyCredential(api_key=api_key)
    # Act
    masked = credential.masked()
    # Assert
    assert masked == expected


def test_encoded_credential_decodes_to_equal_credential() -> None:
    # Arrange
    credential = ApiKeyCredential(api_key="secret")
    # Act
    decoded = decode(encode(credential))
    # Assert
    assert decoded == credential


@pytest.mark.parametrize(
    "raw",
    ["not json", "[]", '{"kind": "oauth", "api_key": "x"}', '{"kind": "api_key", "api_key": ""}'],
)
def test_decode_rejects_unknown_or_malformed_payloads(raw: str) -> None:
    # Arrange
    payload = raw
    # Act
    decoded = decode(payload)
    # Assert
    assert decoded is None
