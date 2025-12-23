from __future__ import annotations

from fastapi_mail import FastMail, MessageSchema, MessageType
from ..core.config import get_mail_config, get_settings


class EmailService:
    """Email service for sending invitations and notifications."""

    def __init__(self):
        self.mail_config = get_mail_config()
        self.settings = get_settings()

    async def send_invite(self, email: str, token: str, org_name: str) -> None:
        """
        Send an invitation email to a user.

        Args:
            email: Recipient email address
            token: Invitation token
            org_name: Name of the organization
        """
        # Construct the invitation link
        invite_link = f"{self.settings.FRONTEND_URL}/join?token={token}"

        # Create the email message
        message = MessageSchema(
            subject="Invitation to Ceras Security",
            recipients=[email],
            template_body={"link": invite_link, "org_name": org_name},
            subtype=MessageType.html,
        )

        # Send the email
        fm = FastMail(self.mail_config)
        await fm.send_message(message, template_name="invitation.html")
