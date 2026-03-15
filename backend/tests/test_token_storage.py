"""Tests for Fernet-encrypted token storage in Redis."""

import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.fernet import Fernet

from app.auth.token_storage import (
    StoredToken,
    TokenEncryptionError,
    TokenNotFoundError,
    _get_fernet,  # pyright: ignore[reportPrivateUsage]
    delete_token,
    get_token,
    reset_fernet,
    store_token,
)


@pytest.fixture(autouse=True)
def _reset_fernet_singleton() -> None:  # pyright: ignore[reportUnusedFunction]
    reset_fernet()


@pytest.fixture
def fernet_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def fake_settings(fernet_key: str) -> SimpleNamespace:
    return SimpleNamespace(fernet_key=fernet_key)


@pytest.fixture
def sample_token() -> StoredToken:
    return StoredToken(
        access_token="ya29.access-token-value",
        refresh_token="1//refresh-token-value",
        expires_at=int(time.time()) + 3600,
        scopes=["openid", "email", "profile"],
    )


@pytest.fixture
def mock_redis() -> AsyncMock:
    return AsyncMock()


class TestStoreToken:
    async def test_should_encrypt_and_store_token(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
        fernet_key: str,
        sample_token: StoredToken,
    ) -> None:
        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
        ):
            await store_token("user-123", sample_token)

        call_args = mock_redis.hset.call_args
        mapping = call_args.kwargs["mapping"]

        assert mapping["access_token"] != sample_token.access_token
        assert mapping["refresh_token"] != sample_token.refresh_token

        fernet = Fernet(fernet_key.encode())
        assert (
            fernet.decrypt(mapping["access_token"].encode()).decode()
            == sample_token.access_token
        )
        assert (
            fernet.decrypt(mapping["refresh_token"].encode()).decode()
            == sample_token.refresh_token
        )

        assert mapping["expires_at"] == str(sample_token.expires_at)
        assert json.loads(mapping["scopes"]) == sample_token.scopes

    async def test_should_use_correct_redis_key_pattern(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
        sample_token: StoredToken,
    ) -> None:
        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
        ):
            await store_token("user-abc", sample_token)

        key = mock_redis.hset.call_args.args[0]
        assert key == "oauth_token:user-abc:google"

    async def test_should_set_ttl_with_safety_margin(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
    ) -> None:
        future_time = int(time.time()) + 3600
        token = StoredToken(
            access_token="a",
            refresh_token="r",
            expires_at=future_time,
            scopes=["openid"],
        )

        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
        ):
            await store_token("user-123", token)

        mock_redis.expire.assert_awaited_once()
        actual_ttl = mock_redis.expire.call_args.args[1]
        expected_ttl = future_time - int(time.time()) - 300
        assert abs(actual_ttl - expected_ttl) <= 2

    async def test_should_use_fallback_ttl_when_already_expired(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
    ) -> None:
        past_time = int(time.time()) - 100
        token = StoredToken(
            access_token="a",
            refresh_token="r",
            expires_at=past_time,
            scopes=["openid"],
        )

        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
        ):
            await store_token("user-123", token)

        mock_redis.expire.assert_awaited_once()
        actual_ttl = mock_redis.expire.call_args.args[1]
        assert actual_ttl == 60


class TestGetToken:
    async def test_should_return_decrypted_token(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
        fernet_key: str,
    ) -> None:
        fernet = Fernet(fernet_key.encode())
        encrypted_data = {
            "access_token": fernet.encrypt(b"ya29.my-access-token").decode(),
            "refresh_token": fernet.encrypt(b"1//my-refresh-token").decode(),
            "expires_at": "1700000000",
            "scopes": '["openid", "email"]',
        }
        mock_redis.hgetall.return_value = encrypted_data

        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
        ):
            result = await get_token("user-123")

        assert result.access_token == "ya29.my-access-token"
        assert result.refresh_token == "1//my-refresh-token"
        assert result.expires_at == 1700000000
        assert result.scopes == ["openid", "email"]

    async def test_should_raise_not_found_for_missing_user(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
    ) -> None:
        mock_redis.hgetall.return_value = {}

        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
            pytest.raises(TokenNotFoundError, match="user-missing"),
        ):
            await get_token("user-missing")

    async def test_should_raise_encryption_error_for_corrupted_data(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
    ) -> None:
        corrupted_data = {
            "access_token": "not-valid-fernet-ciphertext",
            "refresh_token": "also-invalid",
            "expires_at": "1700000000",
            "scopes": '["openid"]',
        }
        mock_redis.hgetall.return_value = corrupted_data

        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
            pytest.raises(TokenEncryptionError, match="decryption failed"),
        ):
            await get_token("user-123")

    async def test_should_raise_encryption_error_for_malformed_metadata(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
        fernet_key: str,
    ) -> None:
        fernet = Fernet(fernet_key.encode())
        malformed_data = {
            "access_token": fernet.encrypt(b"valid-token").decode(),
            "refresh_token": fernet.encrypt(b"valid-refresh").decode(),
            "expires_at": "not-an-integer",
            "scopes": "not-valid-json{",
        }
        mock_redis.hgetall.return_value = malformed_data

        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
            pytest.raises(TokenEncryptionError, match="decryption failed"),
        ):
            await get_token("user-123")

    async def test_should_raise_encryption_error_for_missing_fields(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
    ) -> None:
        mock_redis.hgetall.return_value = {"expires_at": "1700000000"}

        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
            pytest.raises(TokenEncryptionError, match="decryption failed"),
        ):
            await get_token("user-123")


class TestDeleteToken:
    async def test_should_delete_redis_key(
        self,
        mock_redis: AsyncMock,
    ) -> None:
        with patch("app.auth.token_storage.get_redis", return_value=mock_redis):
            await delete_token("user-123")

        mock_redis.delete.assert_awaited_once_with("oauth_token:user-123:google")

    async def test_should_not_raise_for_nonexistent_token(
        self,
        mock_redis: AsyncMock,
    ) -> None:
        mock_redis.delete.return_value = 0

        with patch("app.auth.token_storage.get_redis", return_value=mock_redis):
            await delete_token("user-nonexistent")


class TestFernetInitialization:
    def test_should_raise_when_fernet_key_not_configured(self) -> None:
        with (
            patch(
                "app.auth.token_storage.settings",
                SimpleNamespace(fernet_key=""),
            ),
            pytest.raises(TokenEncryptionError, match="not configured"),
        ):
            _get_fernet()

    def test_should_raise_for_invalid_fernet_key(self) -> None:
        with (
            patch(
                "app.auth.token_storage.settings",
                SimpleNamespace(fernet_key="not-a-valid-key"),
            ),
            pytest.raises(TokenEncryptionError, match="Invalid FERNET_KEY"),
        ):
            _get_fernet()

    def test_should_reuse_fernet_instance(self, fernet_key: str) -> None:
        with patch(
            "app.auth.token_storage.settings",
            SimpleNamespace(fernet_key=fernet_key),
        ):
            first = _get_fernet()
            second = _get_fernet()
            assert first is second


class TestRoundTrip:
    async def test_should_store_and_retrieve_identical_token(
        self,
        mock_redis: AsyncMock,
        fake_settings: SimpleNamespace,
        sample_token: StoredToken,
    ) -> None:
        stored_data: dict[str, str] = {}

        async def capture_hset(key: str, mapping: dict[str, str]) -> int:
            stored_data.update(mapping)
            return len(mapping)

        mock_redis.hset.side_effect = capture_hset
        mock_redis.hgetall.return_value = stored_data

        with (
            patch("app.auth.token_storage.get_redis", return_value=mock_redis),
            patch("app.auth.token_storage.settings", fake_settings),
        ):
            await store_token("user-123", sample_token)
            result = await get_token("user-123")

        assert result == sample_token
