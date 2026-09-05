import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from agents.base_agent import BaseAgent
import os
import time

class EmailAgent(BaseAgent):
    name = "email_agent"

    def __init__(self):
        self.email = os.getenv("EMAIL_ADDRESS", "").strip()
        self.password = os.getenv("EMAIL_PASSWORD", "").strip()
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com").strip()
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()
        self.conn = None

    def _connect_imap(self):
        try:
            conn = imaplib.IMAP4_SSL(self.imap_server)
            conn.login(self.email, self.password)
            conn.select("INBOX")
            self.conn = conn
            return conn
        except Exception as e:
            print(f"❌ IMAP connection failed: {e}")
            return None

    def _get_connection(self):
        if self.conn is None:
            return self._connect_imap()
        try:
            self.conn.noop()
            return self.conn
        except Exception:
            self.conn = None
            return self._connect_imap()

    def fetch_recent_emails(self, limit=5):
        try:
            conn = self._get_connection()
            if conn is None:
                return {"success": False, "agent": self.name, "message": "IMAP connection failed."}
            result, data = conn.search(None, "ALL")
            if result != "OK":
                return {"success": False, "agent": self.name, "message": f"Search failed: {data}"}
            email_ids = data[0].split()
            recent_ids = email_ids[-limit:] if email_ids else []
            emails = []
            for eid in recent_ids:
                result, msg_data = conn.fetch(eid, "(RFC822)")
                # --- Robust extraction of raw email bytes ---
                raw_email = None
                if msg_data and len(msg_data) > 0:
                    if isinstance(msg_data[0], tuple) and len(msg_data[0]) >= 2:
                        raw_email = msg_data[0][1]   # bytes
                    elif isinstance(msg_data[0], bytes):
                        raw_email = msg_data[0]
                    else:
                        # fallback: concatenate all bytes parts
                        raw_email = b''.join([part for part in msg_data if isinstance(part, bytes)])
                if not raw_email or not isinstance(raw_email, bytes):
                    continue
                msg = email.message_from_bytes(raw_email)
                subject = msg["subject"] or "(no subject)"
                from_ = msg["from"] or "unknown"
                date = msg["date"] or "unknown"
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors='ignore')
                emails.append({
                    "subject": subject[:100],
                    "from": from_,
                    "date": date,
                    "body": body[:200] + ("..." if len(body) > 200 else "")
                })
            return {"success": True, "agent": self.name, "action": "fetch_emails", "count": len(emails), "emails": emails}
        except Exception as e:
            return {"success": False, "agent": self.name, "message": f"Failed to fetch emails: {str(e)}"}

    def send_email(self, to, subject, body):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            server = smtplib.SMTP_SSL(self.smtp_server, 465)
            server.login(self.email, self.password)
            server.sendmail(self.email, to, msg.as_string())
            server.quit()
            return {"success": True, "agent": self.name, "action": "send_email", "to": to, "subject": subject}
        except Exception as e:
            return {"success": False, "agent": self.name, "message": f"Send failed: {str(e)}"}

    def execute(self, command: str) -> dict:
        command_lower = command.lower()
        if "check email" in command_lower or "read email" in command_lower:
            return self.fetch_recent_emails()
        elif "send email" in command_lower:
            parts = command.split("send email", 1)[1].strip()
            try:
                if "subject" not in parts or "body" not in parts:
                    return {"success": False, "agent": self.name, "message": "Use: send email to <address> subject <subject> body <body>"}
                to_part = parts.split("subject", 1)[0].strip().replace("to ", "").strip()
                rest = parts.split("subject", 1)[1].strip()
                subject_part = rest.split("body", 1)[0].strip()
                body_part = rest.split("body", 1)[1].strip()
                return self.send_email(to_part, subject_part, body_part)
            except Exception as e:
                return {"success": False, "agent": self.name, "message": f"Parsing error: {str(e)}"}
        else:
            return {"success": False, "agent": self.name, "message": "Email Agent: Command not understood."}