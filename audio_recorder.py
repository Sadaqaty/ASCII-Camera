import sounddevice as sd
import numpy as np
import threading
import scipy.io.wavfile as wavfile
import tempfile
import os

class AudioRecorder:
    def __init__(self, samplerate=44100, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self.recording = False
        self.frames = []
        self.thread = None
        self.wav_path = os.path.join(tempfile.gettempdir(), 'ascii_cam_audio.wav')

    def _callback(self, indata, frames, time, status):
        if self.recording:
            self.frames.append(indata.copy())

    def start(self):
        self.frames = []
        self.recording = True
        self.stream = sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=self._callback)
        self.stream.start()

    def stop(self):
        self.recording = False
        self.stream.stop()
        self.stream.close()
        audio = np.concatenate(self.frames, axis=0)
        wavfile.write(self.wav_path, self.samplerate, audio)
        return self.wav_path

    def get_wav_path(self):
        return self.wav_path 