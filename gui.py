import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, Image, ImageDraw, ImageFont
import threading
import time
import shutil
import os

from ascii_renderer import ASCIIRenderer, DENSE_CHARS, LIGHT_CHARS
from camera_stream import CameraStream
from image_saver import save_image
from video_recorder import VideoRecorder
from audio_recorder import AudioRecorder
from config import CONFIG

APP_ACCENT = '#4F8EF7'
APP_FONT = ('Segoe UI', 12)
HEADER_FONT = ('Segoe UI', 18, 'bold')

RESOLUTIONS = {
    '480p': (640, 480),
    '720p': (1280, 720),
    '1080p': (1920, 1080)
}
DENSITIES = {
    'Dense': DENSE_CHARS,
    'Light': LIGHT_CHARS
}

class ASCIICamApp:
    def __init__(self, root):
        self.root = root
        self.root.title('ASCII Camera')
        self.root.configure(bg='#f7f9fa')
        self.root.resizable(False, False)

        # State
        self.resolution = tk.StringVar(value='720p')
        self.density = tk.StringVar(value='Dense')
        self.color_mode = tk.BooleanVar(value=False)
        self.font_size = tk.IntVar(value=18)
        self.recording = False
        self.fps = 0
        self.last_frame_time = time.time()
        self.frame_timestamps = []
        self.blink = True

        # Camera and ASCII renderer
        self.cam = CameraStream()
        self.cam.start()
        self.renderer = self._make_renderer()
        self.video_recorder = None
        self.audio_recorder = None
        self.preview_imgtk = None
        self.first_frame = True
        self.out_width, self.out_height = RESOLUTIONS[self.resolution.get()]
        self.overlay_font = ImageFont.truetype(self.renderer.font_path, 16)

        # Settings panel
        self.settings_frame = tk.Frame(self.root, bg='#f7f9fa')
        self.settings_frame.pack(pady=(8, 0))
        tk.Label(self.settings_frame, text='Resolution:', bg='#f7f9fa').pack(side='left', padx=(0, 4))
        res_menu = ttk.OptionMenu(self.settings_frame, self.resolution, self.resolution.get(), *RESOLUTIONS.keys(), command=self._on_settings_change)
        res_menu.pack(side='left', padx=4)
        tk.Label(self.settings_frame, text='Density:', bg='#f7f9fa').pack(side='left', padx=(12, 4))
        dens_menu = ttk.OptionMenu(self.settings_frame, self.density, self.density.get(), *DENSITIES.keys(), command=self._on_settings_change)
        dens_menu.pack(side='left', padx=4)
        color_btn = ttk.Checkbutton(self.settings_frame, text='Color', variable=self.color_mode, command=self._on_settings_change)
        color_btn.pack(side='left', padx=(12, 4))

        # Header
        self.header = tk.Label(self.root, text='ASCII Camera', font=HEADER_FONT, bg='#f7f9fa', fg=APP_ACCENT, pady=6)
        self.header.pack(side='top', fill='x')

        # Preview card frame
        self.card = tk.Frame(self.root, bg='white', bd=0, highlightthickness=0)
        self.card.pack(pady=(10, 0), padx=30)

        # Preview label (image) with small placeholder
        placeholder = Image.new('RGB', (320, 180), color='#e0e4ea')
        self.preview_imgtk = ImageTk.PhotoImage(placeholder)
        self.preview_label = tk.Label(self.card, bg='white', bd=0, image=self.preview_imgtk, width=320, height=180)
        self.preview_label.pack(padx=24, pady=24)

        # Controls frame
        self.controls = tk.Frame(self.root, bg='#f7f9fa')
        self.controls.pack(pady=(10, 0))
        self.capture_btn = ttk.Button(self.controls, text='📸 Capture', command=self.capture_image, style='Accent.TButton')
        self.capture_btn.grid(row=0, column=0, padx=16, pady=10)
        self.record_btn = ttk.Button(self.controls, text='⏺ Record', command=self.start_recording, style='Accent.TButton')
        self.record_btn.grid(row=0, column=1, padx=16, pady=10)
        self.stop_btn = ttk.Button(self.controls, text='⏹ Stop', command=self.stop_recording, state='disabled', style='Accent.TButton')
        self.stop_btn.grid(row=0, column=2, padx=16, pady=10)
        self.exit_btn = ttk.Button(self.controls, text='✖ Exit', command=self.on_exit, style='Accent.TButton')
        self.exit_btn.grid(row=0, column=3, padx=16, pady=10)
        self.about_btn = ttk.Button(self.controls, text='❔ About', command=self.show_about, style='Link.TButton')
        self.about_btn.grid(row=0, column=4, padx=8, pady=10)

        # Status label
        self.status_label = tk.Label(self.root, text='Ready', bg='#f7f9fa', fg='#444', font=APP_FONT)
        self.status_label.pack(pady=(0, 12))

        # Style
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('Accent.TButton', font=APP_FONT, background=APP_ACCENT, foreground='white', borderwidth=0, focusthickness=3, focuscolor=APP_ACCENT, padding=10)
        style.map('Accent.TButton', background=[('active', '#2566d6')])
        style.configure('Link.TButton', font=(APP_FONT[0], 11, 'underline'), background='#f7f9fa', foreground=APP_ACCENT, borderwidth=0)
        style.map('Link.TButton', foreground=[('active', '#2566d6')])

        # Start preview update thread
        self.update_thread = threading.Thread(target=self.update_preview, daemon=True)
        self.update_thread.start()
        self._start_blink()

    def _make_renderer(self):
        return ASCIIRenderer(
            font_size=self.font_size.get(),
            density=DENSITIES[self.density.get()],
            color_mode=self.color_mode.get()
        )

    def _on_settings_change(self, *_):
        self.out_width, self.out_height = RESOLUTIONS[self.resolution.get()]
        self.renderer = self._make_renderer()
        self.overlay_font = ImageFont.truetype(self.renderer.font_path, 16)
        self.first_frame = True

    def _start_blink(self):
        def blink():
            self.blink = not self.blink
            self.root.after(500, blink)
        blink()

    def update_preview(self):
        while True:
            frame = self.cam.get_frame()
            if frame is not None:
                img = self.renderer.frame_to_ascii_image(frame, self.out_width, self.out_height)
                
                # Draw overlay directly on the image
                draw = ImageDraw.Draw(img)
                if self.recording and self.blink:
                    draw.ellipse((20, 20, 40, 40), fill='red', outline='red')
                fps_text = f"FPS: {self.fps:.1f}"
                draw.text((self.out_width - 20, 20), fps_text, anchor='rt', fill='red', font=self.overlay_font)

                self.preview_imgtk = ImageTk.PhotoImage(img)
                self.preview_label.config(image=self.preview_imgtk, width=self.out_width, height=self.out_height)

                # Resize card and window only on first frame or if size changes
                if self.first_frame:
                    self.card.config(width=self.out_width + 48, height=self.out_height + 48)
                    self.card.pack_propagate(False)
                    win_w = min(self.out_width + 120, self.root.winfo_screenwidth())
                    win_h = min(self.out_height + 220, self.root.winfo_screenheight())
                    self.root.geometry(f"{win_w}x{win_h}")
                    self.first_frame = False
                # FPS calculation
                now = time.time()
                self.fps = 1.0 / (now - self.last_frame_time) if self.last_frame_time else 0
                self.last_frame_time = now
                # Video recording
                if self.recording and self.video_recorder:
                    self.video_recorder.write_frame(img)
                    self.frame_timestamps.append(now)

            time.sleep(0.03)  # ~30 FPS max

    def capture_image(self):
        frame = self.cam.get_frame()
        if frame is not None:
            img = self.renderer.frame_to_ascii_image(frame, self.out_width, self.out_height)
            path = save_image(img, ext='png')
            messagebox.showinfo('Image Saved', f'Image saved to {path}')

    def start_recording(self):
        frame = self.cam.get_frame()
        if frame is not None and not self.recording:
            img = self.renderer.frame_to_ascii_image(frame, self.out_width, self.out_height)
            self.video_recorder = VideoRecorder(img.width, img.height, fps=20)  # FPS will be updated after recording
            self.audio_recorder = AudioRecorder()
            self.video_recorder.start()
            self.audio_recorder.start()
            self.recording = True
            self.frame_timestamps = [time.time()]
            self.record_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text='Recording...')

    def stop_recording(self):
        if self.recording and self.video_recorder and self.audio_recorder:
            video_path = self.video_recorder.stop()
            audio_path = self.audio_recorder.stop()
            # Calculate actual FPS
            if len(self.frame_timestamps) > 1:
                duration = self.frame_timestamps[-1] - self.frame_timestamps[0]
                actual_fps = max(1, int((len(self.frame_timestamps) - 1) / duration))
            else:
                actual_fps = 10
            # Re-encode video with correct FPS before muxing
            self.video_recorder.reencode_fps(actual_fps)
            # Check if ffmpeg is available
            if not shutil.which('ffmpeg'):
                messagebox.showerror('FFmpeg Not Found', 'FFmpeg is required to mux audio and video. Please install ffmpeg and try again.')
                return
            final_path = self.video_recorder.mux_with_audio(audio_path)
            self.recording = False
            self.record_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.status_label.config(text=f'Saved video: {final_path}')
            messagebox.showinfo('Video Saved', f'Video with audio saved to {final_path}')

    def show_about(self):
        messagebox.showinfo('About ASCII Camera',
            'ASCII Camera\n\nA modern, minimal webcam utility that streams and records your world as ASCII art.\n\nMade with ❤️ for system analytics students!')

    def on_exit(self):
        self.cam.stop()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = ASCIICamApp(root)
    root.mainloop() 