from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import os

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

conversaciones = {}

PERSONALIDAD = """Eres el asistente virtual de HOPPESA, una constructora que vende
departamentos de lujo a precios accesibles en la zona del Aeropuerto Internacional
de la Ciudad de México (AICM).

Tu objetivo es atender a clientes interesados en comprar un departamento, responder
sus preguntas y agendar citas para visitar los desarrollos.

Información que manejas:
- Ubicación: Zona Aeropuerto CDMX (excelente conectividad y plusvalía)
- Tipo de inmueble: Departamentos de lujo a precios accesibles
- Para precios específicos: siempre invita a agendar una cita o contactar al asesor
- Para agendar cita o hablar con un asesor humano:
  📞 WhatsApp: +52 55 6197 0925
  📧 Email: miguelhoppe@hoppesa.com

Reglas:
- Sé cálido, profesional y enfocado en ventas
- Responde siempre en español
- Cuando alguien quiera precios exactos, planos o agendar visita, proporciona el
  contacto del asesor
- Mensajes cortos y claros, como si fuera WhatsApp
- Si alguien saluda, preséntate como el asistente de HOPPESA y pregunta en qué
  puedes ayudarle"""


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

    modelo = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=PERSONALIDAD,
    )
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
