import os
import re
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_compress import Compress

app = Flask(__name__, static_folder=None)
Compress(app)
app.config["COMPRESS_MIMETYPES"] = [
    "text/html", "text/css", "text/xml", "application/json",
    "application/javascript", "image/svg+xml",
]
app.config["COMPRESS_LEVEL"] = 6
app.config["COMPRESS_MIN_SIZE"] = 500

MESSAGE_FILE = os.path.join(os.path.dirname(__file__), "message.txt")

DEFAULT_MESSAGE = """Sophie

Feliz cumpleaños.

Aquí escribiré algo mucho más bonito después.

— Brayan"""

# --- Logging dual: consola (Railway) + archivo rotativo ---
access_logger = logging.getLogger("access")
access_logger.setLevel(logging.INFO)
access_logger.propagate = False

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
access_logger.addHandler(console_handler)

log_file = os.path.join(os.path.dirname(__file__), "access.log")
file_handler = RotatingFileHandler(
    log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
access_logger.addHandler(file_handler)

UA_PATTERNS = [
    (r"Android", "Android"),
    (r"iPhone|iPad|iPod", "iOS"),
    (r"Windows Phone", "Windows Phone"),
    (r"Windows", "Windows"),
    (r"Mac OS X|macintosh", "macOS"),
    (r"Linux", "Linux"),
    (r"CrOS", "ChromeOS"),
]
BROWSER_PATTERNS = [
    (r"Edg/|EdgA|EdgiOS", "Edge"),
    (r"OPR|Opera", "Opera"),
    (r"Firefox", "Firefox"),
    (r"SamsungBrowser", "Samsung"),
    (r"Chrome", "Chrome"),
    (r"Safari", "Safari"),
]


def parse_user_agent(ua):
    if not ua or ua == "unknown":
        return "unknown"
    os_name = "unknown"
    for pattern, name in UA_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            os_name = name
            break
    browser = "unknown"
    for pattern, name in BROWSER_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            browser = name
            break
    is_mobile = bool(re.search(r"Mobile|Android|iPhone|iPod|BlackBerry|Opera Mini|IEMobile", ua, re.IGNORECASE))
    device_type = "Mobile" if is_mobile else "Desktop"
    return f"{device_type}|{os_name}|{browser}|{ua[:60]}"


def get_message():
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        f.write(DEFAULT_MESSAGE)
    return DEFAULT_MESSAGE


@app.before_request
def log_request_info():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    ua = request.headers.get("User-Agent", "unknown")
    device = parse_user_agent(ua)
    access_logger.info(f"IP={ip} | DEVICE={device} | PATH={request.path}")


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.route("/")
def home():
    return render_template(
        "index.html",
        message=get_message()
    )


@app.route("/save_message", methods=["POST"])
def save_message():
    try:
        data = request.get_json()
        new_message = data.get("message", "")
        with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
            f.write(new_message)
        return jsonify({"status": "success", "message": "Message saved successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/static/<path:filename>")
def static_files(filename):
    response = send_from_directory("static", filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".webp", ".jpeg", ".jpg", ".png", ".gif", ".svg"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif ext in (".mp3", ".mp4", ".wav", ".ogg"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    else:
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)