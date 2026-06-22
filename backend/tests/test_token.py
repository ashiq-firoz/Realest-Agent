"""
Property-based tests for token utilities.

Property 5: JWT Identity Round-Trip
Property 8: Share Token Uniqueness and Format
Validates: Requirements 2.1, 2.4, 2.5, 3.4
"""
import os
import re
import time

# Set required env vars before any app imports to prevent Settings validation failure.
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test_key")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")
os.environ.setdefault("DOMAIN_API_KEY", "test_domain_key")

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from app.utils.token import create_jwt, decode_jwt, generate_share_token  # noqa: E402

# URL-safe base64 characters: A-Z, a-z, 0-9, -, _
URL_SAFE_RE = re.compile(r'^[A-Za-z0-9\-_]+$')


# ---------------------------------------------------------------------------
# Property 8: Share Token Uniqueness and Format
# ---------------------------------------------------------------------------

def test_share_token_format_and_uniqueness():
    """Property 8: Share tokens are exactly 8 URL-safe chars, and 1000 tokens have no duplicates.

    **Validates: Requirements 3.4**
    """
    batch = [generate_share_token() for _ in range(1000)]

    for token in batch:
        assert len(token) == 8, f"Token '{token}' is not 8 chars (got {len(token)})"
        assert URL_SAFE_RE.match(token), (
            f"Token '{token}' contains non-URL-safe characters"
        )

    unique_count = len(set(batch))
    assert unique_count == 1000, (
        f"Duplicate tokens found: only {unique_count} unique tokens in 1000 samples"
    )


# ---------------------------------------------------------------------------
# Property 5: JWT Identity Round-Trip
# ---------------------------------------------------------------------------

@given(st.uuids())
@settings(max_examples=100)
def test_jwt_identity_round_trip(user_uuid):
    """Property 5: JWT sub claim round-trips back to the same user_id.

    Also asserts that exp - iat is within [86340, 86460] seconds (24 h ± 60 s)
    and that iat is close to the current time.

    **Validates: Requirements 2.1, 2.4, 2.5**
    """
    user_id = str(user_uuid)
    tier = "regular"

    before = int(time.time())
    token = create_jwt(user_id, tier)
    after = int(time.time())

    payload = decode_jwt(token)

    # sub must round-trip to the same user_id
    assert payload["sub"] == user_id

    # iat and exp must both be present
    assert "iat" in payload, "JWT payload missing 'iat' claim"
    assert "exp" in payload, "JWT payload missing 'exp' claim"

    # Token lifetime must be within [86340, 86460] seconds (24 h ± 60 s)
    delta = payload["exp"] - payload["iat"]
    assert 86340 <= delta <= 86460, (
        f"Token lifetime {delta}s is outside the expected [86340, 86460] range"
    )

    # iat should be bracketed by the timestamps taken before/after create_jwt
    assert before <= payload["iat"] <= after + 1, (
        f"iat={payload['iat']} is not within [{before}, {after + 1}]"
    )


@given(st.uuids(), st.sampled_from(["regular", "pro"]))
@settings(max_examples=50)
def test_jwt_tier_preserved(user_uuid, tier):
    """Property 5b: JWT tier claim is preserved after encode → decode round-trip.

    **Validates: Requirements 2.1, 2.4**
    """
    token = create_jwt(str(user_uuid), tier)
    payload = decode_jwt(token)

    assert payload["tier"] == tier, (
        f"Expected tier='{tier}' but got '{payload.get('tier')}'"
    )
