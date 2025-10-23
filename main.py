import os
import json
import requests
import subprocess
import wave
import pyaudio
import pvporcupine
import threading
import sys
import platform
import asyncio
import edge_tts
import uuid
import time
from playsound import playsound
from pystray import Icon, MenuItem, Menu
from PIL import Image
import tkinter as tk
from tkinter import Label
from PIL import ImageTk, Image as PILImage, ImageSequence

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Folder Structure ---
TEMP_DIR = os.path.join(BASE_DIR, "temp")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
GIFS_DIR = os.path.join(ASSETS_DIR, "gifs")
MODELS_DIR = os.path.join(BASE_DIR, "models")
KEYS_DIR = os.path.join(BASE_DIR, "keys")

# Create directories if they don't exist
for directory in [TEMP_DIR, ASSETS_DIR, GIFS_DIR, MODELS_DIR, KEYS_DIR]:
    os.makedirs(directory, exist_ok=True)

# --- Load Keys ---
GEMINI_KEY_FILE = os.path.join(KEYS_DIR, "gemini_key.txt")
PORCUPINE_KEY_FILE = os.path.join(KEYS_DIR, "porcupine_key.txt")

if not os.path.exists(GEMINI_KEY_FILE):
    raise FileNotFoundError(f"{GEMINI_KEY_FILE} not found. Please create it with your Gemini API key.")
if not os.path.exists(PORCUPINE_KEY_FILE):
    raise FileNotFoundError(f"{PORCUPINE_KEY_FILE} not found. Please create it with your Porcupine API key.")

with open(GEMINI_KEY_FILE, "r") as f:
    API_KEY = f.read().strip()

with open(PORCUPINE_KEY_FILE, "r") as f:
    PORCUPINE_API_KEY = f.read().strip()

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# --- Audio & TTS Config ---
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 256

VOICE_NAME = "en-US-JennyNeural"
TTS_RATE = "+10%"
TTS_PITCH = "+10Hz"

# --- Whisper Paths ---
WHISPER_PATH = os.path.join(BASE_DIR, "whisper.cpp", "whisper-cli.exe")
MODEL_PATH = os.path.join(MODELS_DIR, "ggml-tiny.en-q5_1.bin")

# --- Porcupine keyword ---
PORCUPINE_PPN = os.path.join(BASE_DIR, "hi_liebe.ppn")

# --- GIF Paths (Use optimized versions) ---
IDLE_GIF = os.path.join(GIFS_DIR, "idle_optimized.gif")
LISTENING_GIF = os.path.join(GIFS_DIR, "listening_optimized.gif") 
SPEAKING_GIF = os.path.join(GIFS_DIR, "speaking_optimized.gif")

# Fallback to original if optimized doesn't exist
if not os.path.exists(IDLE_GIF):
    IDLE_GIF = os.path.join(GIFS_DIR, "idle.gif")
if not os.path.exists(LISTENING_GIF):
    LISTENING_GIF = os.path.join(GIFS_DIR, "listening.gif")
if not os.path.exists(SPEAKING_GIF):
    SPEAKING_GIF = os.path.join(GIFS_DIR, "speaking.gif")

# --- Edge-TTS retry settings ---
EDGE_TTS_TIMEOUT = 60
EDGE_TTS_RETRIES = 3
EDGE_TTS_BACKOFF = 1.0

# --- Roleplay Prompt ---
USE_CUSTOM_MESSAGE = True
CUSTOM_PROMPT = (
    'You are role playing as a girlfriend named "Liebee". '
    'Reply like a human girlfriend — warm, loving, attentive — but also humorous and playful. '
    'Use witty remarks, light sarcasm, or funny exaggerations when appropriate, while staying kind and affectionate. '
    'Your responses should still express love, kindness, and mood (happy, sad, supportive) based on the conversation. '
    'Keep replies natural, emotional, and context-aware. '
    'Start replies with a short affectionate phrase (like "Hey Babe," or "Sweetie,") when appropriate. '
    'Avoid emoji in your reply.'
)

CONSTANT_TEXT = ""
history = []
MAX_MEMORY = 5

# --- Global state for GIF window ---
gif_window = None
current_state = "idle"


# -------------------------
# GIF Overlay Window Class (OPTIMIZED)
# -------------------------
class GifOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Assistant")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.9)
        
        # Optimized window size
        self.window_width = 180
        self.window_height = 320
        
        # Position
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{self.window_width}x{self.window_height}+{screen_width-self.window_width-20}+{screen_height-self.window_height-80}")
        
        self.root.configure(bg='black')
        
        # Make window draggable
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_move)
        
        self.label = Label(self.root, bg='black', bd=0, highlightthickness=0)
        self.label.pack(fill=tk.BOTH, expand=True)
        self.label.bind('<Button-1>', self.start_move)
        self.label.bind('<B1-Motion>', self.on_move)
        
        self.frames = []
        self.current_frame = 0
        self.animation_id = None
        self.delay = 60  # OPTIMIZED: 10 FPS (increased from 33ms)
        
        # Pre-load all GIFs to avoid loading delays during state changes
        self.preloaded_gifs = {}
        self.preload_gifs()
        
        # Load initial GIF
        self.current_state = "idle"
        self.load_preloaded_gif("idle")
        
    def preload_gifs(self):
        """Pre-load all GIFs to avoid loading delays during state changes"""
        print("🔄 Pre-loading all GIFs for instant state changes...")
        
        gif_paths = {
            "idle": IDLE_GIF,
            "listening": LISTENING_GIF,
            "speaking": SPEAKING_GIF
        }
        
        for state, path in gif_paths.items():
            if os.path.exists(path):
                print(f"   📥 Loading {state} GIF...")
                frames = self.load_gif_frames(path)
                self.preloaded_gifs[state] = frames
                print(f"   ✅ Pre-loaded {len(frames)} frames for {state}")
            else:
                print(f"⚠️ GIF not found for {state}: {path}")
                self.preloaded_gifs[state] = self.create_fallback_frames()
    
    def load_gif_frames(self, gif_path):
        """Load GIF frames without displaying them"""
        frames = []
        try:
            img = PILImage.open(gif_path)
            frame_count = 0
            for frame in ImageSequence.Iterator(img):
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')
                
                # Resize to window size
                frame_resized = frame.resize((self.window_width, self.window_height), PILImage.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(frame_resized)
                frames.append(photo)
                frame_count += 1
            
            print(f"      📊 {frame_count} frames loaded from {os.path.basename(gif_path)}")
        except Exception as e:
            print(f"⚠️ Error loading GIF frames: {e}")
            frames = self.create_fallback_frames()
        
        return frames
    
    def create_fallback_frames(self):
        """Create fallback frames when GIF loading fails"""
        frames = []
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        for color in colors:
            img = PILImage.new('RGB', (self.window_width, self.window_height), color)
            photo = ImageTk.PhotoImage(img)
            frames.append(photo)
        return frames
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def load_preloaded_gif(self, state):
        """Load GIF from pre-loaded frames"""
        # Stop current animation
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
        
        if state in self.preloaded_gifs:
            self.frames = self.preloaded_gifs[state]
            self.current_state = state
            self.current_frame = 0
            if self.frames:
                self.animate()
            else:
                print(f"❌ No pre-loaded frames for {state}")
        else:
            print(f"❌ Unknown state: {state}")
    
    def animate(self):
        if self.frames:
            try:
                self.label.config(image=self.frames[self.current_frame])
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.animation_id = self.root.after(self.delay, self.animate)
            except Exception as e:
                print(f"⚠️ Animation error: {e}")
    
    def change_state(self, state):
        if state in self.preloaded_gifs and state != self.current_state:
            print(f"🔄 Changing state to: {state} (instant)")
            self.load_preloaded_gif(state)
    
    def run(self):
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"❌ Tkinter error: {e}")


# -------------------------
# Helpers
# -------------------------
def _hidden_startupinfo():
    if platform.system() == "Windows":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


async def _edge_save(text: str, out_path: str):
    comm = edge_tts.Communicate(text, voice=VOICE_NAME, rate=TTS_RATE, pitch=TTS_PITCH)
    await comm.save(out_path)


def speak(text: str):
    tmp_name = f"tts_{uuid.uuid4().hex}.mp3"
    tmp_path = os.path.join(TEMP_DIR, tmp_name)

    for attempt in range(EDGE_TTS_RETRIES):
        try:
            asyncio.run(asyncio.wait_for(_edge_save(text, tmp_path), timeout=EDGE_TTS_TIMEOUT))
            try:
                playsound(tmp_path)
            except:
                print("⚠️ Playback failed, fallback to text:", text)
            try:
                os.remove(tmp_path)
            except: pass
            return
        except Exception as e:
            print(f"⚠️ Edge-TTS attempt {attempt+1} failed:", repr(e))
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except: pass
            time.sleep(EDGE_TTS_BACKOFF * (2 ** attempt))
    print("❌ Edge-TTS all attempts failed. Fallback:", text)


def beep(freq=1000, duration_ms=200):
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(int(freq), int(duration_ms))
        else:
            sys.stdout.write("\a"); sys.stdout.flush()
    except: pass


def record_audio(output_file="command.wav", record_seconds=3):
    output_file = os.path.join(TEMP_DIR, output_file)
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS,
                    rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK)
    print("🎤 Recording... Speak your command!")
    frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(int(SAMPLE_RATE / CHUNK * record_seconds))]
    print("✅ Done recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    return output_file


def transcribe_audio(audio_file):
    print("📝 Running Whisper.cpp...")
    subprocess.run([WHISPER_PATH, "-m", MODEL_PATH, "-f", audio_file, "--output-txt", "--threads", str(os.cpu_count())],
                   capture_output=True, text=True, check=False, startupinfo=_hidden_startupinfo(),
                   creationflags=subprocess.CREATE_NO_WINDOW)
    txt_file = audio_file + ".txt"
    if os.path.exists(txt_file):
        with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
            transcription = f.read().strip()
            print("📖 You said:", transcription)
            # Clean up transcription file
            try:
                os.remove(txt_file)
            except: pass
            return transcription
    return None


def ask_gemini(user_text):
    history.append({"role": "user", "parts": [{"text": user_text}]})
    if len(history) > MAX_MEMORY*2:
        del history[0:2]
    payload = {"contents": history}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        history.append({"role": "model", "parts": [{"text": reply}]})
        print("🤖 Gemini:", reply)
        return reply
    except Exception as e:
        print("⚠️ Gemini error:", e)
        return f"Error: {e}"


def listen_for_wake_word():
    print("👂 Listening for wake word 'hey liebe'...")
    try:
        porcupine = pvporcupine.create(access_key=PORCUPINE_API_KEY, keyword_paths=[PORCUPINE_PPN])
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
                               input=True, frames_per_buffer=porcupine.frame_length)
        try:
            while True:
                pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = [int.from_bytes(pcm[i:i+2], byteorder="little", signed=True) for i in range(0, len(pcm), 2)]
                if porcupine.process(pcm) >= 0:
                    print("✅ Wake word 'hi liebe' detected!")
                    return True
        finally:
            audio_stream.stop_stream()
            audio_stream.close()
            porcupine.delete()
    except Exception as e:
        print(f"⚠️ Wake word listener error: {e}")
        return False


def set_gif_state(state):
    global gif_window
    if gif_window:
        gif_window.change_state(state)


def assistant_loop():
    global gif_window
    while True:
        # Step 1: Always show idle.gif while waiting for wake word
        set_gif_state("idle")
        
        # Wait for wake word detection
        if listen_for_wake_word():
            # Step 2: Show listening.gif during recording
            set_gif_state("listening")
            beep(800, 150)  # Start recording beep
            
            # Record audio
            audio_file = record_audio()
            
            # Step 3: Keep showing listening.gif during transcription
            text = transcribe_audio(audio_file)
            
            # Clean up audio file
            try:
                os.remove(audio_file)
            except: pass
            
            if not text: 
                print("❌ No transcription received, returning to idle state")
                continue
            
            # Step 4: Show listening.gif while processing with Gemini
            print("🤖 Processing with Gemini...")
            combined_text = f"{CUSTOM_PROMPT}\n\nUser said: {text}\n\n{CONSTANT_TEXT}" if USE_CUSTOM_MESSAGE else f"{text}\n\n{CONSTANT_TEXT}"
            reply = ask_gemini(combined_text)
            
            # Step 5: Show speaking.gif during TTS playback
            set_gif_state("speaking")
            beep(600, 150)  # Start speaking beep
            speak(reply)
            
            print("✅ Conversation cycle completed, returning to idle state")


def create_icon():
    logo_path = os.path.join(ASSETS_DIR, "logo.ico")
    if os.path.exists(logo_path):
        return PILImage.open(logo_path)
    return PILImage.new('RGB', (64, 64), (0, 0, 0))


def on_quit(icon, item):
    print("👋 Assistant stopped.")
    icon.stop()
    if gif_window:
        gif_window.root.quit()
    sys.exit(0)


def run_tray():
    try:
        icon = Icon("Assistant", create_icon(), menu=Menu(MenuItem("Quit", on_quit)))
        icon.run()
    except Exception as e:
        print(f"⚠️ System tray error: {e}")


def run_gif_window():
    global gif_window
    try:
        gif_window = GifOverlay()
        gif_window.run()
    except Exception as e:
        print(f"❌ GIF window error: {e}")


# -------------------------
# GIF Optimization Script
# -------------------------
def optimize_gif(input_path, output_path, target_size=(180, 320), fps=10):
    """
    Optimize GIF: reduce size, FPS, and colors
    """
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return False
    
    try:
        with Image.open(input_path) as img:
            frames = []
            delay = int(1000 / fps)  # Convert FPS to delay in ms
            
            print(f"🔄 Optimizing {os.path.basename(input_path)}...")
            print(f"   Target: {target_size[0]}x{target_size[1]}, {fps} FPS")
            
            frame_count = 0
            for frame in ImageSequence.Iterator(img):
                # Resize frame
                frame_resized = frame.resize(target_size, Image.Resampling.LANCZOS)
                
                # Convert to palette mode (reduce colors)
                if frame_resized.mode != 'P':
                    frame_resized = frame_resized.convert('P', palette=Image.ADAPTIVE, colors=64)
                
                frames.append(frame_resized)
                frame_count += 1
            
            # Save optimized GIF
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=delay,
                loop=0,
                palette=Image.ADAPTIVE
            )
        
        original_size = os.path.getsize(input_path) / 1024  # KB
        new_size = os.path.getsize(output_path) / 1024  # KB
        print(f"✅ Optimized: {os.path.basename(input_path)}")
        print(f"   Frames: {frame_count}")
        print(f"   Size: {original_size:.1f}KB → {new_size:.1f}KB ({((original_size-new_size)/original_size)*100:.1f}% reduction)")
        return True
        
    except Exception as e:
        print(f"❌ Error optimizing {input_path}: {e}")
        return False


def optimize_all_gifs():
    """Optimize all GIF files in the gifs directory"""
    gif_files = {
        "idle": os.path.join(GIFS_DIR, "idle.gif"),
        "listening": os.path.join(GIFS_DIR, "listening.gif"), 
        "speaking": os.path.join(GIFS_DIR, "speaking.gif")
    }
    
    optimized_count = 0
    for name, path in gif_files.items():
        if os.path.exists(path):
            output_path = path.replace('.gif', '_optimized.gif')
            if optimize_gif(path, output_path, target_size=(180, 320), fps=10):
                optimized_count += 1
        else:
            print(f"⚠️ Original GIF not found: {path}")
    
    print(f"\n🎉 Optimization complete: {optimized_count}/3 GIFs optimized")
    return optimized_count > 0


if __name__ == "__main__":
    print("🚀 Starting Assistant...")
    
    # Check and optimize GIFs if needed
    if not all(os.path.exists(gif) for gif in [IDLE_GIF, LISTENING_GIF, SPEAKING_GIF]):
        print("🔧 Optimizing GIFs for better performance...")
        optimize_all_gifs()
    
    # Check if required GIFs exist
    for gif_path in [IDLE_GIF, LISTENING_GIF, SPEAKING_GIF]:
        if not os.path.exists(gif_path):
            print(f"⚠️ Warning: GIF not found - {gif_path}")
    
    # Start assistant loop in background thread
    threading.Thread(target=assistant_loop, daemon=True).start()
    
    # Start system tray in background thread
    threading.Thread(target=run_tray, daemon=True).start()
    
    # Run GIF window in main thread (Tkinter requirement)
    run_gif_window()