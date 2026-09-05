import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

print(f"📧 Email: {EMAIL}")
print(f"🔑 Password: '{PASSWORD}' (length: {len(PASSWORD)})")

try:
    conn = imaplib.IMAP4_SSL("imap.gmail.com")
    conn.login(EMAIL, PASSWORD)
    conn.select("INBOX")
    result, data = conn.search(None, "ALL")
    print(f"✅ Success! You have {len(data[0].split())} emails.")
    conn.close()
except Exception as e:
    print(f"❌ Failed: {e}")