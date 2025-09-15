# send_json_mail.py
import os, ssl, json, smtplib, requests
from email.message import EmailMessage

API_URL = "https://get-wbgt.onrender.com/extract_all?url=https://www.wbgt.env.go.jp/graph_ref_td.php%3Fregion=10%26prefecture=82%26point=82056"

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
TO_ADDR   = os.getenv("TO_ADDR")

def fetch_wbgt() -> dict:
    r = requests.get(API_URL, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    return r.json()

def send_json(data: dict, filename="wbgt.json"):
    msg = EmailMessage()
    msg["Subject"] = "[WBGT JSON] auto"
    msg["From"] = SMTP_USER
    msg["To"] = TO_ADDR
    msg.set_content("WBGT latest JSON attached.")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    msg.add_attachment(payload, maintype="application", subtype="json", filename=filename)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

if __name__ == "__main__":
    data = fetch_wbgt()
    send_json(data, filename="point_82056.json")
