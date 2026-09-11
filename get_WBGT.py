from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS

# 引入现有的邮件发送模块
import send_json_mail


# ---------------------------
# 初始化 Flask 应用
# ---------------------------
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


# ---------------------------
# CORS 设置
# ---------------------------
CORS(app, resources={
    r"/*": {
        "origins": [
            "*",
            "https://excel.officeapps.live.com",
            "https://*.officeapps.live.com",
            "https://*.sharepoint.com",
            "https://*.office.com",
        ]
    }
}, supports_credentials=False)


# ---------------------------
# WBGT 数据来源
# ---------------------------
WBGT_URL = (
    "https://www.wbgt.env.go.jp/graph_ref_td.php"
    "?region=10&prefecture=82&point=82056"
)


# ---------------------------
# 共通函数：抓取并解析 WBGT
# ---------------------------
def get_wbgt_data(url):
    """
    从环境省网页获取 WBGT 数据，
    返回 {"max": ..., "max_times": [...]}
    """

    r = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    selector = ".wbgt0, .wbgt1, .wbgt2, .wbgt3, .wbgt4, .wbgt5"
    elements = soup.select(selector)

    if not elements:
        raise RuntimeError("no elements found")

    values = []

    for el in elements:
        txt = el.get_text(strip=True)

        try:
            values.append(float(txt))
        except ValueError:
            values.append(0.0)

    max_value = max(values)

    max_indices = [
        i for i, v in enumerate(values)
        if v == max_value
    ]

    max_times = [
        f"{(i + 1) * 3}時"
        for i in max_indices
    ]

    return {
        "max": max_value,
        "max_times": max_times
    }


# ---------------------------
# 原有 API：返回 WBGT JSON
# ---------------------------
@app.get("/extract_all")
def extract_all():

    url = request.args.get("url")

    if not url:
        return jsonify({"error": "url is required"}), 400

    try:
        data = get_wbgt_data(url)
        return jsonify(data)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# ---------------------------
# 新 API：获取 WBGT 后发送邮件
# ---------------------------
@app.get("/send_mail")
def send_mail():

    try:
        # ① 直接访问环境省网页
        data = get_wbgt_data(WBGT_URL)

        # ② 把取得的数据交给原有邮件函数
        send_json_mail.send_json(data)

        # ③ 成功
        return jsonify({
            "status": "ok",
            "message": "WBGT mail sent successfully",
            "data": data
        }), 200

    except Exception as e:

        # 失败时把错误返回出来，方便 Render / cron-job.org 调试
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
