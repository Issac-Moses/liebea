import os
import tkinter as tk
from tkinter import Label, Button, Frame
from PIL import Image, ImageTk, ImageSequence

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GIFS_DIR = os.path.join(BASE_DIR, "assets", "gifs")

class GifTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GIF Tester")
        self.root.geometry("400x550")
        self.root.configure(bg='black')
        
        # Control frame
        control_frame = Frame(self.root, bg='black')
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        Button(control_frame, text="Load Idle", command=lambda: self.load_gif("idle.gif")).pack(side=tk.LEFT, padx=5)
        Button(control_frame, text="Load Listening", command=lambda: self.load_gif("listening.gif")).pack(side=tk.LEFT, padx=5)
        Button(control_frame, text="Load Speaking", command=lambda: self.load_gif("speaking.gif")).pack(side=tk.LEFT, padx=5)
        
        # Info labels
        self.info_label = Label(self.root, text="Click a button to test GIF", bg='black', fg='white', font=('Arial', 10))
        self.info_label.pack(pady=5)
        
        self.status_label = Label(self.root, text="Status: Ready", bg='black', fg='yellow', font=('Arial', 9))
        self.status_label.pack(pady=2)
        
        # GIF display label
        self.label = Label(self.root, bg='black', bd=0, highlightthickness=0)
        self.label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.frames = []
        self.current_frame = 0
        self.animation_id = None
        self.frame_durations = []
        self.delay = 33
        
    def load_gif(self, gif_name):
        gif_path = os.path.join(GIFS_DIR, gif_name)
        
        if not os.path.exists(gif_path):
            self.info_label.config(text=f"❌ File not found: {gif_name}")
            print(f"❌ File not found: {gif_path}")
            return
        
        # Stop current animation
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
        
        self.frames = []
        
        try:
            img = Image.open(gif_path)
            
            # Display info
            info_text = f"📊 {gif_name} | Size: {img.size[0]}x{img.size[1]} | Format: {img.format} | Mode: {img.mode}"
            self.info_label.config(text=info_text)
            print(f"\n{info_text}")
            
            frame_count = 0
            for frame in ImageSequence.Iterator(img):
                # Convert to RGBA
                frame = frame.convert('RGBA')
                
                # Resize to fit display (maintain aspect ratio)
                frame.thumbnail((350, 400), Image.Resampling.LANCZOS)
                
                # Create photo
                photo = ImageTk.PhotoImage(frame)
                self.frames.append(photo)
                frame_count += 1
            
            print(f"✅ Successfully loaded {frame_count} frames")
            self.info_label.config(text=self.info_label.cget("text") + f" | Frames: {frame_count}")
            
            self.current_frame = 0
            if self.frames:
                self.animate()
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.info_label.config(text=error_msg)
            print(error_msg)
            import traceback
            traceback.print_exc()
    
    def animate(self):
        if self.frames:
            self.label.config(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.animation_id = self.root.after(50, self.animate)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("🎬 GIF Tester Started")
    print(f"📁 Looking for GIFs in: {GIFS_DIR}\n")
    
    # Check if GIFs exist
    for gif_name in ["idle.gif", "listening.gif", "speaking.gif"]:
        gif_path = os.path.join(GIFS_DIR, gif_name)
        if os.path.exists(gif_path):
            print(f"✅ Found: {gif_name}")
        else:
            print(f"❌ Missing: {gif_name}")
    
    print("\n" + "="*50)
    tester = GifTester()
    tester.run()