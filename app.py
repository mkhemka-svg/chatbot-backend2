import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

SYSTEM_INSTRUCTIONS = """
You are Manya Khemka — a Carnegie Mellon University student studying Information Systems with an additional major in Artificial Intelligence.

You are:
- Founder of Learnclusive (460+ students served)
- Founder of Skill Upliftment Initiative (120 women trained; 35% income growth)
- Built personalization pipelines using association-rule mining at Handpickd
- A Collester Fellow focused on systems thinking and stakeholder analysis

Be analytical but warm.
Keep answers under 150 words unless asked for depth.
Use structured thinking.
Never invent experiences.
""".strip()

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


@app.get("/")
def home():
    return jsonify({"ok": True, "endpoints": ["/health", "/chat"]})


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/chat")
def chat():
    if not GEMINI_API_KEY:
        return jsonify({"ok": False, "error": "Missing GEMINI_API_KEY"}), 500

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"ok": False, "error": "Message is required"}), 400

    # Convert your history format [{role, content}, ...] into a single text context
    # (Simple + reliable approach)
    convo_lines = [f"SYSTEM: {SYSTEM_INSTRUCTIONS}"]
    for h in history[-12:]:
        role = h.get("role", "")
        content = h.get("content", "")
        if role and content:
            convo_lines.append(f"{role.upper()}: {content}")
    convo_lines.append(f"USER: {message}")

    prompt_text = "\n".join(convo_lines)

    resp = requests.post(
        GEMINI_URL,
        params={"key": GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json={
            "contents": [
                {"role": "user", "parts": [{"text": prompt_text}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 250
            }
        },
        timeout=60
    )

    if resp.status_code != 200:
        return jsonify({"ok": False, "status": resp.status_code, "error": resp.text}), 500

    result = resp.json()

    # Extract text safely
    reply = ""
    try:
        reply = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        reply = ""

    return jsonify({"ok": True, "reply": reply})
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
