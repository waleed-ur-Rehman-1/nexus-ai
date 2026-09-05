import pyttsx3
import os
import tempfile
import uuid

class VoiceService:
    def __init__(self):
        self.is_available = False
        self.tts_engine = None
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            self.is_available = True
            print("✅ TTS initialized successfully.")
        except Exception as e:
            print(f"⚠️ TTS not available (eSpeak missing). Voice output disabled. Error: {e}")

    def speech_to_text(self, audio_file_path: str) -> str:
        # This method remains unchanged – we don't use eSpeak here
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                return text
        except Exception:
            return ""

    def text_to_speech(self, text: str, output_file: str = None) -> str:
        if not self.is_available or self.tts_engine is None:
            print(f"⚠️ TTS skipped: {text}")
            return ""  # return empty string to avoid errors
        if output_file is None:
            output_file = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.wav")
        self.tts_engine.save_to_file(text, output_file)
        self.tts_engine.runAndWait()
        return output_file