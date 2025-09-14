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
            values.append(0.0)  # 空值用 0 填充

    max_value = max(values)

    # 找到所有最大值的索引
    max_indices = [i for i, v in enumerate(values) if v == max_value]

    # 把索引转换成时间（索引 * 3 小时）
    max_times = [f"{(i+1) * 3}時" for i in max_indices]

    return jsonify({
        "values": values,        # 全部值
        "max": max_value,        # 最大值
        "max_indices": max_indices,  # 所有最大值的位置
        "max_times": max_times       # 所有最大值对应的时间（数组）
    })
