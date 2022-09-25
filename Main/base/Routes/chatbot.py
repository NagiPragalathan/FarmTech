from pyexpat.errors import messages
from django.shortcuts import render
import requests
import wikipedia
from gtts import gTTS
from bs4 import BeautifulSoup
import playsound, os
import threading
from datetime import datetime
import pywhatkit
from random import choice
messages = []
dic = {"hello" : ["hi, it's really good to hear form you, i hope you are doing well","hey.there how can i help you"],
"thank you":["it's okey"],}

def cource(request):
    return render(request,'cources\school_education\simple.html')

def speak(text,Lang):
    try :
        tts = gTTS(text=text, lang=Lang)
        filename = "abc.mp3"
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)
    except :
       pass       
        

def scrping(Text, paraLen):
        
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

def WebScrap(Topic,Lines):
    try :
        Value = wikipedia.summary(Topic, sentences = Lines)
        return Value
    except :
        return False

def chatbot(request):
    times = datetime.now()
    current_time = times.strftime("%H:%M %p")
    usr_input = request.GET.get('input')
    print(usr_input)
    messages.append(usr_input)
    replay=""
    try:
        replay = choice(dic.get(usr_input))
        messages.append(replay)
    except:
        replay=None
    print(replay)
    if(replay == None):
        if usr_input != None :
            replay = WebScrap(usr_input,1)
            if replay:
                print("webscrap worked....")
                pass
            else :
                replay = scrping(usr_input,1)
        elif(usr_input == None) :
            replay = ""
        messages.append(replay)
    makefullcode = ""
    for i,x in enumerate(messages):
        if(i != 0 and i != 1):
            if(i%2 == 0):
                user = f"""<div class="chat-r">
                                <div class="sp"></div>
                                <div class="mess mess-r">
                                        {x}
                                    </p>
                                    <div class="check">
                                        <span>{current_time}</span>
                                    </div>
                                </div>
                            </div>
                """
                makefullcode = makefullcode + user 
            else:
                system_ = f"""<div class="chat-l">
                                <div class="mess">
                                    <p style="word-break: break-word;">
                                    {x}
                                    </p>
                                    <div class="check">
                                        <span>{current_time}</span>
                                    </div>
                                </div>
                                <div class="sp"></div>
                            </div>"""
                makefullcode = makefullcode + system_
    frontend = {"codes":makefullcode}
    def say():
        try:
            speak(messages[-1],"en")
        except:
            pass
    t1 = threading.Thread(target=say)
    t1.setDaemon(False)
    t1.start()

    return render(request, 'chatbot/index.html',frontend)
