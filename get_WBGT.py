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

    for el in elements:
        txt = el.get_text(strip=True)
        try:
            number = float(txt)
            values.append(number)
        except ValueError:
            # 没有数字 → 记为 0
            values.append(0.0)

    # 计算最大值及其位置
    max_value = max(values)
    max_index = values.index(max_value)  # 返回第一个最大值的位置 (从 0 开始)
    max_time = max_index * 3        # 用顺序乘以 3 估算几点

    return jsonify({
        "values": values,           # 全部值（空 → 0）
        "max": max_value,           # 最大值
        "max_index": max_index,     # 最大值在数组中的位置
        "max_time": f"{max_time}時"  # 对应时间（粗略）
    })
