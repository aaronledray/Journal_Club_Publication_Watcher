"""
Weekly email digest sender. Sends via Gmail SMTP_SSL using an App Password.

Reads credentials from environment variables (populated from GitHub Actions
secrets at run time): GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Tuple

from core.paper_processor import sort_papers_by_date

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
REQUIRED_ENV_VARS = ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "RECIPIENT_EMAIL")


def load_smtp_env() -> Dict[str, str]:
    """Read + validate required env vars. Raises RuntimeError listing missing names."""
    values = {name: os.environ.get(name, "").strip() for name in REQUIRED_ENV_VARS}
    missing = [name for name, val in values.items() if not val]
    if missing:
        raise RuntimeError(
            "--notify-email requires environment variable(s) that are missing/empty: "
            f"{', '.join(missing)}. Set them as GitHub Actions repo secrets "
            "(or export them locally before running with --notify-email)."
        )
    return values


def build_email_subject(new_count: int, date_range: Tuple[str, str]) -> str:
    start, end = date_range
    if new_count == 0:
        return f"Journal Watcher: no new papers this week ({start} to {end})"
    plural = "paper" if new_count == 1 else "papers"
    return f"Journal Watcher: {new_count} new {plural} ({start} to {end})"


def _authors_str(authors: List[str], limit: int = 4) -> str:
    authors = [a for a in (authors or []) if a and a != "No authors available"]
    if not authors:
        return "Unknown authors"
    if len(authors) > limit:
        return f"{', '.join(authors[:limit])}, et al."
    return ", ".join(authors)


def build_plaintext_body(components: List[Dict[str, Any]], date_range: Tuple[str, str]) -> str:
    start, end = date_range
    lines = [f"Journal Watcher weekly digest ({start} to {end})", ""]
    if not components:
        lines.append("No new papers matched your criteria this week.")
        return "\n".join(lines)

    ordered = sort_papers_by_date(components, reverse=True)
    for i, c in enumerate(ordered, 1):
        lines += [
            f"{i}. {c.get('Title', 'No title available')}",
            f"   {_authors_str(c.get('Authors'))}",
            f"   {c.get('Journal', 'Unknown journal')} — {c.get('Date', 'Unknown date')}",
        ]
        link = c.get("Link", "No link available")
        if link != "No link available":
            lines.append(f"   {link}")
        lines.append("")
    return "\n".join(lines)


def build_html_body(components: List[Dict[str, Any]], date_range: Tuple[str, str]) -> str:
    start, end = date_range
    if not components:
        body = "<p>No new papers matched your criteria this week.</p>"
    else:
        ordered = sort_papers_by_date(components, reverse=True)
        cards = []
        for c in ordered:
            title = c.get("Title", "No title available")
            link = c.get("Link", "No link available")
            title_html = (
                f'<a href="{link}" style="color:#1a5276;text-decoration:none;">{title}</a>'
                if link != "No link available" else title
            )
            cards.append(f"""
            <div style="margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid #e0e0e0;">
              <div style="font-size:16px;font-weight:600;margin-bottom:4px;">{title_html}</div>
              <div style="font-size:13px;color:#444;">{_authors_str(c.get('Authors'))}</div>
              <div style="font-size:13px;color:#777;">{c.get('Journal', 'Unknown journal')} &middot; {c.get('Date', 'Unknown date')} &middot; {c.get('Source', '')}</div>
            </div>""")
        body = "".join(cards)

    return f"""<html><body style="font-family:-apple-system,Helvetica,Arial,sans-serif;color:#222;">
      <h2 style="margin-bottom:4px;">Journal Watcher weekly digest</h2>
      <div style="color:#777;margin-bottom:20px;">{start} to {end}</div>
      {body}
    </body></html>"""


def send_digest_email(new_components: List[Dict[str, Any]], date_range: Tuple[str, str]) -> None:
    """
    Always sends an email - either the digest of new papers, or a short
    "no new papers this week" notice. Raises on missing env vars or SMTP
    failure; caller must NOT mark papers seen if this raises, so a failed
    send never silently drops a paper from future digests.
    """
    creds = load_smtp_env()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = build_email_subject(len(new_components), date_range)
    msg["From"] = creds["GMAIL_ADDRESS"]
    msg["To"] = creds["RECIPIENT_EMAIL"]
    msg.attach(MIMEText(build_plaintext_body(new_components, date_range), "plain"))
    msg.attach(MIMEText(build_html_body(new_components, date_range), "html"))

    print(f'   Sending email via {SMTP_HOST}:{SMTP_PORT} to {creds["RECIPIENT_EMAIL"]}...')
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(creds["GMAIL_ADDRESS"], creds["GMAIL_APP_PASSWORD"])
        server.sendmail(creds["GMAIL_ADDRESS"], [creds["RECIPIENT_EMAIL"]], msg.as_string())
    print("   Email sent successfully.")
