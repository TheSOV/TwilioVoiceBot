import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import yaml

# Load environment variables from .env file
load_dotenv(override=True)

# Load OpenAI models and credentials
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_STT_MODEL = os.getenv('OPENAI_STT_MODEL')
OPENAI_TEXT_MODEL = os.getenv('OPENAI_TEXT_MODEL')

class ClientInfoExtraction(BaseModel):
    place: str
    budget: int
    other_requirements: str

class InfoExtractionAgent:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def _load_system_message(self):
        yaml_path = os.path.join(os.path.dirname(__file__), 'AI', 'prompts', 'info_extraction_prompts.yaml')

        with open(yaml_path, 'r', encoding='utf-8') as file:
            system_config = yaml.safe_load(file)
            return system_config['system_prompt']['content'], system_config['initial_prompt']['content']

    def _transcribe_audio(self, filedir):
        audio_file = open(filedir, "rb")
        transcription = self.client.audio.transcriptions.create(
            model=OPENAI_STT_MODEL, 
            file=audio_file,
            language="es",
            prompt="MiCityHome",
        )
        print(f"Transcription: {transcription.text}")
        return transcription.text

    def _extract_info_from_transcription(self, text):
        system_prompt, initial_prompt = self._load_system_message()
        text = f"{initial_prompt}\n\n{text}"

        response = self.client.beta.chat.completions.parse(
            model=OPENAI_TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format=ClientInfoExtraction,
        )
        return response.choices[0].message

    def extract_info(self, audio_file):
        text = self._transcribe_audio(audio_file)
        return self._extract_info_from_transcription(text)


if __name__ == '__main__':
    agent = InfoExtractionAgent()
    filedir = 'recordings/combined/combined_audio_20250206_073547.wav'
    response = agent.extract_info(filedir)
    print(response)