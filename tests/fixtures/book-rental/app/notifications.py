"""E-mail receipts."""

import smtplib
from email.message import EmailMessage

from app import config


def send_receipt(email, subject, body):
    message = EmailMessage()
    message["To"] = email
    message["From"] = "library@example.org"
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(config.SMTP_HOST, timeout=5) as smtp:
            smtp.send_message(message)
    except Exception:
        pass
