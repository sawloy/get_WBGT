from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 保持 UTF-8

@app.get("/extract")
def extract():
    url = request.args.get("url")
    selector = request.args.get("selector")
    if not url or not selector:
        return jsonify({"error": "url and selector are required"}), 400

    r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    # ✅ 改成 select() 获取所有匹配的元素
    elements = soup.select(selector)
    if not elements:
        return jsonify({"error": "selector not found"}), 404

    # 提取每个元素的纯文本，去掉多余空格
    texts = [el.get_text(strip=True) for el in elements]

    # 返回 JSON 数组
    return jsonify({"results": texts})
