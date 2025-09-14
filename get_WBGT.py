from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False   # 关键：返回 JSON 时不要把非 ASCII 字符转义

@app.get("/extract")
def extract():
    url = request.args.get("url")
    selector = request.args.get("selector")
    if not url or not selector:
        return jsonify({"error": "url and selector are required"}), 400

    r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    el = soup.select_one(selector)
    if not el:
        return jsonify({"error": "selector not found"}), 404

    text = el.get_text(strip=True)
    return jsonify({"text": text})
