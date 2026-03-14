"""OAuth 2.0 authentication for Dida365 Open API."""

from __future__ import annotations

import json
import logging
import os
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

logger = logging.getLogger(__name__)

# Dida365 OAuth endpoints
AUTH_URL = "https://dida365.com/oauth/authorize"
TOKEN_URL = "https://dida365.com/oauth/token"
REDIRECT_URI = "http://localhost:18365/callback"

# Config paths — use ~/.dida365 to avoid macOS ~/.config ownership issues
CONFIG_DIR = Path.home() / ".dida365"
TOKEN_FILE = CONFIG_DIR / "token.json"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler to capture OAuth callback."""

    auth_code: str | None = None
    state: str | None = None

    def do_GET(self) -> None:
        """Handle GET request from OAuth redirect."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            OAuthCallbackHandler.state = params.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("认证成功！请返回终端继续操作。".encode())
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"认证失败: {error}".encode())

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default HTTP server logging."""


def _ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_token(token_data: dict) -> None:
    """Save OAuth token to disk with secure permissions."""
    _ensure_config_dir()
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
    os.chmod(TOKEN_FILE, 0o600)
    logger.debug("Token saved to %s", TOKEN_FILE)


def load_token() -> dict | None:
    """Load OAuth token from disk. Returns None if not found."""
    if not TOKEN_FILE.exists():
        return None
    try:
        data = json.loads(TOKEN_FILE.read_text())
        if "access_token" in data:
            return data
    except (json.JSONDecodeError, KeyError):
        logger.warning("Invalid token file, ignoring")
    return None


def delete_token() -> bool:
    """Delete stored OAuth token. Returns True if deleted."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        return True
    return False


def get_access_token() -> str | None:
    """Get the current access token string. Returns None if not authenticated."""
    token_data = load_token()
    if token_data is None:
        return None
    return token_data.get("access_token")


def oauth_login(client_id: str, client_secret: str) -> dict:
    """Perform OAuth 2.0 authorization code flow.

    Opens browser for user authorization and starts local server to capture callback.
    Returns token data dict on success.
    Raises RuntimeError on failure.
    """
    state = secrets.token_urlsafe(16)

    # Build authorization URL
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "tasks:read tasks:write",
        "state": state,
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    # Reset handler state
    OAuthCallbackHandler.auth_code = None
    OAuthCallbackHandler.state = None

    # Start local callback server
    server = HTTPServer(("localhost", 18365), OAuthCallbackHandler)
    server_thread = Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    # Open browser for authorization
    webbrowser.open(auth_url)

    # Wait for callback
    server_thread.join(timeout=120)
    server.server_close()

    if OAuthCallbackHandler.auth_code is None:
        msg = "未收到授权回调，请重试"
        raise RuntimeError(msg)

    if OAuthCallbackHandler.state != state:
        msg = "OAuth state 不匹配，可能存在安全风险"
        raise RuntimeError(msg)

    # Exchange code for token
    token_data = _exchange_code(
        code=OAuthCallbackHandler.auth_code,
        client_id=client_id,
        client_secret=client_secret,
    )

    # Save credentials alongside token for future refresh
    token_data["client_id"] = client_id
    token_data["client_secret"] = client_secret
    save_token(token_data)

    return token_data


def _exchange_code(code: str, client_id: str, client_secret: str) -> dict:
    """Exchange authorization code for access token."""
    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        auth=(client_id, client_secret),
        timeout=30,
    )

    if response.status_code != 200:
        msg = f"Token 交换失败 (HTTP {response.status_code}): {response.text}"
        raise RuntimeError(msg)

    return response.json()


def refresh_access_token() -> dict | None:
    """Attempt to refresh the access token using stored refresh token.

    Returns updated token data on success, None on failure.
    """
    token_data = load_token()
    if token_data is None:
        return None

    refresh_token = token_data.get("refresh_token")
    client_id = token_data.get("client_id")
    client_secret = token_data.get("client_secret")

    if not all([refresh_token, client_id, client_secret]):
        return None

    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(client_id, client_secret),
            timeout=30,
        )
        if response.status_code == 200:
            new_data = response.json()
            new_data["client_id"] = client_id
            new_data["client_secret"] = client_secret
            save_token(new_data)
            return new_data
    except httpx.HTTPError:
        logger.warning("Token refresh failed")

    return None
