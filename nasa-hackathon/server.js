const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');

const app = express();
const PORT = 3000;

// Obtén tu API key GRATIS en: https://makersuite.google.com/app/apikey
const GEMINI_API_KEY = 'AIzaSyAX4PoLfHacsq7yHCpix5lr2sZ58BIAIA4';

app.use(cors());
app.use(express.json());
app.use(express.static('.'));

app.post('/api/chat', async (req, res) => {
    console.log('📨 Nueva petición recibida');
    
    try {
        // Convertir el formato de mensajes de OpenAI a Gemini
        const messages = req.body.messages;
        
        // Construir el historial de conversación para Gemini
        const contents = messages.map(msg => ({
            role: msg.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: msg.content }]
        }));

        // Usar gemini-2.0-flash que está disponible
        const response = await fetch(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: contents,
                    generationConfig: {
                        temperature: 0.7,
                        maxOutputTokens: 2000,
                    }
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            console.error('❌ Error de Gemini:', data);
            return res.status(response.status).json({
                error: { message: data.error?.message || 'Error con Gemini API' }
            });
        }

        // Verificar que hay una respuesta válida
        if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
            console.error('❌ Respuesta inválida de Gemini:', data);
            return res.status(500).json({
                error: { message: 'Respuesta inválida de Gemini API' }
            });
        }

        // Convertir respuesta de Gemini al formato de OpenAI
        const geminiResponse = data.candidates[0].content.parts[0].text;
        
        const openAiFormat = {
            choices: [{
                message: {
                    role: 'assistant',
                    content: geminiResponse
                }
            }]
        };

        console.log('✅ Respuesta exitosa de Gemini');
        res.json(openAiFormat);

    } catch (error) {
        console.error('❌ Error:', error.message);
        res.status(500).json({ 
            error: { message: error.message }
        });
    }
});

app.listen(PORT, () => {
    console.log(`🚀 Servidor con Google Gemini en http://localhost:${PORT}`);
    console.log(`📝 Abre http://localhost:${PORT}/chat.html`);
    console.log(`🔑 Modelo usado: gemini-2.0-flash`);
    console.log(`🔑 Obtén tu API key gratis en: https://makersuite.google.com/app/apikey`);
});