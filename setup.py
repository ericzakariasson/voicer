# setup.py
from setuptools import setup

APP = ['voicer.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['rumps', 'openai', 'speech_recognition', 'pynput'],  # Include the required packages
    'iconfile': 'app_icon.icns',  # If you have an icon for your app
    'plist': {
        'CFBundleName': 'voicer',
        'CFBundleDisplayName': 'voicer',
        'CFBundleIdentifier': 'com.example.voicer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2023 Eric Zakariasson. All rights reserved.',
        'LSUIElement': True
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
