"""
Property tests for Settings validation.

Property 23: Environment Variable Startup Validation
Validates: Requirements 10.3
"""
import os
from unittest.mock import patch

os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("DOMAIN_API_KEY", "test")
os.environ.setdefault("RAPIDAPI_KEY", "test")
os.environ.setdefault("NEXTAUTH_SECRET", "test_secret_min_32_characters_long_abc")

from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from app.config import Settings

# ---------------------------------------------------------------------------
# Required Environment Variables
# ---------------------------------------------------------------------------

# DOMAIN_API_KEY / PROPERTYLENS_API_KEY are now OPTIONAL (Domain dropped;
# PropertyLens has a mock fallback), so they are not part of the required set.
REQUIRED_VARS = [
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "REDIS_URL",
    "GEMINI_API_KEY",
    "RAPIDAPI_KEY",
    "NEXTAUTH_SECRET",
]

# We must ensure that the base environment passed to the mock contains
# valid values for all required variables, so we only fail on the ones
# we explicitly remove.
VALID_ENV = {
    "POSTGRES_DB": "test_db",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password",
    "REDIS_URL": "redis://localhost:6379/0",
    "GEMINI_API_KEY": "valid_key",
    "RAPIDAPI_KEY": "valid_key",
    "NEXTAUTH_SECRET": "test_secret_min_32_characters_long_abc",
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@given(st.sets(st.sampled_from(REQUIRED_VARS), min_size=1))
def test_p23_environment_variable_startup_validation(missing_vars):
    """Property 23: Environment Variable Startup Validation.
    
    If any subset of required environment variables is missing, Settings()
    must raise a ValidationError mentioning at least one missing variable.
    """
    # Create a clean mock environment from VALID_ENV, removing missing_vars
    mock_env = {k: v for k, v in VALID_ENV.items() if k not in missing_vars}
    
    with patch.dict(os.environ, mock_env, clear=True):
        try:
            # _env_file=None so the test validates purely against the patched
            # environment and is not satisfied by a local .env file.
            Settings(_env_file=None)
            assert False, f"Expected ValidationError when missing {missing_vars}"
        except ValidationError as e:
            error_msg = str(e).lower()
            # Assert that at least one of the missing vars is mentioned in the error
            # Pydantic validation errors list the missing fields.
            found_missing = any(var.lower() in error_msg for var in missing_vars)
            assert found_missing, f"Expected error to mention one of {missing_vars}, got: {error_msg}"
