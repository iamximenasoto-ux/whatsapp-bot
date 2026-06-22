from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google import genai
import os

app = Flask(__name__)
cliente = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
conversaciones = {}

PERSONALIDAD = """Eres el asistente virtual de HOPPESA, una constructora que vende
departamentos de lujo a precios accesibles en la zona del Aeropuerto Internacional
de la Ciudad de México (AICM).
Tu objetivo es atender a clientes interesados en comprar un departamento.
- Ubicación: Zona Aeropuerto CDMX
- Para precios o agendar visita: 📞 +52 55 6197 0925 / 📧 miguelhoppe@hoppesa.com
- Sé cálido, profesional y breve
- Responde siempre en español
- Al saludar, preséntate como asistente de HOPPESA"""

@app.route("/webhook", methods=["POST"])
def webhook():
    numero = request.form.get("From", "")
    mensaje = request.form.get("Body", "").strip()
    if not mensaje:
        return str(MessagingResponse())
    if numero not in conversaciones:
        conversaciones[numero] = []
    conversaciones[numero].append({"role": "user", "parts": [{"text": mensaje}]})
    conversaciones[numero] = conversaciones[numero][-20:]
    respuesta = cliente.models.generate_content(
        model="gemini-1.5-flash",
        contents=conversaciones[numero],
        config={"system_instruction": PERSONALIDAD},
    )
    respuesta_texto = respuesta.text
    conversaciones[numero].append({"role": "model", "parts": [{"text": respuesta_texto}]})
    resp = MessagingResponse()
    resp.message(respuesta_texto)
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
