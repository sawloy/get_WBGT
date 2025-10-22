# 引入必要模块
from flask import Flask, request, jsonify    # Flask：Web 框架；request 用于取参数；jsonify 用于返回 JSON 响应
import requests                              # requests：发送 HTTP 请求
from bs4 import BeautifulSoup                # BeautifulSoup：解析 HTML 内容
from flask_cors import CORS                  # CORS：解决跨域访问问题

# ---------------------------
# 初始化 Flask 应用
# ---------------------------
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 设置返回 JSON 时不转义非 ASCII 字符，保持 UTF-8 中文正常显示

# ---------------------------
# 开启跨域访问（CORS）
# ---------------------------
CORS(app, resources={
    r"/*": {   # 匹配所有路径
        "origins": [
            "*",  # 允许所有来源（开发调试阶段方便测试）
            # 以下是允许的正式来源（Excel、SharePoint、Office）
            "https://excel.officeapps.live.com",
            "https://*.officeapps.live.com",
            "https://*.sharepoint.com",
            "https://*.office.com",
        ]
    }
}, supports_credentials=False)  # 不携带认证信息（因为这里不需要登录）

@app.get("/extract_all")
def extract_all():
    # 1️⃣ 从请求参数中获取目标 URL（要爬的 WBGT 网页地址）
    url = request.args.get("url")
    if not url:
        # 如果没有提供 url 参数，返回错误信息 + 状态码 400
        return jsonify({"error": "url is required"}), 400

    # 2️⃣ 发送请求到目标网址
    r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})  # 模拟浏览器访问
    r.raise_for_status()   # 若返回码不是 200 会抛出异常
    soup = BeautifulSoup(r.text, "html.parser")  # 用 BeautifulSoup 解析 HTML

    # 3️⃣ 定义选择器，匹配页面中的 wbgt0 ~ wbgt5 这些 class 名的元素（每个时间段的 WBGT 值）
    selector = ".wbgt0, .wbgt1, .wbgt2, .wbgt3, .wbgt4, .wbgt5"
    elements = soup.select(selector)  # 获取所有匹配的元素
    if not elements:
        # 如果没找到，说明网页结构有变或参数错误
        return jsonify({"error": "no elements found"}), 404

    # 4️⃣ 提取每个元素中的数字值
    values = []
    for el in elements:
        txt = el.get_text(strip=True)  # 取文字并去掉空格
        try:
            number = float(txt)        # 转成数字
            values.append(number)
        except ValueError:
            values.append(0.0)         # 如果转失败（为空或异常字符）就用 0 填充

    # 5️⃣ 计算最大 WBGT 值
    max_value = max(values)

    # 6️⃣ 找到所有最大值对应的索引位置
    max_indices = [i for i, v in enumerate(values) if v == max_value]

    # 7️⃣ 把索引转换为时间。假设 wbgt0 对应 3时，wbgt1 对应 6时... 每个元素间隔 3 小时。
    max_times = [f"{(i+1) * 3}時" for i in max_indices]

    # 8️⃣ 返回 JSON 响应
    return jsonify({
        # "values": values,          # 如果你想查看完整 6 段数据，可取消注释
        "max": max_value,            # 最大 WBGT 值
        # "max_indices": max_indices, # 最大值所在的索引（调试用）
        "max_times": max_times       # 对应的时间（可能有多个）
    })
