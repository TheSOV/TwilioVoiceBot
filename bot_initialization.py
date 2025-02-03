import json

async def initialize_session(openai_ws, voice, system_message):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.9,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 1000,
                "create_response": True
            },
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": voice,
            "instructions": system_message,
            "modalities": ["text", "audio"],
            "temperature": 0.6,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Have the AI speak first
    await send_initial_conversation_item(openai_ws)


async def send_initial_conversation_item(openai_ws):
    """Send initial conversation so AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        """Primero saludas al cliente, y explicas brevemente que has notado que está buscando una propiedad en alquiler y luego que estás para ayudarlo a encontrar una propiedad en alquiler. Todo muy breve, en pocas palabras.
                        
                        Si el cliente confirma que está buscando una propiedad en alquiler, continua con el conversatorio, mencionando que eres el asistente virtual de MyCityHome, y que harás algunas preguntas para entender mejor sus necesidades.
                        
                        
                        Ejemplos de conversaciones:
                            -Asistente virtual de MyCityHome: ¡Hola! He notado que está planeando mudarse. ¿Le interesaría escuchar algunas ofertas?
                            Cliente: Sí
                            -Asistente virtual de MyCityHome: Perfecto, soy el asistente virtual de MyCityHome, y a continuación realizo una serie de preguntas para entender mejor sus necesidades. ¿En qué zona desea vivir?
                            ...resto de la conversación..."""
                        )
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    # await openai_ws.send(json.dumps({"type": "response.create"}))

