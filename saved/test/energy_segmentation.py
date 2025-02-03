import librosa
import numpy as np
import soundfile as sf

# Load audio file
y, sr = librosa.load("audio.wav", sr=None)

# Define frame and hop length
frame_length = 1024
hop_length = 512

# Compute short-time energy (STE)
energy = np.array([
    sum(abs(y[i:i + frame_length] ** 2))
    for i in range(0, len(y), hop_length)
])

# Define threshold (50% of mean energy)
threshold = np.mean(energy) * 0.5

# Find segments with energy above threshold
segments = []
start = None
for i, e in enumerate(energy):
    if e > threshold and start is None:
        start = i * hop_length  # Convert to sample index
    elif e < threshold and start is not None:
        segments.append((start, i * hop_length))
        start = None

# If audio ends with speech, add the last segment
if start is not None:
    segments.append((start, len(y)))

# Save extracted segments
for i, (start, end) in enumerate(segments):
    sf.write(f"segment_{i}.wav", y[start:end], sr)

print(f"Extracted {len(segments)} high-energy segments.")
