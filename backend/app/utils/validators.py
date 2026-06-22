"""Input validation helpers used by auth routes."""
import re
from typing import Optional


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> Optional[str]:
    """
    Return an error message if email is invalid, else None.
    Checks for @ symbol and at least one dot in the domain part.
    """
    if not email or not EMAIL_RE.match(email):
        return "Invalid email address"
    return None


def validate_password(password: str) -> Optional[str]:
    """
    Return an error message if password is invalid, else None.
    Password must be at least 8 characters.
    """
    if not password or len(password) < 8:
        return "Password must be at least 8 characters"
    return None
