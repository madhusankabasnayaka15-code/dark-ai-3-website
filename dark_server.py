
import os
from flask import Flask, request, jsonify, send_from_directory
from google import genai

app = Flask(__name__)

# Gemini API Key - Windows Environment Variable
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found in Windows Environment Variables."
    )

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

@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({"error": "Please enter a message."}), 400

        if len(message) > 10000:
            return jsonify({"error": "Message is too long."}), 400

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
    print("================================")
    print("       DARK AI 3.0 WEBSITE")
    print("================================")
    print("Local address: http://127.0.0.1:5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )

