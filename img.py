# import required module
from playsound import playsound
 
a="C:/Users/NagiPragalathan/Desktop/FarmTech/abc.mp3"

# import pygame

from gtts import gTTS
from io import BytesIO
from pygame import mixer
import time

def speak(text):
    mixer.init()
    mp3_fp = BytesIO()
    tts = gTTS(text, lang='en')
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    mixer.music.load(mp3_fp, "mp3")
    mixer.music.play()
    time.sleep(5)
