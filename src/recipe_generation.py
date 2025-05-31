import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

def configure_gemini():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ GEMINI_API_KEY not found in .env file. Please add your valid API key.")
        st.stop()
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
        return model
    except Exception as e:
        st.error(f"🚨 Failed to configure Gemini: {str(e)}")
        st.error("Please ensure your API key is correct and has the Gemini API enabled.")
        st.stop()

def generate_recipe(model, ingredients, diet, cuisine, meal_type, skill_level="Any", total_time=""):
    prompt = f"""
    Create a detailed {meal_type.lower()} recipe using primarily these ingredients: {ingredients}.

    Requirements:
    - Diet: {diet if diet != "None" else "No dietary restrictions"}
    - Cuisine style: {cuisine if cuisine != "Any" else "Any style is acceptable"}
    - Cooking skill level: {skill_level if skill_level != "Any" else "Any skill level (make it accessible)"}
    {'- The total time for the recipe (prep + cook) should not exceed ' + total_time + ' minutes.' if total_time.strip() else ''}

    The recipe should include:
    1. CREATIVE RECIPE NAME (make this appealing and unique)
    2. A short, enticing DESCRIPTION of the dish (1-2 sentences).
    3. PREP TIME: (e.g., 15 minutes)
    4. COOK TIME: (e.g., 30 minutes)
    5. TOTAL TIME: (Prep + Cook)
    6. SERVINGS: (e.g., 4 servings)
    7. INGREDIENTS:
       - List all ingredients with precise measurements (e.g., 1 cup, 2 tbsp, 100g).
       - Organize by category if needed (e.g., "For the marinade:", "For the main dish:").
    8. EQUIPMENT: (Optional: list any special equipment needed, e.g., "9x13 inch baking dish")
    9. PREPARATION STEPS:
       - Numbered, clear, concise instructions.
       - Include cooking temperatures and estimated times for each major step.
       - Start with preheating oven/preparing pans if necessary.
    10. SERVING SUGGESTIONS:
        - How to plate or present the dish.
        - Recommended side dishes or accompaniments.
    11. CHEF'S TIPS: (Optional: 1-2 helpful tips, variations, or storage instructions)

    Make the recipe easy to follow for home cooks.
    Be creative and ensure the recipe sounds delicious!
    The very first line of your response MUST be "1. CREATIVE RECIPE NAME: [Actual Name Here]". Do not add any other text or numbering before this line.
    For subsequent sections like "2. DESCRIPTION:", "3. PREP TIME:", etc., also ensure they start on a new line with the number and title.
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.8,
                "top_p": 0.95,
                "max_output_tokens": 3500
            }
        )
        if not response.text:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason_message = "Unknown reason"
                if hasattr(response.prompt_feedback, 'block_reason_message') and response.prompt_feedback.block_reason_message:
                    block_reason_message = response.prompt_feedback.block_reason_message
                elif hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                    block_reason_message = response.prompt_feedback.block_reason.name
                st.error(f"⚠️ Recipe generation blocked. Reason: {block_reason_message}")
                return None
            raise ValueError("Empty response from model.")
        return response.text
    except Exception as e:
        st.error(f"⚠️ Recipe generation failed: {str(e)}")
        return None
