import websockets
import asyncio
import base64
import json
from googletrans import Translator
import pyaudio
import pygame
from pygame.locals import *

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

pygame.init()

# Display configuration
caption_font = pygame.font.SysFont("stsong", 24)
caption_color = (255, 255, 255)
caption_bg_color = (0, 0, 0)
screen_size = (800, 200)

# Create a Pygame window
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Transcription Display")


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
                            display_text = translated_text.text
                        else:
                            display_text = orig_text
                    else:
                        if translation and orig_text:
                            translated_text = translator.translate(
                                orig_text, src='en', dest=dest_code)
                            display_text = translated_text.text
                        else:
                            display_text = orig_text

                    # Draw the text on the Pygame window
                    screen.fill(caption_bg_color)
                    text_surface = caption_font.render(
                        display_text, True, caption_color)
                    screen.blit(text_surface, (10, 10))
                    pygame.display.flip()

                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break

                except Exception as e:
                    assert False, "Not a websocket 4008 error"

        send_result, receive_result = await asyncio.gather(send(), receive())

while True:
    asyncio.run(send_receive())
