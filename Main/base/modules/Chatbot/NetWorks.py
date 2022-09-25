import pywhatkit
from googlesearch import search



def send_WhatsMessage(Number : str, Msg : str):
    pywhatkit.sendwhatmsg(Number, Msg)

def send_whatImage():
    pywhatkit.sendwhats_image("+910123456789", "Images/Hello.png")

def send_mail(email_sender, password, subject, html_code, email_receiver):
    pywhatkit.send_hmail(email_sender, password, subject, html_code, email_receiver)
    
def GetGoogleLink(query):
    Links = list()
    for link in search(query, tld="co.in", num=10, stop=10, pause=2):
        Links.append(link)
    return Links

# play a video on youtube
# pywhatkit.playonyt("PyWhatKit")