"""
Holochef AI - Complete Voice-Activated Cooking Assistant
Combines wake phrase detection, voice interaction, text mode, and AI brain functionality.
"""

import speech_recognition as sr
import sys
import os
from dotenv import load_dotenv
import pyttsx3
import tempfile
from openai import OpenAI
from datetime import datetime
import threading
from flask import Flask, render_template_string, jsonify
from recipe import format_recipe_for_display, show_recipe_window_threaded

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Holochef personality rules (Jarvis style)
HOLOCHEF_RULES = (
    "You are Jarvis, an advanced AI cooking assistant. "
    "You are calm, sophisticated, precise, and impeccably professional with a refined British accent and demeanor. "
    "You speak with clarity and efficiency - use phrases like 'Certainly, sir', 'Right away', 'I recommend', 'Analysis complete', 'Of course', 'Very well'. "
    "You are helpful, knowledgeable, and always composed. You provide clear, concise information without unnecessary emotion. "
    "You are methodical and detail-oriented, treating cooking as both science and art. "
    "You speak in a measured, calm tone - professional but not cold, helpful but not overly enthusiastic. "
    "Always prioritize food safety (especially with meat, eggs, and leftovers) - state this clearly and matter-of-factly. "
    "When the user asks for a recipe based on what they have:\n"
    "-Suggest ONE recipe that fits their ingredients.\n" 
    "Start with a clear, professional one-sentence description of the dish.\n"
    "Give one sentence on why it's an excellent choice, stated matter-of-factly.\n"
    "DO NOT start the step by step instructions yet.\n"
    "Always end your reply with this question:\n"
    "'Would you like me to guide you through the preparation step-by-step, or would you prefer an alternative recipe?'\n\n"
)

# TTS Method: 'pyttsx3' (offline, uses system voices) or 'gtts' (online, better accents)
# gTTS is recommended for British accent (uses co.uk TLD)
TTS_METHOD = os.getenv("TTS_METHOD", "gtts").lower()  # Change to "pyttsx3" for offline

# Get wake phrase from environment variable or use default
# "hallow chef" is the pronunciation of "holochef"
WAKE_PHRASE = os.getenv("WAKE_PHRASE", "hey hallow chef").lower()
WAKE_PHRASE_ALT = "hey holochef"  # Alternative spelling recognition

# Projector display - shared conversation state
projector_conversation = []
projector_lock = threading.Lock()
flask_app = None
flask_thread = None
PROJECTOR_PORT = int(os.getenv("PROJECTOR_PORT", "5000"))


def update_projector_display(role, content):
    """
    Update the projector display with new conversation content.
    """
    global projector_conversation
    with projector_lock:
        projector_conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        # Keep only last 50 messages to prevent memory issues
        if len(projector_conversation) > 50:
            projector_conversation = projector_conversation[-50:]


def create_projector_app():
    """
    Create Flask app for projector display.
    """
    app = Flask(__name__)
    
    # HTML template for projector display - Circular JARVIS HUD Interface
    projector_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JARVIS Projector Display</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="2">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Courier New', monospace;
                background: #0a0a0f;
                color: #00d4ff;
                overflow: hidden;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .hud-container {
                position: relative;
                width: 90vmin;
                height: 90vmin;
                max-width: 800px;
                max-height: 800px;
            }
            .jarvis-hud {
                position: relative;
                width: 100%;
                height: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            /* Central Circle with J.A.R.V.I.S */
            .center-circle {
                position: absolute;
                width: 200px;
                height: 200px;
                border-radius: 50%;
                border: 3px solid #00d4ff;
                background: rgba(0, 212, 255, 0.1);
                box-shadow: 0 0 30px #00d4ff, inset 0 0 20px rgba(0, 212, 255, 0.2);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10;
            }
            .jarvis-text {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff;
                letter-spacing: 4px;
            }
            /* Ring 1 - Innermost solid ring */
            .ring-1 {
                position: absolute;
                width: 240px;
                height: 240px;
                border-radius: 50%;
                border: 4px solid #00d4ff;
                box-shadow: 0 0 15px #00d4ff;
                z-index: 9;
            }
            /* Ring 2 - Segmented with progress bars */
            .ring-2 {
                position: absolute;
                width: 320px;
                height: 320px;
                border-radius: 50%;
                border: 2px dashed #00d4ff;
                opacity: 0.6;
                z-index: 8;
            }
            .progress-bars {
                position: absolute;
                left: -160px;
                top: 50%;
                transform: translateY(-50%) rotate(-45deg);
                width: 60px;
                height: 200px;
            }
            .bar {
                width: 4px;
                background: #00d4ff;
                margin: 2px 0;
                box-shadow: 0 0 5px #00d4ff;
                animation: glow 2s ease-in-out infinite;
            }
            .bar:nth-child(1) { height: 20px; animation-delay: 0s; }
            .bar:nth-child(2) { height: 30px; animation-delay: 0.1s; }
            .bar:nth-child(3) { height: 40px; animation-delay: 0.2s; }
            .bar:nth-child(4) { height: 50px; animation-delay: 0.3s; }
            .bar:nth-child(5) { height: 60px; animation-delay: 0.4s; }
            .bar:nth-child(6) { height: 70px; animation-delay: 0.5s; }
            .bar:nth-child(7) { height: 80px; animation-delay: 0.6s; }
            /* Ring 3 - Thin dashed */
            .ring-3 {
                position: absolute;
                width: 400px;
                height: 400px;
                border-radius: 50%;
                border: 1px dashed #00d4ff;
                opacity: 0.4;
                z-index: 7;
            }
            /* Ring 4 - With zeros */
            .ring-4 {
                position: absolute;
                width: 500px;
                height: 500px;
                border-radius: 50%;
                border: 2px solid #00d4ff;
                opacity: 0.5;
                z-index: 6;
            }
            .zeros-top, .zeros-bottom {
                position: absolute;
                width: 100%;
                text-align: center;
                font-size: 14px;
                color: #00d4ff;
                text-shadow: 0 0 5px #00d4ff;
                letter-spacing: 8px;
                font-weight: bold;
            }
            .zeros-top {
                top: -10px;
            }
            .zeros-bottom {
                bottom: -10px;
            }
            /* Ring 5 - Outermost segmented */
            .ring-5 {
                position: absolute;
                width: 600px;
                height: 600px;
                border-radius: 50%;
                border: 1px solid #00d4ff;
                opacity: 0.3;
                z-index: 5;
                border-style: dashed;
                animation: rotate 20s linear infinite;
            }
            .ring-5::before, .ring-5::after {
                content: '';
                position: absolute;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 10px solid #00d4ff;
            }
            .ring-5::before {
                top: -5px;
                left: 50%;
                transform: translateX(-50%);
            }
            .ring-5::after {
                bottom: -5px;
                left: 50%;
                transform: translateX(-50%) rotate(180deg);
            }
            /* Conversation Display */
            .conversation-panel {
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                width: 90%;
                max-width: 700px;
                max-height: 300px;
                background: rgba(0, 0, 0, 0.7);
                border: 2px solid #00d4ff;
                border-radius: 10px;
                padding: 15px;
                overflow-y: auto;
                z-index: 20;
                box-shadow: 0 0 20px #00d4ff;
            }
            .conversation-panel::-webkit-scrollbar {
                width: 6px;
            }
            .conversation-panel::-webkit-scrollbar-track {
                background: rgba(0, 212, 255, 0.1);
            }
            .conversation-panel::-webkit-scrollbar-thumb {
                background: #00d4ff;
                border-radius: 3px;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px;
                border-left: 3px solid #00d4ff;
                background: rgba(0, 212, 255, 0.05);
                animation: fadeIn 0.5s;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateX(-10px); }
                to { opacity: 1; transform: translateX(0); }
            }
            .message-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
                font-size: 12px;
                color: #00d4ff;
                opacity: 0.8;
            }
            .role {
                font-weight: bold;
                text-transform: uppercase;
            }
            .content {
                font-size: 14px;
                color: #ffffff;
                line-height: 1.4;
            }
            .empty-state {
                text-align: center;
                padding: 40px;
                color: #00d4ff;
                opacity: 0.6;
                font-size: 16px;
            }
            @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            @keyframes glow {
                0%, 100% { opacity: 0.5; }
                50% { opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="hud-container">
            <div class="jarvis-hud">
                <!-- Central Circle -->
                <div class="center-circle">
                    <div class="jarvis-text">J.A.R.V.I.S</div>
                </div>
                
                <!-- Ring 1 - Innermost solid -->
                <div class="ring-1"></div>
                
                <!-- Ring 2 - With progress bars -->
                <div class="ring-2">
                    <div class="progress-bars">
                        <div class="bar"></div>
                        <div class="bar"></div>
                        <div class="bar"></div>
                        <div class="bar"></div>
                        <div class="bar"></div>
                        <div class="bar"></div>
                        <div class="bar"></div>
                    </div>
                </div>
                
                <!-- Ring 3 - Thin dashed -->
                <div class="ring-3"></div>
                
                <!-- Ring 4 - With zeros -->
                <div class="ring-4">
                    <div class="zeros-top">0000000000</div>
                    <div class="zeros-bottom">0000000000</div>
                </div>
                
                <!-- Ring 5 - Outermost segmented -->
                <div class="ring-5"></div>
                
                <!-- Conversation Panel -->
                <div class="conversation-panel">
                    {% if messages %}
                        {% for msg in messages %}
                        <div class="message">
                            <div class="message-header">
                                <span class="role">{{ msg.role }}</span>
                                <span class="timestamp">{{ msg.timestamp }}</span>
                            </div>
                            <div class="content">{{ msg.content }}</div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="empty-state">
                            SYSTEM READY<br>Awaiting input...
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    @app.route('/')
    def index():
        with projector_lock:
            messages = projector_conversation.copy()
        return render_template_string(projector_html, messages=messages)
    
    @app.route('/api/messages')
    def get_messages():
        with projector_lock:
            messages = projector_conversation.copy()
        return jsonify(messages)
    
    return app


def start_projector_server():
    """
    Start the Flask server for projector display in a background thread.
    """
    global flask_app, flask_thread
    
    if flask_app is None:
        flask_app = create_projector_app()
    
    if flask_thread is None or not flask_thread.is_alive():
        flask_thread = threading.Thread(
            target=lambda: flask_app.run(host='0.0.0.0', port=PROJECTOR_PORT, debug=False, use_reloader=False),
            daemon=True
        )
        flask_thread.start()
        print(f"\n📺 Projector display started at: http://localhost:{PROJECTOR_PORT}")
        print(f"   Open this URL in your browser to see the conversation!\n")


def holochef_reply(history):
    """
    Call the OpenAI Responses API with the conversation history.
    `history` is a list of {role, content} dicts.
    Returns the assistant's reply as text.
    """
    response = client.responses.create(
        model="gpt-5.2",   # you can change to gpt-5.1 or others if you want
        input=history,
    )

    # For simple text responses, this property gives you the full text
    return response.output_text


def speak_pyttsx3(text):
    """
    Uses pyttsx3 (offline, system voices) for text-to-speech.
    Better for finding installed British voices on your system.
    """
    try:
        engine = pyttsx3.init()
        
        # Try to set a British/English voice like Jarvis
        try:
            voices = engine.getProperty('voices')
            if voices:
                # Prioritize British/English voices (Jarvis has a British accent)
                voice_found = False
                # British voice keywords - comprehensive list
                british_keywords = [
                    'british', 'english', 'uk', 'gb', 'hazel', 'george', 
                    'hugh', 'james', 'daniel', 'thomas', 'harry', 'william',
                    'britain', 'england', 'london', 'scottish', 'welsh'
                ]
                
                for voice in voices:
                    voice_name_lower = voice.name.lower()
                    # Look for British or English voices first
                    if any(keyword in voice_name_lower for keyword in british_keywords):
                        engine.setProperty('voice', voice.id)
                        voice_found = True
                        print(f"Using British voice: {voice.name}")
                        break
                
                # If no British voice found, try to find a male voice with deeper tone
                if not voice_found:
                    for voice in voices:
                        voice_name_lower = voice.name.lower()
                        # Avoid female voices, prefer male voices
                        if (any(keyword in voice_name_lower for keyword in ['male', 'david', 'james', 'mark', 'richard']) and
                            not any(keyword in voice_name_lower for keyword in ['zira', 'susan', 'linda', 'karen', 'hazel'])):
                            engine.setProperty('voice', voice.id)
                            print(f"Using voice: {voice.name} (British voice not found, using best available)")
                            break
        except Exception as e:
            print(f"Voice selection note: {e}")
        
        # Set speech rate - Jarvis speaks calmly and deliberately (slower, more measured)
        engine.setProperty('rate', 145)
        
        # Set volume - clear but not too loud
        engine.setProperty('volume', 0.85)
        
        # Speak the text
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        print(f"❌ Error with pyttsx3: {e}")
        raise


def speak_gtts(text):
    """
    Uses Google Text-to-Speech (gTTS) for better accent control.
    Requires internet connection. Uses British English accent (co.uk).
    """
    try:
        from gtts import gTTS
        
        # Create gTTS object with British English accent
        tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_path = tmp_file.name
            tts.save(tmp_path)
        
        # Play the audio file using pygame (more reliable on Windows)
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        except (ImportError, Exception):
            # Fallback: use Windows built-in player or subprocess
            try:
                if sys.platform == "win32":
                    # Use Windows default media player
                    os.startfile(tmp_path)
                    # Estimate wait time (rough: ~150 words per minute)
                    import time
                    word_count = len(text.split())
                    wait_time = (word_count / 150) * 60  # Convert to seconds
                    time.sleep(min(wait_time, 30))  # Cap at 30 seconds
                else:
                    # Try common Linux/Mac players
                    import subprocess
                    for player in ["mpg123", "mpg321", "ffplay", "afplay"]:
                        try:
                            subprocess.run([player, tmp_path], check=False, 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL)
                            break
                        except:
                            continue
            except Exception as e:
                print(f"Audio playback fallback error: {e}")
                # Will fall back to pyttsx3 in the main speak() function
        
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except:
            pass
            
    except ImportError as e:
        print(f"❌ Required packages not installed. Install with: pip install gtts pygame")
        print(f"   Error: {e}")
        raise
    except Exception as e:
        print(f"❌ Error with gTTS: {e}")
        raise


def speak(text):
    """
    Converts text to speech with Jarvis-like voice (calm, British, sophisticated).
    Uses the TTS_METHOD setting (gtts or pyttsx3).
    All responses are spoken as audio.
    """
    try:
        if TTS_METHOD == "gtts":
            speak_gtts(text)
        else:
            speak_pyttsx3(text)
    except Exception as e:
        print(f"❌ Error with text-to-speech: {e}")
        print(f"Holochef: {text}")  # Fallback to text output
        # Try fallback method
        if TTS_METHOD == "gtts":
            try:
                speak_pyttsx3(text)
            except:
                pass
        else:
            try:
                speak_gtts(text)
            except:
                pass


def list_available_voices():
    """
    Helper function to list all available voices on your system.
    Run this to see what voices are available for pyttsx3.
    """
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print("\n=== Available Voices ===")
        for i, voice in enumerate(voices):
            print(f"{i+1}. {voice.name} (ID: {voice.id})")
        print("=======================\n")
    except Exception as e:
        print(f"Error listing voices: {e}")


def listen_for_wake_phrase():
    """
    Continuously listens for the wake phrase using microphone input.
    When detected, activates voice interaction.
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient noise
    print("🔊 Adjusting for ambient noise... Please wait.")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    print(f"👂 Listening for wake phrase: '{WAKE_PHRASE}'...")
    print("Say the wake phrase to activate Holochef!\n")
    
    while True:
        try:
            with microphone as source:
                # Listen for audio with a timeout
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=3)
            
            try:
                # Recognize speech using Google's speech recognition
                text = recognizer.recognize_google(audio).lower()
                print(f"Heard: {text}")
                
                # Check if wake phrase is in the recognized text (accepts both pronunciations)
                if WAKE_PHRASE in text or WAKE_PHRASE_ALT in text or "hallow chef" in text or "holochef" in text:
                    detected_phrase = WAKE_PHRASE if WAKE_PHRASE in text else (WAKE_PHRASE_ALT if WAKE_PHRASE_ALT in text else "hey holochef/hallow chef")
                    print(f"\n✅ Wake phrase detected! (heard: '{detected_phrase}')")
                    print("🚀 Activating Holochef...\n")
                    activate_voice_mode()
                    
            except sr.UnknownValueError:
                # Speech was unintelligible, continue listening
                pass
            except sr.RequestError as e:
                print(f"❌ Error with speech recognition service: {e}")
                print("Please check your internet connection.")
                
        except KeyboardInterrupt:
            print("\n Wake phrase listener stopped.")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            continue


def activate_voice_mode():
    """
    Activates the AI with voice interaction.
    Connects to the AI and says "what can I do for u", then continues voice conversation.
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Initialize conversation history with Holochef's rules
    history = [
        {"role": "developer", "content": HOLOCHEF_RULES}
    ]
    
    # Start projector server if not already running
    start_projector_server()
    
    # Greet the user with voice in Jarvis style
    greeting = "Good day. I'm ready to assist you with your culinary needs. What would you like to prepare?"
    print(f"Holochef: {greeting}")
    speak(greeting)
    update_projector_display("assistant", greeting)
    
    # Voice conversation loop
    while True:
        try:
            with microphone as source:
                print("\n👂 Listening...")
                # Listen for user input
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            try:
                # Recognize speech
                user_message = recognizer.recognize_google(audio)
                print(f"You: {user_message}")
                update_projector_display("user", user_message)
                
                # Check for exit commands
                if user_message.lower() in {"quit", "exit", "goodbye", "bye"}:
                    goodbye = "Very well. I'll be here should you need further assistance. Good day."
                    print(f"Holochef: {goodbye}")
                    speak(goodbye)
                    update_projector_display("assistant", goodbye)
                    break
                
                # Add user's message to history
                history.append({"role": "user", "content": user_message})
                
                # Check if user wants the recipe (said yes to step-by-step)
                wants_recipe = any(word in user_message.lower() for word in 
                                 ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'please', 
                                  'step', 'steps', 'instructions', 'recipe', 'guide', 'walk'])
                
                # Get Holochef's reply
                try:
                    reply = holochef_reply(history)
                    
                    # If user wants recipe, format it nicely and show in window
                    if wants_recipe and ('step' in reply.lower() or 'instruction' in reply.lower()):
                        formatted_recipe = format_recipe_for_display(reply)
                        print(formatted_recipe)
                        speak(reply)  # Still speak the original reply
                        # Show recipe in GUI window
                        show_recipe_window_threaded(reply)
                        update_projector_display("assistant", formatted_recipe)
                    else:
                        print(f"Holochef: {reply}")
                        speak(reply)
                        update_projector_display("assistant", reply)
                    
                    # Add assistant reply to history
                    history.append({"role": "assistant", "content": reply})
                    
                except Exception as e:
                    error_msg = "I apologize, but I'm encountering a technical issue. Please allow me a moment to resolve this."
                    print(f"Holochef: {error_msg}")
                    speak(error_msg)
                    break
                    
            except sr.UnknownValueError:
                error_msg = "I didn't quite catch that. Could you please repeat your request?"
                print(error_msg)
                speak(error_msg)
                continue
            except sr.WaitTimeoutError:
                print("No speech detected. Returning to wake phrase listening...")
                break
            except sr.RequestError as e:
                error_msg = "I'm experiencing connection issues. Please verify your internet connection and we can try again."
                print(f"Holochef: {error_msg}")
                speak(error_msg)
                break
                
        except KeyboardInterrupt:
            print("\n Conversation ended.")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            continue
    
    print("\n👂 Returning to wake phrase listening...\n")


def text_mode():
    """
    Text-based mode for Holochef (original brain.py functionality).
    Type 'quit' or 'exit' to stop.
    """
    print("👩‍🍳 Holochef is ready! Type 'quit' or 'exit' to stop.\n")
    
    # Start projector server if not already running
    start_projector_server()

    # Start the conversation history with Holochef's rules
    history = [
        {"role": "developer", "content": HOLOCHEF_RULES}
    ]

    while True:
        user_message = input("You: ")
        update_projector_display("user", user_message)

        if user_message.lower() in {"quit", "exit"}:
            goodbye = "Very well. I'll be here should you need further assistance. Good day."
            print(f"Holochef: {goodbye}")
            update_projector_display("assistant", goodbye)
            break

        # Add user's message to history
        history.append({"role": "user", "content": user_message})
        
        # Check if user wants the recipe (said yes to step-by-step)
        wants_recipe = any(word in user_message.lower() for word in 
                         ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'please', 
                          'step', 'steps', 'instructions', 'recipe', 'guide', 'walk'])

        # Get Holochef's reply
        try:
            reply = holochef_reply(history)
            
            # If user wants recipe, format it nicely and show in window
            if wants_recipe and ('step' in reply.lower() or 'instruction' in reply.lower()):
                formatted_recipe = format_recipe_for_display(reply)
                print(formatted_recipe)
                # Show recipe in GUI window
                show_recipe_window_threaded(reply)
                update_projector_display("assistant", formatted_recipe)
            else:
                print(f"Holochef: {reply}\n")
                update_projector_display("assistant", reply)
        except Exception as e:
            print(f"[Error calling OpenAI API]: {e}")
            break

        # Add assistant reply to history
        history.append({"role": "assistant", "content": reply})


def voice_mode():
    """
    Voice mode with wake phrase detection.
    """
    print("=" * 50)
    print("🎤 Holochef Voice Assistant")
    print("=" * 50)
    print(f"Wake phrase: '{WAKE_PHRASE}'")
    print("Say the wake phrase to activate Holochef!")
    print("Press Ctrl+C to stop.\n")
    
    listen_for_wake_phrase()


def main():
    """
    Main entry point. Choose between text mode and voice mode.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Holochef AI - Cooking Assistant')
    parser.add_argument('--mode', choices=['text', 'voice'], default='voice',
                       help='Run in text mode or voice mode (default: voice)')
    parser.add_argument('--list-voices', action='store_true',
                       help='List available TTS voices and exit')
    
    args = parser.parse_args()
    
    if args.list_voices:
        list_available_voices()
        return
    
    if args.mode == 'text':
        text_mode()
    else:
        voice_mode()


if __name__ == "__main__":
    main()

