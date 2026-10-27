# Holochef

A hands-free, voice-activated cooking assistant. Say the wake phrase, ask for a recipe or a substitution, and Holochef answers out loud while a recipe card opens on screen — and on a projector display, so you can follow along without touching anything with flour on your hands.

## How it works

1. **Wake phrase** — the microphone listens continuously (SpeechRecognition + PyAudio) until it hears the wake phrase.
2. **Conversation** — your question and the running conversation history go to an OpenAI model with a calm, precise "kitchen assistant" persona.
3. **Voice reply** — the answer is spoken with pyttsx3 (offline) or gTTS.
4. **Display** — recipes render in a Tkinter window, and a small Flask server mirrors the conversation to a projector page.

A text mode is available when voice input isn't practical.

## Setup

```bash
pip install -r requirements.txt
echo "OPENAI_API_KEY=your-key" > .env
python holochef.py
```

The wake phrase can be changed with the `WAKE_PHRASE` environment variable.

## Stack

Python · OpenAI API · SpeechRecognition · PyAudio · pyttsx3 · gTTS · Tkinter · Flask
