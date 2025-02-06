import json
import yaml
import os

def load_tools():
    """Load tools from tools.yaml file."""
    yaml_path = os.path.join(os.path.dirname(__file__), 'AI', 'tools', 'tools.yaml')
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            tools_config = yaml.safe_load(file)
            return tools_config
    except (IOError, KeyError) as e:
        print(f"Error loading tools: {e}")
        return {}

async def initialize_session(openai_ws, voice, system_message):
    """Control initial session with OpenAI."""

    # load tools from tools.yaml
    tools = load_tools()
    system_tools = list(tools.values())

    # print('Tools:', tools)
    
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.9,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 800,
                "create_response": True
            },
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": voice,
            "instructions": system_message,
            "modalities": ["text", "audio"],
            "temperature": 0.6,
            "tools": system_tools
        }
    }

    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Have the AI speak first
    await send_initial_conversation_item(openai_ws)


def load_initial_conversation_script():
    """Load initial conversation script from YAML file."""
    yaml_path = os.path.join(os.path.dirname(__file__), 'AI', 'prompts', 'info_extraction_prompts.yaml')
    
    with open(yaml_path, 'r', encoding='utf-8') as file:
        script_config = yaml.safe_load(file)
        return script_config.get('initial_conversation', {}).get('script', '')


async def send_initial_conversation_item(openai_ws):
    """Send initial conversation so AI talks first."""
    initial_script = load_initial_conversation_script()

    print('Sending initial conversation script:', initial_script)   
    
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": initial_script
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    # await openai_ws.send(json.dumps({"type": "response.create"}))
