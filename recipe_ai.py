import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY is missing from .env file.")
    st.stop()

# Configure Gemini with correct API key
genai.configure(api_key=api_key)

# Use correct model name
try:
    model = genai.GenerativeModel(model_name="models/gemini-pro")
except Exception as e:
    st.error(f"Model initialization failed: {e}")
    st.stop()

# Function to generate recipe
def generate_recipe(ingredients, diet, cuisine, meal_type):
    prompt = f"""
    Create a detailed {meal_type.lower()} recipe using: {ingredients}.
    - Diet: {diet if diet != "None" else "Regular"}
    - Cuisine: {cuisine if cuisine != "Any" else "International"}

    Include these sections:
    1. Recipe Name
    2. Ingredients with exact measurements
    3. Step-by-step Instructions
    4. Cooking Time (Prep + Cook)
    5. Serving Suggestions
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048
            }
        )

        return response.text or response.parts[0].text
    except Exception as e:
        st.error(f"Recipe generation failed: {str(e)}")
        return None

# Streamlit app UI
st.title("🍽️ AI Recipe Generator")

with st.form("recipe_form"):
    ingredients = st.text_input("Ingredients (comma-separated):")
    diet = st.selectbox("Diet", ["None", "Vegetarian", "Vegan", "Gluten-Free", "Keto"])
    cuisine = st.selectbox("Cuisine", ["Any", "Italian", "Indian", "Pakistani", "Mexican", "Chinese", "Pakistani (Traditional)"])
    meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Dessert"])
    submit = st.form_submit_button("Generate Recipe")

if submit and ingredients:
    with st.spinner("Generating recipe..."):
        recipe = generate_recipe(ingredients, diet, cuisine, meal_type)
        if recipe:
            st.markdown(recipe)
