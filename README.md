# AI Chat Backend

This backend powers a chatbot hosted on Render.

Endpoints:

GET /health  
Returns: {"ok": true}

POST /chat  
Accepts:
{
  "message": "Hello",
  "history": []
}

Returns:
{
  "ok": true,
  "reply": "..."
}

The frontend calls this backend using fetch().
The OpenAI API key is stored securely as an environment variable on Render.
