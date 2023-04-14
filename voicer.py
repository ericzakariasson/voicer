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

languages = [{
    "name": "English",
    "code": "en-US",
    "icon": "🇺🇸",
}, {
    "name": "Swedish",
    "code": "sv-SE",
    "icon": "🇸🇪",
}]

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
        super(Voicer, self).__init__(title="🔘 voicer", name="voicer", *args, **kwargs)
        self.languages = languages
        self.selected_language = self.languages[0]

        self.menu_item = rumps.MenuItem("Record")
        self.menu_item.set_callback(self.start_transcription)
        self.language_submenu = self.create_language_submenu()
        self.menu = [self.menu_item, self.language_submenu]

        self.key_listener = GlobalKeyListener(callback=self.start_transcription)

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)

    def create_language_submenu(self):
        language_submenu = rumps.MenuItem("Language")
        for language in self.languages:
            language_item = rumps.MenuItem(title=f"{language['icon']} {language['name']}", callback=lambda sender, lang=language: self.select_language(sender, lang))
            if language['code'] == self.selected_language['code']:
                language_item.state = 1
            language_submenu.add(language_item)
        return language_submenu

    def select_language(self, sender, language):
        for language_item in self.language_submenu.values():
            language_item.state = 0
        sender.state = 1
        self.selected_language = language

    def start_transcription(self, sender=None):
        self.menu_item.title = 'Recording'
        try:
            with microphone as source:
                print("Listening...")
                rumps.notification(title="voicer", subtitle=f"Recording ({self.selected_language['icon']})", message="", sound=False)
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
            if self.selected_language['code'] != "en-US":
                print(f"Model: Google ({self.selected_language['name']})")
                transcription = recognizer.recognize_google(audio, language=self.selected_language['code'])
            else:
                print(f"Model: Whisper")
                transcription = recognizer.recognize_whisper_api(audio, api_key=openai.api_key)
            print(f"Transcription: {transcription}")
            type_text(transcription)
        except Exception as e:
            print(f"An error occurred: {e}")
            rumps.notification(title="voicer", subtitle="An error occurred", message=str(e), sound=False)
        finally:
            self.menu_item.title = 'Record'



# Main function
def main():
    app = Voicer()
    with keyboard.Listener(on_press=app.key_listener.on_press) as listener:
        app.run()
        listener.join()

if __name__ == "__main__":
    main()
