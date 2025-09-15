# send_json_mail.py
import os, ssl, json, smtplib, time, sys, requests
from email.message import EmailMessage

API_URL   = "https://get-wbgt.onrender.com/extract_all?url=https://www.wbgt.env.go.jp/graph_ref_td.php%3Fregion=10%26prefecture=82%26point=82056"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
TO_ADDR   = os.getenv("TO_ADDR")

def log(s): print(s, flush=True)

def fetch_wbgt(timeout=30) -> dict:
    log(f"[fetch] GET {API_URL}")
    r = requests.get(API_URL, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
    log(f"[fetch] status={r.status_code}")
    r.raise_for_status()
    try:
        data = r.json()
    except Exception as e:
        snippet = r.text[:300].replace("\n"," ")
        raise RuntimeError(f"JSON decode failed: {e}; body head: {snippet}")
    if "max" not in data or "max_times" not in data:
        raise RuntimeError(f"JSON missing keys: got {list(data.keys())}")
    return data

def send_json(data: dict, filename="point_82056.json"):
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, TO_ADDR]):
        raise RuntimeError("Missing SMTP env (SMTP_HOST/PORT/USER/PASS or TO_ADDR).")
    msg = EmailMessage()
    msg["Subject"] = "[WBGT JSON] auto"
    msg["From"]    = SMTP_USER
    msg["To"]      = TO_ADDR
    msg.set_content("WBGT latest JSON attached.")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    msg.add_attachment(payload, maintype="application", subtype="json", filename=filename)
    log(f"[smtp] connecting to {SMTP_HOST}:{SMTP_PORT} as {SMTP_USER}")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    log("[smtp] sent ok")

def main():
    max_attempts = 3
    delay = 20
    for i in range(1, max_attempts+1):
        try:
            log(f"=== Attempt {i}/{max_attempts} ===")
            data = fetch_wbgt()
            log(f"[data] max={data.get('max')} max_times={data.get('max_times')}")
            send_json(data)
            log("=== Done ===")
            return 0
        except Exception as e:
            log(f"[error] {e}")
            if i < max_attempts:
                log(f"[retry] sleeping {delay}s ...")
                time.sleep(delay)
            else:
                log("[fail] all attempts failed")
                return 1

if __name__ == "__main__":
    sys.exit(main())
