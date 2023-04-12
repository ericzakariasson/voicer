import rumps
import pyaudio
import wave
import threading
import time
import os
import openai
from pynput import keyboard
import threading


# Recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
KEY = keyboard.Key.caps_lock

# OpenAI settings
openai.api_key = os.getenv("OPENAI_API_KEY")

# Global variables for recording
audio = pyaudio.PyAudio()
stream = None
frames = []
is_recording = False


class GlobalKeyListener:
    def __init__(self, app):
        self.app = app
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
                self.app.toggle_recording(None)
                self.key_press_count = 0
            else:
                self.timer = threading.Timer(self.timeout, self.reset_key_press_count)
                self.timer.start()


controller = keyboard.Controller()

def type_text(text):
    for char in text:
        if char == '\n':
            controller.press(keyboard.Key.enter)
            controller.release(keyboard.Key.enter)
        else:
            controller.type(char)
        time.sleep(0.01)


def start_recording():
    print("Recording...")
    global stream, frames
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    while is_recording:
        data = stream.read(CHUNK)
        frames.append(data)


def save_audio_file(filename='output.wav'):
    print("Saving audio file...")
    global stream, frames

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    stream.stop_stream()
    stream.close()


def convert_audio_to_text(selected_language, filename='output.wav'):
    print("Converting audio to text...")
    # return "Hello World"
    with open(filename, 'rb') as audio_file:
        response = openai.Audio.transcribe(model="whisper-1", file=audio_file, language=selected_language)

    print("Response: ")
    print(response)
    return response.text


class Voicer(rumps.App):
    def __init__(self, *args, **kwargs):
        super(Voicer, self).__init__(*args, **kwargs)
        self.menu_item = rumps.MenuItem("Record")
        self.menu_item.set_callback(self.toggle_recording)
         # Language submenu
        self.language_submenu = rumps.MenuItem("Language")
        self.languages = ["en", "sv"]  # Add more languages as needed
        self.selected_language = self.languages[0]
        for language in self.languages:
            language_item = rumps.MenuItem(language, callback=self.select_language)
            if language == self.selected_language:
                language_item.state = 1
            self.language_submenu.add(language_item)

        self.menu = [self.menu_item, self.language_submenu]
        self.key_listener = GlobalKeyListener(self)

    def select_language(self, sender):
        for language_item in self.language_submenu.values():
            language_item.state = 0
        sender.state = 1
        self.selected_language = sender.title

    def toggle_recording(self, sender):
        global is_recording

        if not is_recording:
            is_recording = True
            self.menu_item.title = 'Stop'
            threading.Thread(target=start_recording).start()
        else:
            is_recording = False
            self.menu_item.title = 'Record'
            save_audio_file()
            transcription = convert_audio_to_text(self.selected_language)
            if transcription:
                type_text(transcription)

def main():
    app = Voicer("Voicer 🎙")
    with keyboard.Listener(on_press=app.key_listener.on_press) as listener:
        app.run()
        listener.join()

if __name__ == "__main__":
    main()
