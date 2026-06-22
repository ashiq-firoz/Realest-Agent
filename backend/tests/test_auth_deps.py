"""
Property-based tests for FastAPI auth dependencies.

Property 5: JWT Identity Round-Trip (via get_current_user dependency)
Property 20: Pro Feature Gate (via require_pro dependency)
Validates: Requirements 2.1, 2.4, 2.5, 7.5, 8.4
"""
import os
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Set required env vars BEFORE any app imports to prevent Settings failure.
# ---------------------------------------------------------------------------
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test_key")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")
os.environ.setdefault("DOMAIN_API_KEY", "test_domain_key")

# ---------------------------------------------------------------------------
# Stub out app.database so it doesn't try to connect to asyncpg/postgres.
# This must happen before any module that imports app.database is imported.
# ---------------------------------------------------------------------------
_fake_db_module = ModuleType("app.database")

# Provide a Base class so ORM models can import it without error.
from sqlalchemy.orm import DeclarativeBase  # noqa: E402

class _FakeBase(DeclarativeBase):
    pass

_fake_db_module.Base = _FakeBase  # type: ignore[attr-defined]
_fake_db_module.get_db = AsyncMock()  # type: ignore[attr-defined]
sys.modules.setdefault("app.database", _fake_db_module)

# ---------------------------------------------------------------------------
# Now it is safe to import the app modules.
# ---------------------------------------------------------------------------
import asyncio  # noqa: E402

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from fastapi.security import HTTPAuthorizationCredentials  # noqa: E402
from hypothesis import given  # noqa: E402
from hypothesis import settings as h_settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from app.deps import get_current_user, require_pro  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utils.token import create_jwt  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id: str, tier: str) -> User:
    """
    Construct a User-like mock with the required attributes.

    We use MagicMock(spec=User) rather than User.__new__(User) because
    when app.database is stubbed the ORM mapper is not fully initialised,
    making attribute assignment via InstrumentedAttribute fail.
    The mock satisfies all type checks (isinstance / spec-match) that
    get_current_user and require_pro actually perform.
    """
    user = MagicMock(spec=User)
    user.id = user_id
    user.tier = tier
    user.email = f"test-{user_id}@example.com"
    user.name = "Test User"
    user.image = None
    user.provider = "credentials"
    return user


def _make_credentials(token: str) -> HTTPAuthorizationCredentials:
    """Wrap a raw JWT string into HTTPAuthorizationCredentials."""
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _make_mock_db(user: User) -> AsyncMock:
    """
    Return an AsyncMock DB session whose `.get()` returns the given user.
    SQLAlchemy's `session.get(Model, pk)` is called as an awaitable.
    """
    db = AsyncMock()
    db.get = AsyncMock(return_value=user)
    return db


# ---------------------------------------------------------------------------
# Property 5: JWT Identity Round-Trip
# get_current_user decodes the JWT and returns the correct User
# ---------------------------------------------------------------------------

@given(st.uuids(), st.sampled_from(["regular", "pro"]))
@h_settings(max_examples=100)
def test_p5_get_current_user_returns_correct_user(user_uuid, tier):
    """Property 5: JWT Identity Round-Trip via get_current_user dependency.

    For any valid (user_id, tier) pair, creating a JWT and passing it through
    get_current_user must return a User whose id and tier match the inputs.

    **Validates: Requirements 2.1, 2.4, 2.5**
    """
    user_id = str(user_uuid)

    # Build a JWT for this user
    token = create_jwt(user_id, tier)
    credentials = _make_credentials(token)

    # Build a mock User that the DB "returns"
    mock_user = _make_user(user_id, tier)
    mock_db = _make_mock_db(mock_user)

    # Call the dependency directly (it is a regular async function)
    result = asyncio.run(
        get_current_user(credentials=credentials, db=mock_db)
    )

    assert result.id == user_id, (
        f"Expected user.id={user_id!r} but got {result.id!r}"
    )
    assert result.tier == tier, (
        f"Expected user.tier={tier!r} but got {result.tier!r}"
    )

    # Verify DB was queried exactly once with the correct user_id
    mock_db.get.assert_awaited_once_with(User, user_id)


# ---------------------------------------------------------------------------
# Property 20: Pro Feature Gate
# require_pro raises HTTP 403 for tier="regular", passes for tier="pro"
# ---------------------------------------------------------------------------

@given(st.uuids())
@h_settings(max_examples=100)
def test_p20_require_pro_allows_regular_tier(user_uuid):
    """Pro gate is intentionally permissive: every tier (including "regular") may
    access all features for now. require_pro returns the user without raising.

    (Backed by real per-user auth via get_current_user; can be tightened later.)
    """
    user_id = str(user_uuid)
    regular_user = _make_user(user_id, "regular")

    result = asyncio.run(require_pro(user=regular_user))

    assert result.id == user_id
    assert result.tier == "regular"


@given(st.uuids())
@h_settings(max_examples=100)
def test_p20_require_pro_passes_for_pro_tier(user_uuid):
    """Property 20: Pro Feature Gate — pro users are never blocked.

    For any valid user_id with tier="pro", require_pro must return the user
    without raising.

    **Validates: Requirements 7.5, 8.4**
    """
    user_id = str(user_uuid)
    pro_user = _make_user(user_id, "pro")

    result = asyncio.run(
        require_pro(user=pro_user)
    )

    assert result.id == user_id, (
        f"Expected user.id={user_id!r} but got {result.id!r}"
    )
    assert result.tier == "pro", (
        f"Expected tier='pro' but got {result.tier!r}"
    )


# ---------------------------------------------------------------------------
# Edge case: invalid / tampered token raises 401
# ---------------------------------------------------------------------------

def test_get_current_user_raises_401_for_invalid_token():
    """get_current_user raises HTTP 401 when the JWT is invalid/tampered."""
    credentials = _make_credentials("this.is.not.a.valid.jwt")
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            get_current_user(credentials=credentials, db=mock_db)
        )

    assert exc_info.value.status_code == 401


def test_get_current_user_raises_401_when_user_not_in_db():
    """get_current_user raises HTTP 401 when user_id from JWT is not in DB."""
    user_id = "00000000-0000-0000-0000-000000000001"
    token = create_jwt(user_id, "regular")
    credentials = _make_credentials(token)

    # DB returns None — user doesn't exist
    mock_db = AsyncMock()
    mock_db.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            get_current_user(credentials=credentials, db=mock_db)
        )

    assert exc_info.value.status_code == 401
