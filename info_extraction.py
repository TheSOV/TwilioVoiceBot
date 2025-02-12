import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
import yaml
from pyannote.audio import Pipeline


# Load environment variables from .env file
load_dotenv(override=True)

# Load OpenAI models and credentials
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_STT_MODEL = os.getenv('OPENAI_STT_MODEL')
OPENAI_TEXT_MODEL = os.getenv('OPENAI_TEXT_MODEL')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')

class ClientInfoExtraction(BaseModel):
    place: str = Field(description="El lugar o lugares en los que el cliente desearía vivir.")
    budget: int = Field(description="El presupuesto máximo que el cliente está dispuesto a gastar.")
    other_requirements: str = Field(description="Requisitos o preferencias adicionales para la vivienda.")

class InfoExtractionAgent:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=HUGGINGFACE_TOKEN)

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
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
        # print(f"Transcription: {transcription.words}")
        return transcription

    def _combine_transcription_and_diarization(self, transcription, diarization):
        # Convert diarization to a list of speaker segments
        speaker_segments = []
        for segment, track, label in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                'speaker': label,
                'start': segment.start,
                'end': segment.end
            })
        
        # Sort speaker segments by start time
        speaker_segments.sort(key=lambda x: x['start'])
        
        # Combine words with speakers
        conversation = []
        current_speaker = None
        current_speaker_text = []
        
        for word in transcription.words:
            # Find the speaker for this word
            word_speaker = None
            for segment in speaker_segments:
                if segment['start'] <= word.start < segment['end']:
                    word_speaker = segment['speaker']
                    break
            
            # If speaker changes, add previous speaker's text to conversation
            if word_speaker != current_speaker and current_speaker is not None:
                conversation.append({
                    'speaker': current_speaker,
                    'text': ' '.join(current_speaker_text)
                })
                current_speaker_text = []
            
            # Update current speaker
            current_speaker = word_speaker
            current_speaker_text.append(word.word)
        
        # Add last speaker's text
        if current_speaker_text:
            conversation.append({
                'speaker': current_speaker,
                'text': ' '.join(current_speaker_text)
            })
        
        return conversation

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
        transcription = self._transcribe_audio(audio_file)
        diarization = self.diarization_pipeline(audio_file, num_speakers=2)

        # Combine transcription and diarization
        conversation = self._combine_transcription_and_diarization(transcription, diarization)
        
        # Print the conversation for debugging
        print("Conversation:")
        for turn in conversation:
            print(f"{turn['speaker']}: {turn['text']}")
        
        # Extract info from the transcribed text
        text = " ".join([turn['text'] for turn in conversation])
        return self._extract_info_from_transcription(text), conversation


if __name__ == '__main__':
    agent = InfoExtractionAgent()
    filedir = 'call_results/+34616642830/combined_audio_+34616642830.wav'
    response = agent.extract_info(filedir)
    print()
    print("Extracted info:")
    print(response)