"""
Email service for sending magic links.
In development mode, prints to console. In production, sends via SMTP.
"""

from app.config import settings


async def send_magic_link_email(email: str, token: str) -> bool:
    """
    Send magic link email to user.

    In development mode, prints the link to console.
    In production mode, sends via SMTP (not implemented yet).

    Args:
        email: Recipient email address
        token: Magic link token

    Returns:
        True if successful
    """
    link = f"{settings.BASE_URL}/auth/verify?token={token}"

    if settings.ENVIRONMENT == "development" or not settings.SMTP_HOST:
        # Development mode: print to console
        print()
        print("=" * 60)
        print(f"  MAGIC LINK LOGIN")
        print("=" * 60)
        print(f"  Email: {email}")
        print(f"  Link:  {link}")
        print("=" * 60)
        print()
        return True

    # Production mode: send via SMTP
    # TODO: Implement actual email sending with aiosmtplib
    # For now, still print to console as fallback
    print(f"[EMAIL] Would send magic link to {email}: {link}")
    return True
