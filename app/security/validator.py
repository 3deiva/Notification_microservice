from app.config import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


class SecurityValidator:
    """Validates auth tokens and masks sensitive data."""

    VALID_TOKENS: set[str] = {settings.AUTH_TOKEN}

    @classmethod
    def validate_token(cls, token: str) -> bool:
        is_valid = token in cls.VALID_TOKENS
        if not is_valid:
            logger.warning("invalid_auth_token", token_prefix=token[:8] + "...")
        return is_valid

    @staticmethod
    def mask_phone(phone: str) -> str:
        if not phone or len(phone) < 4:
            return "****"
        return "*" * (len(phone) - 4) + phone[-4:]

    @staticmethod
    def mask_account(account: str) -> str:
        return account  # Already masked from source

    @staticmethod
    def mask_email(email: str) -> str:
        if not email or "@" not in email:
            return "****"
        user, domain = email.split("@", 1)
        masked_user = user[:2] + "*" * (len(user) - 2) if len(user) > 2 else "**"
        return f"{masked_user}@{domain}"
