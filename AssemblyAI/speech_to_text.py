import assemblyai as aai

aai.settings.api_key = "3aecc3231d964f61b37e334f18fbee0c"

audio_file = "AUDIO/Dollar Drop Prediction.mp3"
# audio_file = "https://assembly.ai/wildfires.mp3"

config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)

transcript = aai.Transcriber(config=config).transcribe(audio_file)

if transcript.status == "error":
  raise RuntimeError(f"Transcription failed: {transcript.error}")

print(transcript.text)