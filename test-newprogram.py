import websockets
import asyncio
import base64
import json
from googletrans import Translator


import pyaudio

auth_key = "d8514a90779941b39b2cc70f19774c0b"
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()

# starts recording
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)

# the AssemblyAI endpoint we're going to hit
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

translator = Translator()

# Create a dictionary for language mappings
language_mappings = {
    "spanish": "es",
    "french": "fr",
    "chinese": "zh-cn",
    "arabic": "ar",
    "japanese": "ja",
    "hindi": "hi",
    "german": "de",
    "nepali": "ne",
    "vietnamese": "vi"
}

translation = (input("Translation to another language (y/n): ").lower() == 'y')
dest_lang = input("Enter the destination language: ").lower()


async def send_receive():

    print(f'Connecting websocket to url ${URL}')

    async with websockets.connect(
            URL,
            extra_headers=(("Authorization", auth_key),),
            ping_interval=5,
            ping_timeout=20
    ) as _ws:

        await asyncio.sleep(0.1)
        print("Receiving SessionBegins ...")

        session_begins = await _ws.recv()
        print(session_begins)
        print("Sending messages ...")

        async def send():
            while True:
                try:
                    data = stream.read(FRAMES_PER_BUFFER)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    await _ws.send(json_data)

                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break

                except Exception as e:
                    assert False, "Not a websocket 4008 error"

                await asyncio.sleep(0.01)

            return True

        async def receive():
            while True:
                try:
                    result_str = await _ws.recv()
                    # Check if the destination language is supported
                    orig_text = json.loads(result_str)['text']
                    if orig_text is None:
                        continue
                    if translation:
                        if dest_lang in language_mappings:
                            dest_code = language_mappings[dest_lang]
                        else:
                            print("Unsupported destination language.")
                    if 'text_formatted' in json.loads(result_str) and json.loads(result_str)['text_formatted']:
                        if translation and orig_text:
                            translated_text = translator.translate(
                                orig_text, src='en', dest=dest_code)
                            print(translated_text.text, end="\r\n")
                        else:
                            print(orig_text, end="\r\n")
                    else:
                        if translation and orig_text:
                            translated_text = translator.translate(
                                orig_text, src='en', dest=dest_code)
                            print(translated_text.text, end="\r")
                        else:
                            print(orig_text, end="\r")

                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break

                except Exception as e:
                    assert False, "Not a websocket 4008 error"

        send_result, receive_result = await asyncio.gather(send(), receive())

while True:
    asyncio.run(send_receive())
