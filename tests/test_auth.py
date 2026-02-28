"""Tests for dida.auth module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from dida.auth import delete_token, get_access_token, load_token, save_token


@pytest.fixture
def tmp_config(tmp_path):
    """Override config paths to use temp directory."""
    token_file = tmp_path / "token.json"
    config_dir = tmp_path
    with (
        patch("dida.auth.TOKEN_FILE", token_file),
        patch("dida.auth.CONFIG_DIR", config_dir),
    ):
        yield token_file


class TestTokenStorage:
    """Tests for token save/load/delete operations."""

    def test_save_and_load_token(self, tmp_config: Path) -> None:
        token_data = {"access_token": "test123", "refresh_token": "refresh456"}
        save_token(token_data)

        loaded = load_token()
        assert loaded is not None
        assert loaded["access_token"] == "test123"

    def test_load_token_not_found(self, tmp_config: Path) -> None:
        assert load_token() is None

    def test_load_token_invalid_json(self, tmp_config: Path) -> None:
        tmp_config.write_text("not valid json")
        assert load_token() is None

    def test_load_token_missing_access_token(self, tmp_config: Path) -> None:
        tmp_config.write_text(json.dumps({"refresh_token": "only_refresh"}))
        assert load_token() is None

    def test_delete_token(self, tmp_config: Path) -> None:
        save_token({"access_token": "test"})
        assert delete_token() is True
        assert not tmp_config.exists()

    def test_delete_token_not_found(self, tmp_config: Path) -> None:
        assert delete_token() is False

    def test_get_access_token(self, tmp_config: Path) -> None:
        save_token({"access_token": "my_token"})
        assert get_access_token() == "my_token"

    def test_get_access_token_none(self, tmp_config: Path) -> None:
        assert get_access_token() is None

    def test_token_file_permissions(self, tmp_config: Path) -> None:
        save_token({"access_token": "test"})
        mode = tmp_config.stat().st_mode & 0o777
        assert mode == 0o600
