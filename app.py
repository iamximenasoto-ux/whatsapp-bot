from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import os

app = Flask(__name__)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
conversaciones = {}

PERSONALIDAD = """Eres un asistente amigable y útil que responde por WhatsApp.
Sé conciso, claro y usa un tono cálido. Responde siempre en el mismo idioma que el usuario."""

@app.route("/webhook", methods=["POST"])
def webhook():
    numero = request.form.get("From", "")
    mensaje = request.form.get("Body", "").strip()
    if not mensaje:
        return str(MessagingResponse())
    if numero not in conversaciones:
        conversaciones[numero] = []
    conversaciones[numero].append({"role": "user", "parts": [mensaje]})
    conversaciones[numero] = conversaciones[numero][-20:]
    modelo = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=PERSONALIDAD)
    chat = modelo.start_chat(history=conversaciones[numero][:-1])
    respuesta = chat.send_message(mensaje)
    respuesta_texto = respuesta.text
    conversaciones[numero].append({"role": "model", "parts": [respuesta_texto]})
    resp = MessagingResponse()
    resp.message(respuesta_texto)
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
