import websockets
import asyncio
import base64
import json
from googletrans import Translator
import pygame
from pygame.locals import *
import threading
import string
import re

import pyaudio

auth_key = "d8514a90779941b39b2cc70f19774c0b"
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()

# Display configuration
pygame.init()
pygame.font.init()
caption_font = pygame.font.SysFont("stsong", 72)
caption_color = (255, 255, 255)
caption_bg_color = (0, 0, 0)
caption_position = (50, 450)
caption_max_width = 700
caption_max_lines = 3
screen_size = (1000, 800)

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
    "vietnamese": "vi",
    "urdu": "ur"
}
current_line_is_formatted = False
run = True
check_translation = False
translation = False
translator = Translator()
captions_lock = threading.Lock()


def real_time_captions():
    try:
        global translation
        translation = (
            input("Translation to another language (y/n): ").lower() == 'y')
        global dest_lang
        dest_lang = input("Enter the destination language: ").lower()
    # Create a Pygame window
    except Exception as e:
        # Handle the exception when there is an error during translation
        return None
    # Create a Pygame window
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("AR Glasses Captions")

    def display_captions(captions):
        font = None
        if translation:
            if dest_lang == "nepali" or dest_lang == "hindi":
                font = "font/NotoSerifDevanagari-Regular.ttf"
            elif dest_lang == "chinese":
                font = "font/NotoSansSC-Regular.ttf"
            elif dest_lang == "vietnamese":
                font = "font/NotoSans-Regular.ttf"
            elif dest_lang == "arabic" or dest_lang == "urdu":
                font = "font/NotoNaskhArabic-Regular.ttf"
            elif dest_lang == "japanese":
                font = "font/NotoSerifJP-Regular.otf"
        caption_font = pygame.font.Font(font, 72)
        screen.fill(caption_bg_color)
        y = caption_position[1]
        for line in captions:
            wrapped_lines = []
            # Split the line into multiple lines with word wrap
            max_width = caption_max_width - caption_position[0]
            words = line.split()
            current_line = words[0]

            for word in words[1:]:
                test_line = current_line + " " + word
                if caption_font.size(test_line)[0] > max_width:
                    wrapped_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line

            wrapped_lines.append(current_line)

            for wrapped_line in wrapped_lines:
                text_surface = caption_font.render(
                    wrapped_line, True, caption_color)
                # Flip the mirrored display horizontally
                mirrored_screen = pygame.transform.flip(
                    text_surface, True, False)
                text_width, text_height = text_surface.get_size()

                # Blit the clear surface onto the screen at the specified location
                x = screen.get_width() - text_width - 50
                if y == caption_position[1]:
                    screen.fill(caption_bg_color)
                screen.blit(mirrored_screen, (x, y))
                y += text_height  # Adjust the y-position for the next line
                if y > screen_size[1] - 50:
                    y = caption_position[1]
        pygame.display.update()
        pygame.event.pump()

    # Run the Pygame loop in a separate thread

    def pygame_thread():
        global current_captions, clock, run
        current_captions = []
        clock = pygame.time.Clock()

        while run:
            pygame.event.pump()

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    run = False
                    return
            with captions_lock:
                display_captions(current_captions)
            clock.tick(30)

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
                while run:
                    try:
                        data = stream.read(
                            FRAMES_PER_BUFFER, exception_on_overflow=False)
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
                global current_captions, current_line_is_formatted, run, translation, dest_lang, check_translation, dest_code
                while run:
                    try:
                        result_str = await _ws.recv()
                        # Check if the destination language is supported
                        orig_text = json.loads(result_str)['text']
                        if not orig_text:
                            continue
                        remove_punc = str.maketrans('', '', string.punctuation)
                        print(orig_text)
                        words = re.findall(r'\b\w+\b', orig_text)
                        for word in words:
                            if check_translation:
                                if word in language_mappings:
                                    translation = True
                                    dest_lang = word
                                    check_translation = False
                                    break

                        if 'panda translate' in orig_text.lower().translate(remove_punc):
                            check_translation = True
                            print("What language do you want to translate to?\n")

                        if 'stop' in orig_text.lower().translate(remove_punc):
                            translation = False

                        if 'panda exit' in orig_text.lower().translate(remove_punc):
                            run = False
                            await _ws.close()

                        if orig_text and translation:
                            if dest_lang in language_mappings:
                                dest_code = language_mappings[dest_lang]
                                translated_text = translator.translate(
                                    orig_text, src='en', dest=dest_code).text
                            else:
                                print("Unsupported destination language.")
                        else:
                            translated_text = orig_text

                        if 'text_formatted' in json.loads(result_str) and json.loads(result_str)['text_formatted']:
                            if current_captions:
                                current_captions.pop()
                            current_captions.append(translated_text)
                            current_line_is_formatted = True
                            print(translated_text, end="\r\n")

                        else:
                            if current_line_is_formatted:
                                current_line_is_formatted = False
                            elif current_captions:
                                current_captions.pop()
                            current_captions.append(translated_text)
                            print(translated_text, end="\r")

                        if len(current_captions) > caption_max_lines:
                            current_captions.pop(0)

                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break

                    except Exception as e:
                        print(e)
                        assert False, "Error not working"

            send_result, receive_result = await asyncio.gather(send(), receive())

    pygame_thread = threading.Thread(target=pygame_thread)
    pygame_thread.start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_receive())
    if not run:
        print("Testing checking")
        pygame.quit()
        pygame_thread.join()
        return


if __name__ == "__main__":
    real_time_captions()
