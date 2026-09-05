import speech_recognition as sr
import pyttsx3
import os
import tempfile
import uuid

class VoiceService:
    def __init__(self):
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)

    def speech_to_text(self, audio_file_path: str) -> str:
        """
        Convert audio file to text.
        Supports WAV, WebM, OGG, MP4, etc. (converts to WAV internally).
        """
        # If file is not WAV, convert using pydub
        if not audio_file_path.lower().endswith('.wav'):
            try:
                from pydub import AudioSegment
                # Load the audio file (supports many formats)
                audio = AudioSegment.from_file(audio_file_path)
                # Create a temporary WAV file
                wav_path = audio_file_path.rsplit('.', 1)[0] + '.wav'
                audio.export(wav_path, format='wav')
                audio_file_path = wav_path
            except ImportError:
                print("⚠️ pydub not installed. Please install: pip install pydub")
                return ""
            except Exception as e:
                print(f"❌ Audio conversion error: {e}")
                return ""

        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                return text
        except sr.UnknownValueError:
            print("⚠️ Speech not recognized.")
            return ""
        except sr.RequestError as e:
            print(f"❌ Google Speech Recognition error: {e}")
            return ""
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return ""

    def text_to_speech(self, text: str, output_file: str = None) -> str:
        if output_file is None:
            output_file = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.wav")
        self.tts_engine.save_to_file(text, output_file)
        self.tts_engine.runAndWait()
        return output_file