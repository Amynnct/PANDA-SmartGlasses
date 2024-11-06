import assemblyai as aai
import openai
import elevenlabs
from queue import Queue
from transcribe import real_time_captions
import string

# Set API keys
aai.settings.api_key = # insert your assembly ai key here
openai.api_key = # insert your open ai key
elevenlabs.set_api_key(# elevenlabs key)

transcript_queue = Queue()


def on_data(transcript: aai.RealtimeTranscript):
    if not transcript.text:
        return
    remove_punc = str.maketrans('', '', string.punctuation)
    if 'panda transcribe' in transcript.text.lower().translate(remove_punc) and isinstance(transcript, aai.RealtimeFinalTranscript):
        real_time_captions()
    elif 'panda stop' in transcript.text.lower().translate(remove_punc) and isinstance(transcript, aai.RealtimeFinalTranscript):
        return
    elif 'panda' in transcript.text.lower().translate(remove_punc) and isinstance(transcript, aai.RealtimeFinalTranscript):
        print("User:", transcript.text, end="\r\n")
        transcript_queue.put(transcript.text + '')
        transcript_result = transcript_queue.get()
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k-0613",
            messages=[
                {"role": "system", "content": 'You are a highly skilled AI, answer the questions given within a maximum of 1000 characters.'},
                {"role": "user", "content": transcript_result}
            ]
        )
        chat_res = response.choices[0].message.content
        print("\nAI:", chat_res, end="\r\n")
        audio = elevenlabs.generate(
            text=chat_res,
            voice="Bella"  # or any voice of your choice
        )
        elevenlabs.play(audio)
    else:
        print(transcript.text, end="\r")


def on_error(error: aai.RealtimeError):
    print("An error occured:", error)

# Conversation loop


def handle_conversation():
    transcriber = aai.RealtimeTranscriber(
        on_data=on_data,
        on_error=on_error,
        sample_rate=44_100,
    )
    # Start the connection
    transcriber.connect()
    # Open  the microphone stream
    microphone_stream = aai.extras.MicrophoneStream()
    # Stream audio from the microphone
    transcriber.stream(microphone_stream)
    transcriber.close()
    # while True:
    # Retrieve data from queue
    # transcript_result = transcript_queue.get()
    # print("Test succeed!:", transcript_result)
    # # Send the transcript to OpenAI for response generation
    # response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "system", "content": 'You are a highly skilled AI, answer the questions given within a maximum of 1000 characters.'},
    #         {"role": "user", "content": transcript_result}
    #     ]
    # )
    # print(response.choices[0].message.content)
    # text = response['choices'][0]['message']['content']
    # text = "AssemblyAI is the best YouTube channel for the latest AI tutorials."

    # Convert the response to audio and play it


print("Hello World 2")
handle_conversation()
