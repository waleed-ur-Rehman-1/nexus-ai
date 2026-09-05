import pvporcupine
import pyaudio
import struct
import threading
import time
import os
import tempfile
import wave
import asyncio

class WakeWordService:
    def __init__(self, keyword="porcupine", callback=None):
        """
        keyword: built-in keyword ('porcupine', 'hey google', 'alexa', etc.)
        callback: function to call when wake word is detected
        """
        self.keyword = keyword
        self.callback = callback
        self.porcupine = pvporcupine.create(keywords=[keyword])
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        self.running = False
        self.listening = False

    def start_listening(self):
        self.running = True
        threading.Thread(target=self._listen, daemon=True).start()
        print(f"🔊 Wake word '{self.keyword}' listening started.")

    def _listen(self):
        while self.running:
            pcm = self.stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            if self.porcupine.process(pcm) >= 0:
                print("🔊 Wake word detected!")
                if self.callback:
                    self.callback()
                # Avoid multiple triggers
                time.sleep(1)

    def stop(self):
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()