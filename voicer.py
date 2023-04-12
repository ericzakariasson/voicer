import os
import time
import threading
import rumps
import openai
import speech_recognition as sr
from pynput import keyboard

# OpenAI settings
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize speech recognizer and microphone
recognizer = sr.Recognizer()
microphone = sr.Microphone()

controller = keyboard.Controller()
KEY = keyboard.Key.caps_lock

# Global Key Listener
class GlobalKeyListener:
    def __init__(self, callback):
        self.callback = callback
        self.key_press_count = 0
        self.timeout = 0.5  # Time interval in seconds
        self.timer = None

    def reset_key_press_count(self):
        self.key_press_count = 0

    def on_press(self, key):
        if key == KEY:
            self.key_press_count += 1
            if self.timer is not None:
                self.timer.cancel()

            if self.key_press_count == 2:
                self.callback()
                self.key_press_count = 0
            else:
                self.timer = threading.Timer(self.timeout, self.reset_key_press_count)
                self.timer.start()

# Helper functions
def type_text(text):
    for char in text:
        if char == '\n':
            controller.press(keyboard.Key.enter)
            controller.release(keyboard.Key.enter)
        else:
            controller.type(char)
        time.sleep(0.01)

# Voicer App
class Voicer(rumps.App):
    def __init__(self, *args, **kwargs):
        super(Voicer, self).__init__(*args, **kwargs)
        self.menu_item = rumps.MenuItem("Record")
        self.menu_item.set_callback(self.start_transcription)
        self.language_submenu = self.create_language_submenu()
        self.menu = [self.menu_item, self.language_submenu]
        
        self.key_listener = GlobalKeyListener(callback=self.start_transcription)

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)

    def create_language_submenu(self):
        language_submenu = rumps.MenuItem("Language")
        languages = ["en", "sv"]  # Add more languages as needed
        selected_language = languages[0]
        for language in languages:
            language_item = rumps.MenuItem(language, callback=self.select_language)
            if language == selected_language:
                language_item.state = 1
            language_submenu.add(language_item)
        return language_submenu

    def select_language(self, sender):
        for language_item in self.language_submenu.values():
            language_item.state = 0
        sender.state = 1
        self.selected_language = sender.title

    def start_transcription(self, sender=None):
        self.menu_item.title = 'Recording'
        with microphone as source:
            print("Listening...")
            rumps.notification(title="voicer ⚫️", subtitle="Recording...", message="    ", sound=False)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        transcription = recognizer.recognize_whisper_api(audio, api_key=openai.api_key)
        print(f"Transcription: {transcription}")
        type_text(transcription)

# Main function
def main():
    app = Voicer("voicer ⚫️")
    with keyboard.Listener(on_press=app.key_listener.on_press) as listener:
        app.run()
        listener.join()

if __name__ == "__main__":
    main()
