"""Notification system for Campaign Respond pipeline."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def send_notification(config: dict, message: str):
    """Send notification via configured channels.

    Args:
        config: Campaign configuration dict
        message: Notification message text
    """
    notifications = config.get("notifications", {})
    requester = config.get("requester", {})

    # Log to comms ledger
    _log_to_ledger(message, requester)

    # iMessage (if on homelab and enabled)
    if notifications.get("imessage_enabled") and _is_homelab():
        phone = requester.get("phone", "")
        if phone:
            _send_imessage(phone, message)

    # Email (if enabled)
    if notifications.get("email_enabled"):
        email = requester.get("email", "")
        if email:
            _send_email(email, "Campaign Respond Update", message)

    # SMS via Twilio (if enabled)
    if notifications.get("sms_enabled"):
        phone = requester.get("phone", "")
        if phone:
            _send_sms(phone, message)


def _log_to_ledger(message: str, requester: dict):
    """Append to comms ledger."""
    ledger_path = BASE_DIR / "state" / "comms-ledger.json"

    if ledger_path.exists():
        with open(ledger_path) as f:
            ledger = json.load(f)
    else:
        ledger = {"entries": []}

    ledger["entries"].append({
        "timestamp": datetime.now().isoformat(),
        "type": "notification",
        "message": message,
        "recipient": requester.get("name", "unknown"),
    })

    with open(ledger_path, "w") as f:
        json.dump(ledger, f, indent=2)


def _is_homelab() -> bool:
    """Check if running inside Teddy's homelab."""
    return os.path.exists("/Users/ctgiii/homelab/state/system-state.json")


def _send_imessage(phone: str, message: str):
    """Send iMessage via homelab imsg tool."""
    try:
        subprocess.run(
            ["/opt/homebrew/bin/imsg", "send", "--to", phone, "--text", message],
            capture_output=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Silent fail — not critical


def _send_email(to: str, subject: str, body: str):
    """Send email via SMTP."""
    try:
        import smtplib
        from email.mime.text import MIMEText

        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")

        host = os.getenv("SMTP_HOST", "127.0.0.1")
        port = int(os.getenv("SMTP_PORT", "1025"))
        user = os.getenv("SMTP_USER", "")
        from_addr = os.getenv("SMTP_FROM", user)

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to

        with smtplib.SMTP(host, port) as server:
            if user:
                server.login(user, os.getenv("SMTP_PASS", ""))
            server.sendmail(from_addr, [to], msg.as_string())
    except Exception:
        pass  # Silent fail — not critical


def _send_sms(phone: str, message: str):
    """Send SMS via Twilio."""
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")

        sid = os.getenv("TWILIO_SID")
        token = os.getenv("TWILIO_TOKEN")
        from_num = os.getenv("TWILIO_FROM")

        if not all([sid, token, from_num]):
            return

        import httpx
        httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            auth=(sid, token),
            data={"From": from_num, "To": phone, "Body": message},
            timeout=30,
        )
    except Exception:
        pass  # Silent fail — not critical
