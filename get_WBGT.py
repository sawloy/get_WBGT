from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 保持 UTF-8

@app.get("/extract_all")
def extract_all():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400

    r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # ✅ 组合选择器，匹配 wbgt0 ~ wbgt5
    selector = ".wbgt0, .wbgt1, .wbgt2, .wbgt3, .wbgt4, .wbgt5"
    elements = soup.select(selector)
    if not elements:
        return jsonify({"error": "no elements found"}), 404

    values = []
    numeric_values = []

    for el in elements:
        txt = el.get_text(strip=True)

        # 即使为空也 append，只是保留 None
        if txt == "":
            values.append(None)
        else:
            try:
                number = float(txt)
                values.append(number)
                numeric_values.append(number)
            except ValueError:
                # 如果不是数字，保留原始字符串
                values.append(txt)

    if not numeric_values:
        return jsonify({"values": values, "max": None})

    return jsonify({
        "values": values,       # 保留每个位置的值，空用 None
        "max": max(numeric_values)  # 只从数字里找最大值
    })
