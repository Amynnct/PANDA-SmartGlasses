import speech_recognition as sr

# Initialize the recognizer
recognizer = sr.Recognizer()

# Function to perform real-time speech recognition


def real_time_speech_to_text():
    with sr.Microphone() as source:
        print("Listening...")

        while True:
            try:
                audio = recognizer.listen(source)  # Continuously listen
                # Use Google Web Speech API for recognition
                text = recognizer.recognize_google(audio)
                print("You said: " + text)
            except sr.RequestError as e:
                print("Could not request results. Check your internet connection.")
            except sr.UnknownValueError:
                pass  # Ignore unrecognized speech
            except KeyboardInterrupt:
                print("Listening stopped.")
                break


if __name__ == "__main__":
    real_time_speech_to_text()
