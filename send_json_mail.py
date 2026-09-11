# -------------------------------
# send_json_mail.py
# -------------------------------
# 功能：从 WBGT API 获取最新数据（JSON），然后通过邮件发送。
# 用于 GitHub Actions 定时任务中自动执行。
# -------------------------------

# 导入模块
import os, ssl, json, smtplib, time, sys, requests
from email.message import EmailMessage

# -------------------------------
# 1️⃣ 常量和配置
# -------------------------------

# WBGT 数据 API：指向你部署在 Render 上的接口
API_URL = (
    "https://get-wbgt.onrender.com/extract_all?"
    "url=https://www.wbgt.env.go.jp/graph_ref_td.php%3Fregion=10%26prefecture=82%26point=82056"
)

# 从环境变量读取 SMTP 配置（由 GitHub Secrets 提供）
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")  # 邮件服务器主机（默认 Gmail）
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))        # SMTP 端口号（587 = STARTTLS）
SMTP_USER = os.getenv("SMTP_USER")                    # 发件人邮箱账号
SMTP_PASS = os.getenv("SMTP_PASS")                    # 发件人邮箱密码或应用专用密码
TO_ADDR   = os.getenv("TO_ADDR")                      # 收件人邮箱地址

# -------------------------------
# 2️⃣ 工具函数：日志输出
# -------------------------------
def log(s):
    """打印日志信息并立即刷新（确保 GitHub Actions 实时显示）"""
    print(s, flush=True)

# -------------------------------
# 3️⃣ 获取 WBGT 数据
# -------------------------------
def fetch_wbgt(timeout=30) -> dict:
    """向 Render API 发送请求，解析返回 JSON"""
    log(f"[fetch] GET {API_URL}")
    r = requests.get(API_URL, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    log(f"[fetch] status={r.status_code}")  # 打印响应状态码
    r.raise_for_status()  # 如果不是 200，会直接抛异常（停止执行）

    # 尝试把返回内容解析为 JSON
    try:
        data = r.json()
    except Exception as e:
        # 如果解析失败，输出前 300 个字符方便调试
        snippet = r.text[:300].replace("\n", " ")
        raise RuntimeError(f"JSON decode failed: {e}; body head: {snippet}")

    # 校验关键字段是否存在
    if "max" not in data or "max_times" not in data:
        raise RuntimeError(f"JSON missing keys: got {list(data.keys())}")

    return data  # 返回解析好的 dict

# -------------------------------
# 4️⃣ 邮件发送函数
# -------------------------------
def send_json(data: dict, filename="point_82056.json"):
    """把 WBGT JSON 数据打包成附件并通过 SMTP 发邮件"""
    # 检查必要配置是否存在
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, TO_ADDR]):
        raise RuntimeError("Missing SMTP env (SMTP_HOST/PORT/USER/PASS or TO_ADDR).")

    # 创建邮件对象
    msg = EmailMessage()
    msg["Subject"] = "[WBGT JSON] auto"       # 邮件主题
    msg["From"]    = SMTP_USER                # 发件人
    msg["To"]      = TO_ADDR                  # 收件人
    msg.set_content("WBGT latest JSON attached.")  # 邮件正文

    # 将数据序列化成 JSON 并转为二进制（UTF-8）
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    # 添加附件
    msg.add_attachment(payload,
                       maintype="application",
                       subtype="json",
                       filename=filename)

    # 打印日志：连接 SMTP 服务器
    log(f"[smtp] connecting to {SMTP_HOST}:{SMTP_PORT} as {SMTP_USER}")

    # 建立安全连接并发送邮件
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=ssl.create_default_context())  # 启用 TLS 加密
        server.login(SMTP_USER, SMTP_PASS)                     # 登录邮箱
        server.send_message(msg)                               # 发送邮件
    log("[smtp] sent ok")  # 打印成功日志

# -------------------------------
# 5️⃣ 主逻辑：带重试机制
# -------------------------------
def main():
    """主函数：尝试获取数据并发送邮件，最多重试 3 次"""
    max_attempts = 3  # 最多重试次数
    delay = 20        # 两次重试间隔（秒）

    for i in range(1, max_attempts + 1):
        try:
            log(f"=== Attempt {i}/{max_attempts} ===")
            data = fetch_wbgt()  # 抓取数据
            log(f"[data] max={data.get('max')} max_times={data.get('max_times')}")  # 打印数据
            send_json(data)       # 发送邮件
            log("=== Done ===")   # 成功后退出
            return 0
        except Exception as e:
            # 捕获错误，打印并根据情况重试
            log(f"[error] {e}")
            if i < max_attempts:
                log(f"[retry] sleeping {delay}s ...")
                time.sleep(delay)
            else:
                log("[fail] all attempts failed")
                return 1  # 所有尝试失败

# -------------------------------
# 6️⃣ 程序入口
# -------------------------------
if __name__ == "__main__":
    # Python 脚本直接执行时运行 main()
    sys.exit(main())  # 用 sys.exit() 把状态码传给 GitHub Actions
