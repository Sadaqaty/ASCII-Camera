import cv2
import threading

class CameraStream:
    def __init__(self, src=0):
        """
        src: Camera index (default 0)
        """
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.cap.release() 