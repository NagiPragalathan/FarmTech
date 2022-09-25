import os
import speech_recognition as sr
from gtts import gTTS
import playsound    
import wikipedia
import requests
from bs4 import BeautifulSoup


def Input(Lang):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("lision")
        audio = r.listen (source)
    try:
        WhatSpoke = r.recognize_google(audio, language=Lang)
        return WhatSpoke
    except:
        return False


def speak(text,Lang):
    try :
        tts = gTTS(text=text, lang=Lang)
        filename = "abc.mp3"
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)
    except :
       pass       

def WebScrap(Topic,Lines):
    try :
        Value = wikipedia.summary(Topic, sentences = Lines)
        return Value
    except :
        return False

def scrping(Text, paraLen):
        
        def url(query): # this function generateing a links
            links : list = []
            try:
                from googlesearch import search
            except ImportError:
                print("No module named 'google' found")
            # to search
            try:           
                for j in search(query, tld="co.in", num=10, stop=20, pause=1):
                    links.append(j)
            except:
                return "Problem occers in link generator(to search)"
            return links

        # link for extract html data
        def getdata(url):
            try:
                r = requests.get(url)
                return r.text
            except:
                return "none"
        link : list = url(Text) #total links

        try:
            output : list = []
            data : str = "" 
            for i in range(paraLen):
                htmldata = getdata(link[i])
                soup = BeautifulSoup(htmldata, 'html.parser')
                data : str = ''
                for data in soup.find_all("p"):
                    output.append(data.get_text())
            return output[5:10][paraLen]
        except:
            return "ScripeError"
def Cscrping(Text, paraLen,Tags):
        
        def url(query): # this function generateing a links
            links : list = []
            try:
                from googlesearch import search
            except ImportError:
                print("No module named 'google' found")
            # to search
            try:           
                for j in search(query, num_results=10):
                    links.append(j)
            except:
                return "Problem occers in link generator(to search)"
            print(links)
            return links

        # link for extract html data
        def getdata(url):
            try:
                r = requests.get(url)
                return r.text
            except:
                return "none"
        link : list = url(Text) #total links

        try:
            output : list = []
            data : str = "" 
            for i in range(paraLen):
                htmldata = getdata(link[i])
                soup = BeautifulSoup(htmldata, 'html.parser')
                data : str = ''
                for data in soup.find_all(Tags):
                    output.append(data.get_text())
            return output
        except:
            return "ScripeError"
