#!/usr/bin/env python3
"""Send welcome email to the campaign requester."""

import json
import os
import smtplib
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def send_welcome():
    """Send welcome email or open in browser as fallback."""
    config_path = BASE_DIR / "config" / "campaign.json"
    if not config_path.exists():
        print("No campaign config found.")
        return

    with open(config_path) as f:
        config = json.load(f)

    requester = config.get("requester", {})
    candidate = config.get("candidate", {})

    to_email = requester.get("email", "")
    requester_name = requester.get("name", "there")
    candidate_name = candidate.get("name", "your candidate")
    install_path = str(BASE_DIR)

    # Load and fill template
    template_path = BASE_DIR / "templates" / "welcome-email.html"
    if template_path.exists():
        html = template_path.read_text()
    else:
        html = f"<h1>Campaign Respond is Ready</h1><p>Hi {requester_name}, your bot team for {candidate_name} is set up at {install_path}.</p>"

    html = html.replace("{{requester_name}}", requester_name)
    html = html.replace("{{candidate_name}}", candidate_name)
    html = html.replace("{{install_path}}", install_path)

    # Try SMTP (Proton Bridge on homelab, or configured SMTP)
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "0"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    email_sent = False

    if to_email and smtp_host and smtp_port:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your Campaign Respond Bot Team is Ready"
            msg["From"] = smtp_from
            msg["To"] = to_email

            # Plain text version
            plain = f"""Hi {requester_name},

Your Campaign Respond bot team is now installed and ready to help {candidate_name}'s campaign respond to questionnaires.

Built by Teddy Galloway / Visionary Productions.
Housed on YOUR computer — your data stays with you.

HOW TO USE IT:

1. Open Terminal (Mac: Cmd+Space -> type "Terminal")
2. Type: cd {install_path}
3. Type: campaign-respond new ~/path/to/questionnaire.pdf
4. Check progress: campaign-respond status
5. Full command reference: campaign-respond help

Your install guide is at: {install_path}/docs/install-guide.md

— Campaign Respond by Visionary Productions"""

            msg.attach(MIMEText(plain, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_user:
                    smtp_pass = os.getenv("SMTP_PASS", "")
                    if smtp_pass:
                        server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())

            print(f"Welcome email sent to {to_email}")
            email_sent = True
        except Exception as e:
            print(f"Could not send email: {e}")

    # Fallback: save HTML and open in browser
    if not email_sent:
        fallback_path = BASE_DIR / "docs" / "welcome-email.html"
        fallback_path.write_text(html)
        print(f"  Welcome email saved to: {fallback_path}")

        try:
            webbrowser.open(f"file://{fallback_path}")
            print("  Opened in browser.")
        except Exception:
            print(f"  Open manually: {fallback_path}")


if __name__ == "__main__":
    send_welcome()
