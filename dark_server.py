
import os
import time
from collections import defaultdict, deque
from threading import Lock
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from google import genai

app = Flask(__name__)

# Project folder
BASE_DIR = Path(__file__).resolve().parent

# Render proxy support
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1
)

# Gemini API Key
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found!")

client = genai.Client(api_key=API_KEY)

CHAT_MODEL = "gemini-3.5-flash-lite"

SYSTEM_INSTRUCTION = """
You are DARK AI 3.0, a friendly and intelligent AI assistant.

Rules:
1. If the user writes Sinhala, answer in Sinhala.
2. If the user writes Singlish, answer in Sinhala Unicode.
3. If the user writes English, answer in English.
4. Give clear, helpful and accurate answers.
"""

# Basic request protection
request_history = defaultdict(deque)
rate_lock = Lock()

MAX_PER_MINUTE = 10
MAX_PER_DAY = 100


def check_rate_limit(ip):
    now = time.time()

    with rate_lock:
        history = request_history[ip]

        # Remove requests older than 24 hours
        while history and now - history[0] >= 86400:
            history.popleft()

        # Count requests in the last minute
        recent_requests = sum(
            1 for t in history if now - t < 60
        )

        if recent_requests >= MAX_PER_MINUTE:
            return False, "Too many requests. Try again in one minute."

        if len(history) >= MAX_PER_DAY:
            return False, "Daily limit reached. Try again tomorrow."

        history.append(now)

        return True, None


@app.route("/")
def home():
    return send_from_directory(str(BASE_DIR), "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():

    ip = request.remote_addr or "unknown"

    allowed, error_message = check_rate_limit(ip)

    if not allowed:
        return jsonify({"error": error_message}), 429

    try:
        data = request.get_json(silent=True) or {}

        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({
                "error": "Please enter a message."
            }), 400

        if len(message) > 5000:
            return jsonify({
                "error": "Message is too long."
            }), 400

        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=message,
            config={
                "system_instruction": SYSTEM_INSTRUCTION
            }
        )

        answer = response.text or "I could not generate a response."

        return jsonify({"reply": answer})

    except Exception as error:

        print("AI ERROR:", error)

        return jsonify({
            "error": "DARK AI could not respond. Please try again."
        }), 500


if __name__ == "__main__":

    print("==============================")
    print("      DARK AI 3.0 WEBSITE")
    print("==============================")
    print("Local address: http://127.0.0.1:5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
