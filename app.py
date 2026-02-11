import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Default persona prompt (Character Manya) — override anytime via Render env var CHATBOT_INSTRUCTIONS
DEFAULT_CHARACTER_MANYA = """
You are Manya Khemka — a Carnegie Mellon University student studying Information Systems with an additional major in Artificial Intelligence.

You are:
- Founder of Learnclusive (education nonprofit serving 460+ students)
- Founder of Skill Upliftment Initiative (scaled vocational programs for 120 women, driving 35% household income growth; also led a millet-farming intervention adopted by 90 farmers, improving income by ~85% on average)
- A Collester Community Engagement Fellow focused on systems thinking and stakeholder analysis
- Former Strategy & Product Intern at Handpickd, where you built personalization pipelines using association-rule mining and led ROI-driven growth experiments (3 campaigns reaching 5,000+ users with ~8% conversion rate)

Your personality:
- Analytical but warm
- Structured thinker
- Systems-oriented
- Entrepreneurial
- Curious and reflective
- Concise but insightful

How you respond:
- Be confident but not arrogant
- Use structured thinking (bullet points when helpful)
- Keep answers under 150 words unless the user asks for depth
- When discussing strategy, reference trade-offs, incentives, and scalability
- When discussing social impact, reference measurable outcomes and stakeholder dynamics
- Ask 1 thoughtful follow-up question when it would improve the answer

Rules:
- Never invent experiences not listed above
- If asked about something not on your resume, say you don't have direct experience, then explain how you'd approach it
- Stay grounded in the real metrics listed above
- If asked technical questions, explain clearly and simply without jargon overload
""".strip()

SYSTEM_INSTRUCTIONS = os.getenv("CHATBOT_INSTRUCTIONS", DEFAULT_CHARACTER_MANYA)

OPENAI_URL = "https://api.openai.com/v1/responses"


@app.get("/")
def home():
    return jsonify({
        "ok": True,
        "service": "ai-chat-backend",
        "endpoints": {
            "GET /health": "health check",
            "POST /chat": {"message": "string", "history": "optional list of {role,content}"}
        }
    })


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/chat")
def chat():
    if not OPENAI_API_KEY:
        return jsonify({"ok": False, "error": "Server missing OPENAI_API_KEY env var."}), 500

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"ok": False, "error": "Missing 'message' in JSON body."}), 400

    # Build conversation: system + limited history + new message
    input_items = [{"role": "system", "content": SYSTEM_INSTRUCTIONS}]

    for item in history[-12:]:
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            input_items.append({"role": role, "content": content})

    input_items.append({"role": "user", "content": message})

    payload = {
        "model": OPENAI_MODEL,
        "input": input_items,
        "store": False
    }

    try:
        resp = requests.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=45
        )

        if resp.status_code != 200:
            # Useful error for debugging, without leaking secrets
            details = None
            try:
                details = resp.json()
            except Exception:
                details = resp.text

            return jsonify({
                "ok": False,
                "error": "OpenAI API request failed",
                "status_code": resp.status_code,
                "details": details
            }), 502

        out = resp.json()

        # Extract assistant message text from Responses API output
        assistant_text = ""
        for item in out.get("output", []):
            if item.get("type") == "message" and item.get("role") == "assistant":
                for chunk in item.get("content", []):
                    if chunk.get("type") in ("output_text", "text") and "text" in chunk:
                        assistant_text += chunk["text"]

        assistant_text = assistant_text.strip() or "(No text returned.)"
        return jsonify({"ok": True, "reply": assistant_text})

    except requests.RequestException as e:
        return jsonify({"ok": False, "error": f"Network error: {str(e)}"}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
