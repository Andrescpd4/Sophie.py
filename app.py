import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
MESSAGE_FILE = os.path.join(os.path.dirname(__file__), "message.txt")

DEFAULT_MESSAGE = """Sophie

Feliz cumpleaños.

Aquí escribiré algo mucho más bonito después.


— Brayan"""

def get_message():
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    # Create the default file if it doesn't exist
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        f.write(DEFAULT_MESSAGE)
    return DEFAULT_MESSAGE

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

if __name__ == "__main__":
    # En Railway el puerto se pasa en la variable de entorno PORT
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)