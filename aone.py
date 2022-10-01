import speech_recognition as sr
def listen(duration):
	t= sr.Recognizer()
	with sr.Microphone() as source:
		text = t.record(source, duration=duration)
		try:
			return t.recognize_google(text)
		except:
			return "Didn't heard perfectly!"

print(listen(3))