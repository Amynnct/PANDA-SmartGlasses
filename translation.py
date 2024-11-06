from googletrans import Translator


def main():
    translator = Translator()

    # Create a dictionary for language mappings
    language_mappings = {
        "spanish": "es",
        "french": "fr",
        "chinese": "zh-cn",
        "arabic": "ar",
        "japanese": "ja",
        "hindi": "hi",
        "german": "de",  # Corrected the language code for German
        "nepali": "ne",
        "vietnamese": "vi"
    }

    dest_lang = input("Enter the destination language: ").lower()

    # Check if the destination language is valid
    if dest_lang in language_mappings:
        dest_code = language_mappings[dest_lang]
        input_text = "Hello, my name is Nimra"

        # Print the translated text 10 times in a loop
        for i in range(10):
            translated_text = translator.translate(
                input_text, src='en', dest=dest_code)
            print("Translated text:", translated_text.text)
    else:
        print("Invalid destination language.")


if __name__ == "__main__":
    main()
