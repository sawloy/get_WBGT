from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.get("/extract")
def extract():
    url = request.args.get("https://www.wbgt.env.go.jp/graph_ref_td.php?region=10&prefecture=82&point=82056")
    selector = request.args.get("#dataarea > table > tbody > tr:nth-child(3) > td > div > div.value.num_lv3 > span.present_num")
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
