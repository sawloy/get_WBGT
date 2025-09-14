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

    r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    # ✅ 组合选择器：匹配所有 wbgt1 ~ wbgt5
    selector = ".wbgt1, .wbgt2, .wbgt3, .wbgt4, .wbgt5"
    elements = soup.select(selector)
    if not elements:
        return jsonify({"error": "no elements found"}), 404

    # 提取文本并转换为数字
    values = []
    for el in elements:
        txt = el.get_text(strip=True)
        try:
            values.append(float(txt))  # 转成 float，方便比较
        except ValueError:
            pass  # 万一不是数字就跳过

    if not values:
        return jsonify({"error": "no numeric values found"}), 404

    max_value = max(values)

    return jsonify({
        "values": values,   # 数组
        "max": max_value    # 最大值
    })
