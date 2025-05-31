from googletrans import Translator
import streamlit as st

def translate_text(text, dest_language_code):
    if dest_language_code == 'original' or dest_language_code == 'any':
        return text
    translator = Translator()
    try:
        translated = translator.translate(text, dest=dest_language_code)
        return translated.text
    except Exception as e:
        st.warning(f"Translation failed: {e}")
        return text
