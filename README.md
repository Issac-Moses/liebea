# 🎤 Liebee - AI Cʜᴀʀᴇᴄᴛᴇʀ Rᴇʟᴇᴀsᴇᴅ!! 

A voice-activated AI girlfriend assistant with animated GIF overlay, powered by liebea AI Model, Whisper.cpp, and Porcupine wake word detection.

## ✨ Features

- **Wake Word Detection**: Activates with "Hey Liebe" using Porcupine
- **Speech-to-Text**: Local transcription using Whisper.cpp
- **AI Conversation**: Natural, roleplay-based responses via Google Gemini 2.5 Flash
- **Text-to-Speech**: High-quality voice synthesis using Edge-TTS
- **Animated Overlay**: Draggable GIF window showing assistant states (idle, listening, speaking)
- **System Tray**: Runs minimized in background with easy quit option
- **Memory**: Maintains conversation context (last 5 exchanges)

## 📋 Prerequisites

### System Requirements
- **Windows** (required for some features like beep sounds)
- **Python 3.8+**
- **Microphone** and **speakers/headphones**

### API Keys Required
1. **Porcupine API Key** - Get from [Picovoice Console](https://console.picovoice.ai/)

### External Dependencies
1. **Whisper.cpp** - Download and compile:
```bash
   git clone https://github.com/ggerganov/whisper.cpp
   cd whisper.cpp
   # Build according to your platform
```
   Place `whisper-cli.exe` in `whisper.cpp/` folder

2. **Whisper Model** - Download tiny English model:
```bash
   # Download ggml-tiny.en-q5_1.bin
   # Place in models/ folder
```

3. **Porcupine Wake Word File** - Create custom wake word "hi liebe":
   - Visit [Picovoice Console](https://console.picovoice.ai/)
   - Create wake word phrase "hi liebe"
   - Download `.ppn` file and rename to `hi_liebe.ppn`
   - Place in project root directory

## 📁 Project Structure
```
project/
├── assistant.py              # Main script
├── hi_liebe.ppn             # Porcupine wake word file
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── assets/
│   ├── logo.ico            # System tray icon
│   └── gifs/
│       ├── idle.gif        # Idle state animation
│       ├── listening.gif   # Listening state animation
│       ├── speaking.gif    # Speaking state animation
│       └── *_optimized.gif # Auto-generated optimized versions
├── keys/
│   ├── gemini_key.txt      # Your Gemini API key
│   └── porcupine_key.txt   # Your Porcupine API key
├── models/
│   └── ggml-tiny.en-q5_1.bin  # Whisper model
├── whisper.cpp/
│   └── whisper-cli.exe     # Whisper executable
└── temp/                   # Auto-generated temporary files
```

## 🚀 Installation

### 1. Clone or Download the Project
```bash
git clone <your-repo-url>
cd liebee-assistant
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up API Keys
Create the following files in `keys/` directory:

**keys/porcupine_key.txt**
```
your_porcupine_api_key_here
```

### 4. Add Required Files
- Place `whisper-cli.exe` in `whisper.cpp/` folder
- Place `ggml-tiny.en-q5_1.bin` in `models/` folder
- Place `hi_liebe.ppn` in project root
- Add GIF files to `assets/gifs/` folder:
  - `idle.gif`
  - `listening.gif`
  - `speaking.gif`

### 5. (Optional) Add Custom Logo
Place `logo.ico` in `assets/` folder for system tray icon

## 🎮 Usage

### Starting the Assistant
```bash
python assistant.py
```

### How to Use
1. **Wait for Wake Word**: Say "Hey Liebe" to activate
2. **Speak Command**: After beep, speak for ~3 seconds
3. **Listen to Response**: Assistant will respond with voice
4. **Repeat**: Returns to wake word listening automatically

### Visual States
- **Idle (Pink)**: Waiting for wake word
- **Listening (Green)**: Recording your voice
- **Speaking (Blue)**: Assistant is responding

### Controls
- **Drag Window**: Click and drag the GIF overlay to reposition
- **Quit**: Right-click system tray icon → Quit

## ⚙️ Configuration

Edit the following variables in `assistant.py`:

### Voice Settings
```python
VOICE_NAME = "en-US-JennyNeural"  # TTS voice
TTS_RATE = "+10%"                 # Speech rate
TTS_PITCH = "+10Hz"               # Voice pitch
```

### Recording Settings
```python
record_seconds = 3  # Recording duration in seconds
```

### Memory Settings
```python
MAX_MEMORY = 5  # Number of conversation turns to remember
```

### Custom Personality
Modify the `CUSTOM_PROMPT` variable to change assistant personality:
```python
CUSTOM_PROMPT = (
    'You are role playing as a girlfriend named "Liebee". '
    'Reply like a human girlfriend — warm, loving, attentive...'
)
```

## 🎨 GIF Optimization

The script automatically optimizes GIFs on first run:
- Reduces file size by ~70%
- Lowers FPS to 10 for smooth performance
- Resizes to 180x320 pixels
- Reduces color palette to 64 colors

Optimized files are saved as `*_optimized.gif` and used automatically.

## 🔧 Troubleshooting

### Common Issues

**"No module named 'pyaudio'"**
- Windows: `pip install pipwin && pipwin install pyaudio`
- Linux: `sudo apt-get install python3-pyaudio`

**"Wake word not detected"**
- Check microphone permissions
- Verify `hi_liebe.ppn` file exists
- Test microphone with other apps

**"Whisper transcription failed"**
- Ensure `whisper-cli.exe` exists and is executable
- Verify model file `ggml-tiny.en-q5_1.bin` is in `models/`
- Check audio recording quality

**"TTS playback failed"**
- Install system audio codecs (MP3 support)
- Check speaker/headphone connection
- Verify Edge-TTS is working: `edge-tts --list-voices`

**"GIF window not appearing"**
- Check if GIF files exist in `assets/gifs/`
- Verify file paths are correct
- Try running with administrator privileges

## 📝 Notes

- First run will take longer due to GIF optimization
- Internet connection required for Gemini API and Edge-TTS
- Whisper.cpp runs locally (no internet needed for transcription)
- Recording duration is fixed at 3 seconds (configurable)
- Conversation history limited to last 5 exchanges to manage token usage

## 🔐 Privacy & Security

- API keys stored locally in plain text (secure your `keys/` folder)
- Audio files temporarily saved, then deleted after transcription
- Conversation history stored in memory only (cleared on restart)
- No data sent to external servers except Gemini API

## 📄 License

This project is open source. Please ensure compliance with:
- Google Gemini API Terms of Service
- Picovoice Porcupine Licensing
- Whisper.cpp License
- Edge-TTS Terms of Use

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for improvements.

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) - AI conversation
- [Picovoice Porcupine](https://picovoice.ai/) - Wake word detection
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Speech recognition
- [Edge-TTS](https://github.com/rany2/edge-tts) - Text-to-speech
- Python community for amazing libraries

---

Made with ❤️ for AI assistants and girlfriend roleplay enthusiasts
