# If you see "'streamlit' is not recognized", install it first:
# pip install streamlit
# Then run:
# streamlit run app.py

import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

def extract_recipe_name(recipe_text):
    """
    Extracts the recipe name from the generated text.
    Prioritizes lines starting with "1. CREATIVE RECIPE NAME:" or "RECIPE NAME:".
    """
    lines = recipe_text.strip().split('\n')
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        name_part = ""
        # More specific checks first
        if cleaned_line.lower().startswith("1. creative recipe name:"):
            name_part = cleaned_line.split(":", 1)[1].strip()
        elif cleaned_line.lower().startswith("creative recipe name:"):
            name_part = cleaned_line.split(":", 1)[1].strip()
        elif cleaned_line.lower().startswith("1. recipe name:"):
            name_part = cleaned_line.split(":", 1)[1].strip()
        elif cleaned_line.lower().startswith("recipe name:"):
            name_part = cleaned_line.split(":", 1)[1].strip()
        # General "1. " followed by text, trying to avoid it being an instruction
        elif cleaned_line.lower().startswith("1."):
            potential_name = cleaned_line[len("1."):].strip()
            # Heuristic: if it's short and doesn't contain typical instruction keywords, it might be the name
            if len(potential_name.split()) < 10 and not any(kw in potential_name.lower() for kw in ["ingredient", "step", "prep", "cook", "serving", "total time", "description"]):
                name_part = potential_name
            else: # If it's longer or has keywords, it's probably not the name, so continue to next line
                continue
        # Fallback: if no specific prefix, take the first non-empty, non-instruction-like line
        elif not name_part and len(lines) > 0 and lines[0].strip() == cleaned_line: # If it's the very first line
             if len(cleaned_line.split()) < 10 and not any(kw in cleaned_line.lower() for kw in ["ingredient", "step", "prep", "cook", "serving", "total time", "description"]):
                name_part = cleaned_line

        # Clean up and return if a valid name part is found
        if name_part:
            name = name_part.replace("*", "").replace("#", "").strip(":- ")
            if name: # Ensure name is not empty after stripping
                return name[:150] # Limit length

    return "Untitled Recipe" # Fallback if no suitable name found

# Removed: Call to init_db()

# --- AI Configuration ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY not found in .env file. Please add your valid API key.")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini: {str(e)}")
    st.error("Please ensure your API key is correct and has the Gemini API enabled.")
    st.stop()

def generate_recipe(ingredients, diet, cuisine, meal_type):
    """Generates a recipe using the Gemini AI model based on user inputs."""
    prompt = f"""
    Create a detailed {meal_type.lower()} recipe using primarily these ingredients: {ingredients}.

    Requirements:
    - Diet: {diet if diet != "None" else "No dietary restrictions"}
    - Cuisine style: {cuisine if cuisine != "Any" else "Any style is acceptable"}

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
                # Try to get a more specific block reason message
                block_reason_message = "Unknown reason"
                if hasattr(response.prompt_feedback, 'block_reason_message') and response.prompt_feedback.block_reason_message:
                    block_reason_message = response.prompt_feedback.block_reason_message
                elif hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                     block_reason_message = response.prompt_feedback.block_reason.name # or str(response.prompt_feedback.block_reason)
                st.error(f"⚠️ Recipe generation blocked. Reason: {block_reason_message}")
                return None
            raise ValueError("Empty response from model.")
        return response.text

    except Exception as e:
        st.error(f"⚠️ Recipe generation failed: {str(e)}")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="AI Chef - Recipe Generator", page_icon="🧑‍🍳", layout="wide")
st.title("🧑‍🍳 AI Chef - Recipe Generator")
st.markdown("Let AI craft a unique recipe based on your ingredients and preferences!")

# Initialize session state variables
# Removed: viewing_recipe_id
if 'current_generated_recipe_text' not in st.session_state:
    st.session_state.current_generated_recipe_text = None
if 'last_generated_inputs' not in st.session_state:
    st.session_state.last_generated_inputs = None

# --- Sidebar for Inputs ---
with st.sidebar:
    st.header("📝 Recipe Preferences")
    with st.form("recipe_form_sidebar"):
        ingredients_input_val = st.text_input(
            "Main Ingredients (comma separated)",
            placeholder="e.g., chicken, broccoli, rice",
            help="List the main ingredients you have or want to use."
        )
        meal_type_input_val = st.selectbox(
            "Meal Type",
            ["Dinner", "Lunch", "Breakfast", "Dessert", "Snack", "Appetizer", "Side Dish"],
            index=0,
            help="What type of meal are you preparing?"
        )
        cuisine_input_val = st.selectbox(
            "Cuisine Style",
            [
                "Any", "Italian", "Indian", "Pakistani", "Pakistani (Traditional)", "Mexican", "Chinese", "Mediterranean", "Thai", "Japanese", "French", "American", "Fusion"
            ],
            help="Select a preferred cuisine style, or 'Any' for flexibility."
        )
        diet_input_val = st.selectbox(
            "Dietary Preference",
            ["None", "Vegetarian", "Vegan", "Gluten-Free", "Keto", "Paleo", "Dairy-Free", "Low-Carb", "Pescatarian"],
            help="Select any dietary restrictions or preferences."
        )
        submitted = st.form_submit_button("✨ Generate Recipe", type="primary", use_container_width=True)

    # Removed: Saved Recipes section from sidebar
    # st.markdown("---")
    # st.header("📖 Saved Recipes")
    # ... (logic for displaying saved recipes removed)

# --- Main Area for Displaying Recipes ---
main_placeholder = st.empty() # Use a placeholder for dynamic content switching

# Removed: Block for if st.session_state.viewing_recipe_id is not None:

if submitted:
    # A new recipe generation was submitted
    with main_placeholder.container():
        # Removed: st.session_state.viewing_recipe_id = None

        if not ingredients_input_val.strip():
            st.warning("⚠️ Please enter at least one ingredient to get started.")
            st.session_state.current_generated_recipe_text = None
            st.session_state.last_generated_inputs = None
        else:
            with st.spinner("🧑‍🍳 Chef is whisking up your recipe... This might take a moment!"):
                generated_text = generate_recipe(ingredients_input_val, diet_input_val, cuisine_input_val, meal_type_input_val)

            st.session_state.current_generated_recipe_text = generated_text
            st.session_state.last_generated_inputs = {
                "ingredients": ingredients_input_val,
                "meal_type": meal_type_input_val,
                "cuisine": cuisine_input_val,
                "diet": diet_input_val,
            } if generated_text else None


            if generated_text:
                st.success("🎉 Your custom recipe is ready!")
                recipe_name = extract_recipe_name(generated_text)

                # Removed: Call to save_recipe_to_db and related st.toast/st.error
                # if save_recipe_to_db(recipe_name, ingredients_input_val, diet_input_val, cuisine_input_val, meal_type_input_val, generated_text):
                #     st.toast(f"✅ Recipe '{recipe_name}' saved successfully!", icon="💾")
                # else:
                #     st.error("💥 Failed to save the recipe to the database.")

                st.subheader(f"✨ Your Custom Recipe: {recipe_name}")
                st.markdown(f"**Generated for:** Ingredients: `{ingredients_input_val}`, Meal: `{meal_type_input_val}`, Cuisine: `{cuisine_input_val}`, Diet: `{diet_input_val}`")
                st.markdown("---")
                st.markdown(generated_text)
            else:
                if ingredients_input_val.strip(): # Only show error if user actually put ingredients
                     st.error("💥 Oops! Failed to generate a recipe. Please check error messages above or try adjusting your inputs.")
                st.session_state.last_generated_inputs = None # Clear if generation failed

elif st.session_state.current_generated_recipe_text:
    # Display the last generated recipe if no specific action (new submit) is taken
    with main_placeholder.container():
        recipe_name = extract_recipe_name(st.session_state.current_generated_recipe_text)
        st.subheader(f"✨ Your Custom Recipe: {recipe_name}")
        if st.session_state.last_generated_inputs:
            inputs = st.session_state.last_generated_inputs
            st.markdown(f"**Generated for:** Ingredients: `{inputs['ingredients']}`, Meal: `{inputs['meal_type']}`, Cuisine: `{inputs['cuisine']}`, Diet: `{inputs['diet']}`")
        st.markdown("---")
        st.markdown(st.session_state.current_generated_recipe_text)
else:
    # Initial state or after clearing everything
    with main_placeholder.container():
        # Ensure this condition makes sense now without viewing_recipe_id
        if st.session_state.current_generated_recipe_text is None:
            st.info("🍽️ Fill in your preferences in the sidebar and click '✨ Generate Recipe' to begin!")
            st.markdown("""
            ### How to Use:
            1.  **Enter Ingredients:** List the main ingredients you have on hand in the sidebar.
            2.  **Select Preferences:** Choose your desired meal type, cuisine style, and any dietary needs.
            3.  **Generate:** Click the "Generate Recipe" button.
            4.  **View:** Your custom recipe will appear here.

            Happy cooking! 🍳
            """)