from __future__ import annotations


class EmailService:
    def send_invite(self, email: str, invite_link: str) -> None:
        print(f"📧 MOCK EMAIL TO {email}: {invite_link}")
