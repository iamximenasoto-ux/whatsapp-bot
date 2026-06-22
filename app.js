const { Client, LocalAuth } = require('whatsapp-web.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const express = require('express');
const qrcode = require('qrcode');

const app = express();
const genai = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

let qrActual = null;
let botListo = false;
const conversaciones = {};

const PERSONALIDAD = `Eres un asistente amigable y útil que responde por WhatsApp.
Sé conciso, claro y usa un tono cálido. Responde siempre en el mismo idioma que el usuario.`;

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        executablePath: process.env.CHROMIUM_PATH || 'chromium',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--single-process'],
    }
});

client.on('qr', (qr) => {
    qrActual = qr;
    botListo = false;
});

client.on('ready', () => {
    botListo = true;
    qrActual = null;
    console.log('Bot listo!');
});

client.on('disconnected', () => {
    botListo = false;
    client.initialize();
});

client.on('message', async (msg) => {
    if (msg.fromMe) return;
    const numero = msg.from;
    const texto = msg.body.trim();
    if (!texto) return;

    if (!conversaciones[numero]) conversaciones[numero] = [];
    conversaciones[numero].push({ role: 'user', parts: [{ text: texto }] });
    conversaciones[numero] = conversaciones[numero].slice(-20);

    try {
        const model = genai.getGenerativeModel({ model: 'gemini-1.5-flash', systemInstruction: PERSONALIDAD });
        const chat = model.startChat({ history: conversaciones[numero].slice(0, -1) });
        const result = await chat.sendMessage(texto);
        const respuesta = result.response.text();
        conversaciones[numero].push({ role: 'model', parts: [{ text: respuesta }] });
        await msg.reply(respuesta);
    } catch (err) {
        console.error('Error:', err.message);
    }
});

app.get('/', async (req, res) => {
    if (botListo) {
        res.send('<h1 style="font-family:sans-serif;text-align:center;color:green">✅ Bot conectado</h1>');
    } else if (qrActual) {
        const img = await qrcode.toDataURL(qrActual);
        res.send(`<html><head><meta http-equiv="refresh" content="30"></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px">
        <h1>Escanea este QR con WhatsApp</h1>
        <p>WhatsApp → <b>Dispositivos vinculados</b> → <b>Vincular un dispositivo</b></p>
        <img src="${img}" style="width:280px;padding:16px;border:1px solid #ddd;border-radius:12px"/>
        </body></html>`);
    } else {
        res.send('<html><head><meta http-equiv="refresh" content="5"></head><body style="font-family:sans-serif;text-align:center;padding:40px"><h1>⏳ Iniciando...</h1></body></html>');
    }
});

client.initialize();
const PORT = process.env.PORT || 3000;
app.listen(PORT);
