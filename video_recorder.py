import cv2
import os
from datetime import datetime
import numpy as np
import subprocess
import tempfile

class VideoRecorder:
    def __init__(self, width, height, fps=20):
        """
        width, height: Frame size
        fps: Frames per second
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.writer = None
        self.filename = None
        self.final_filename = None

    def start(self):
        if not os.path.exists('videos'):
            os.makedirs('videos')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.filename = os.path.join(tempfile.gettempdir(), f'ascii_{timestamp}_video.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.filename, fourcc, self.fps, (self.width, self.height))

    def write_frame(self, image):
        """
        image: Pillow Image (RGB)
        """
        if self.writer is not None:
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            self.writer.write(frame)

    def stop(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None
        return self.filename

    def reencode_fps(self, new_fps):
        """
        Use ffmpeg to re-encode the temp video file with the correct FPS, replacing the original file.
        """
        if not self.filename or not os.path.exists(self.filename):
            return
        temp_out = self.filename.replace('.mp4', '_fpsfix.mp4')
        cmd = [
            'ffmpeg', '-y',
            '-i', self.filename,
            '-r', str(new_fps),
            temp_out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(temp_out):
            os.replace(temp_out, self.filename)

    def mux_with_audio(self, audio_wav_path):
        """
        Use ffmpeg to mux the video and audio into a final mp4 in videos/.
        Returns the final mp4 path.
        """
        if not os.path.exists('videos'):
            os.makedirs('videos')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.final_filename = f'videos/ascii_{timestamp}.mp4'
        # ffmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-i', self.filename,
            '-i', audio_wav_path,
            '-c:a', 'aac',
            '-shortest',
            self.final_filename
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Clean up temp files
        if os.path.exists(self.filename):
            os.remove(self.filename)
        if os.path.exists(audio_wav_path):
            os.remove(audio_wav_path)
        return self.final_filename 