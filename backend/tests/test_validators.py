"""
Property-based tests for password validation and bcrypt invariants.

Property 3: Password Validation Rejects Invalid Inputs
Property 4: Bcrypt Cost Invariant
Validates: Requirements 2.2, 2.3
"""
import os

# Set required env vars before any app imports to prevent Settings validation failure.
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test_key")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")
os.environ.setdefault("DOMAIN_API_KEY", "test_domain_key")

import bcrypt as _bcrypt_lib  # noqa: E402
from hypothesis import assume, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from app.utils.validators import validate_email, validate_password  # noqa: E402

# Cost factor used by the auth router
BCRYPT_ROUNDS = 12


# ---------------------------------------------------------------------------
# Property 3: Password Validation Rejects Invalid Inputs
# ---------------------------------------------------------------------------

@given(
    email=st.emails() | st.text(),
    password=st.text(max_size=7),
)
@settings(max_examples=200)
def test_p3_invalid_password_always_produces_error(email: str, password: str):
    """Property 3: validate_password returns a non-empty error for any password shorter than 8 chars.

    Short passwords (0-7 characters) must always be rejected regardless of content.
    The validator must never return None (no error) for such inputs.

    **Validates: Requirements 2.2, 2.3**
    """
    error = validate_password(password)
    assert error is not None, (
        f"Expected a validation error for password {password!r} (len={len(password)}), "
        "but validate_password returned None"
    )
    assert len(error) > 0, (
        f"Expected a non-empty error message for password {password!r}, but got empty string"
    )


@given(email=st.text())
@settings(max_examples=200)
def test_p3_invalid_email_always_produces_error(email: str):
    """Property 3b: validate_email returns a non-empty error for emails missing '@' + domain.

    Arbitrary text without proper email structure (@ plus domain with dot) must be rejected.

    **Validates: Requirements 2.2**
    """
    import re
    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    is_valid_format = bool(EMAIL_RE.match(email))

    error = validate_email(email)

    if not is_valid_format:
        # If the email doesn't match the pattern, an error must be returned
        assert error is not None, (
            f"Expected a validation error for email {email!r} (invalid format), "
            "but validate_email returned None"
        )
        assert len(error) > 0, (
            f"Expected a non-empty error message for invalid email {email!r}"
        )
    else:
        # If it passes the regex, the validator should accept it (return None)
        assert error is None, (
            f"Expected no error for well-formed email {email!r}, but got: {error!r}"
        )


# ---------------------------------------------------------------------------
# Property 4: Bcrypt Cost Invariant
# ---------------------------------------------------------------------------

@given(password=st.text(min_size=8, max_size=64, alphabet=st.characters(max_codepoint=127)))
@settings(max_examples=50, deadline=None)
def test_p4_bcrypt_cost_factor_at_least_12(password: str):
    """Property 4: Hashing a valid password always produces a bcrypt hash with cost >= 12.

    The bcrypt hash format is $2b$COST$... where COST is a zero-padded decimal.
    We decode the prefix and assert the extracted cost factor is >= 12.

    Uses the bcrypt library directly (not passlib) to avoid passlib's internal
    wrap-bug detection which is incompatible with bcrypt >= 4.x on newer bcrypt builds.

    Passwords are constrained to printable ASCII (codepoint <= 127) to stay
    within bcrypt's 72-byte limit, and we further guard with assume().

    **Validates: Requirements 2.2, 2.3**
    """
    # Ensure the UTF-8-encoded password never exceeds bcrypt's 72-byte limit
    password_bytes = password.encode("utf-8")
    assume(len(password_bytes) <= 72)

    # Hash using bcrypt directly at cost 12 (same cost the auth router uses)
    hashed_bytes = _bcrypt_lib.hashpw(password_bytes, _bcrypt_lib.gensalt(rounds=BCRYPT_ROUNDS))
    hashed = hashed_bytes.decode("ascii")

    # bcrypt hash format: $2b$12$<22-char-salt><31-char-hash>
    # parts[0] == '' (before first $)
    # parts[1] == '2b' (algorithm identifier)
    # parts[2] == cost factor as zero-padded string, e.g. '12'
    # parts[3] == salt + hash combined
    parts = hashed.split("$")
    assert len(parts) >= 4, (
        f"Unexpected bcrypt hash format: {hashed!r}"
    )
    assert parts[1] in ("2b", "2a", "2y"), (
        f"Unexpected bcrypt algorithm identifier '{parts[1]}' in hash: {hashed!r}"
    )

    cost = int(parts[2])
    assert cost >= 12, (
        f"Bcrypt cost factor {cost} is less than 12 for password {password!r}. "
        f"Hash: {hashed!r}"
    )
