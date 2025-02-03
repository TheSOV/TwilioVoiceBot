import torch
import torchaudio

# Load the Silero VAD model from Torch Hub
model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=True)

# Get utility functions
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
# Load an audio file (must be mono, 16kHz for best results)
wav = read_audio("recordings/audio_20250129_072721.wav", sampling_rate=8000)

resample = torchaudio.transforms.Resample(orig_freq=8000, new_freq=16000)
wav = resample(wav)

# Get speech timestamps
speech_timestamps = get_speech_timestamps(wav, model)

# Print detected speech regions
for segment in speech_timestamps:
    print(f"Speech from {segment['start']} to {segment['end']} ms")
