"""
Simple helpers for generating secure one-time tokens used in
verification and refresh flows.
"""
import secrets


def generate_secure_token(length: int = 48) -> str:
    """
    Create a URL-safe token string.

    Args:
        length: Number of bytes to base the token on before URL-safe encoding.

    Returns:
        A URL-safe string suitable for use as tokens.
    """
    return secrets.token_urlsafe(length)
