import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

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

OPENAI_URL = "https://api.openai.com/v1/responses"

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/chat")
def chat():
    if not OPENAI_API_KEY:
        return jsonify({"ok": False, "error": "Missing OPENAI_API_KEY"}), 500

    data = request.get_json()
    message = data.get("message", "")
    history = data.get("history", [])

    input_items = [{"role": "system", "content": SYSTEM_INSTRUCTIONS}]
    input_items += history[-12:]
    input_items.append({"role": "user", "content": message})

    response = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": OPENAI_MODEL,
            "input": input_items
        }
    )

    result = response.json()

    # Responses API provides a convenient aggregated text field:
    assistant_text = result.get("output_text", "")

    # Fallback: if output_text is missing, try to extract manually
    if not assistant_text:
        for item in result.get("output", []):
            for chunk in item.get("content", []):
                if chunk.get("type") == "output_text":
                    assistant_text += chunk.get("text", "")

    return jsonify({"ok": True, "reply": assistant_text})

@app.get("/")
def home():
    return jsonify({"ok": True, "endpoints": ["/health", "/chat"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

