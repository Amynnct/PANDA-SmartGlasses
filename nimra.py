import openai
from googletrans import Translator

openai.api_key = # insert your key here
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello my name is nimra!"}
    ]
)

print(response['choices'][0]['message']['content'])
translator = Translator()
try:
    translated_text = translator.translate(
        "testing if google trans is working", dest="vi")
    print(translated_text.text)
except Exception as e:
    print(f"An error occurred: {e}")
