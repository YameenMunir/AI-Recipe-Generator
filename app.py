# Importing necessary libraries
import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import json
import io
from fpdf import FPDF
import googletrans
from googletrans import Translator
import unicodedata

# Initialize the Google Generative AI client
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

# --- Recipe Generation Function ---
def generate_recipe(ingredients, diet, cuisine, meal_type, skill_level="Any", total_time=""):
    """Generates a recipe using the Gemini AI model based on user inputs, including skill level and total time."""
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

# --- PDF Generation Function ---
def recipe_to_pdf(recipe_name, recipe_text):
    import unicodedata
    def to_latin1(text):
        # Normalize and encode to latin1, replacing unencodable chars
        return unicodedata.normalize('NFKD', text).encode('latin1', 'replace').decode('latin1')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 16)
    safe_name = to_latin1(recipe_name)
    pdf.cell(0, 10, safe_name, ln=True)
    pdf.set_font("Arial", "", 12)
    for line in recipe_text.split('\n'):
        safe_line = to_latin1(line)
        pdf.multi_cell(0, 8, safe_line)
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return io.BytesIO(pdf_bytes)

# --- Recipe History File Handling ---
HISTORY_FILE = "recipe_history.json"

# Load and save recipe history from/to a JSON file

def load_recipe_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# Save the recipe history to a JSON file
def save_recipe_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# --- Streamlit UI ---
st.set_page_config(page_title="AI Chef - Recipe Generator", page_icon="🧑‍🍳", layout="wide")
st.title("🧑‍🍳 AI Chef - Recipe Generator")
st.markdown("Let AI craft a unique recipe based on your ingredients and preferences!")

# Add language selection for viewing 
view_languages = {
    "Original": "original",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh-cn",
}
view_language = st.selectbox("View Recipe In", list(view_languages.keys()), index=0)
view_lang_code = view_languages[view_language]

# Initialize session state variables
# Removed: viewing_recipe_id
if 'current_generated_recipe_text' not in st.session_state:
    st.session_state.current_generated_recipe_text = None
if 'last_generated_inputs' not in st.session_state:
    st.session_state.last_generated_inputs = None
# Add: Recipe history session state
if 'recipe_history' not in st.session_state:
    st.session_state.recipe_history = load_recipe_history() # Load history from file
if 'selected_history_index' not in st.session_state:
    st.session_state.selected_history_index = None

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
        # --- Advanced Input Options ---
        skill_level_input_val = st.selectbox(
            "Cooking Skill Level",
            ["Any", "Beginner", "Intermediate", "Advanced"],
            index=0,
            help="Choose your cooking skill level for recipe complexity."
        )
        total_time_input_val = st.text_input(
            "Desired Total Cooking Time (Minutes)",
            placeholder="e.g., 30, 45, 60",
            help="Specify a maximum total cooking time in minutes, or leave blank for no limit."
        )
        # --- Language Selection for Generation ---
        language_options = ["Any (auto-detect)", "English", "Spanish", "French", "German", "Chinese"]
        selected_language = st.selectbox(
            "Recipe Language",
            language_options,
            index=0,
            help="Choose the language for recipe generation."
        )
        # Error handling for total_time_input_val
        invalid_time = False
        if total_time_input_val.strip():
            if not total_time_input_val.strip().isdigit() or int(total_time_input_val.strip()) <= 0:
                st.warning("⚠️ Please enter a positive number for total cooking time, or leave blank for no limit.")
                invalid_time = True

        submitted = st.form_submit_button("✨ Generate Recipe", type="primary", use_container_width=True)

    # --- Recipe History Section ---
    st.markdown("---")
    st.header("📜 Recipe History")
    if st.session_state.recipe_history:
        for idx, recipe in enumerate(reversed(st.session_state.recipe_history)):
            display_idx = len(st.session_state.recipe_history) - 1 - idx
            label = recipe['name'] if recipe['name'] else f"Recipe {display_idx+1}"
            col1, col2 = st.columns([4,1])
            with col1:
                if st.button(label, key=f"history_{display_idx}"):
                    st.session_state.selected_history_index = display_idx
            with col2:
                if st.button("🗑️", key=f"delete_{display_idx}"):
                    # Remove the recipe from history
                    del st.session_state.recipe_history[display_idx]
                    save_recipe_history(st.session_state.recipe_history)
                    # If the deleted recipe was selected, clear selection
                    if st.session_state.selected_history_index == display_idx:
                        st.session_state.selected_history_index = None
                    st.rerun()
    else:
        st.caption("No recipes generated yet this session.")
        

# --- Main Area for Displaying Recipes ---
main_placeholder = st.empty() # Use a placeholder for dynamic content switching

# Translation function
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

if submitted and not invalid_time:
    # A new recipe generation was submitted
    with main_placeholder.container():
        # Removed: st.session_state.viewing_recipe_id = None

        if not ingredients_input_val.strip():
            st.warning("⚠️ Please enter at least one ingredient to get started.")
            st.session_state.current_generated_recipe_text = None
            st.session_state.last_generated_inputs = None
        else:
            with st.spinner("🧑‍🍳 Chef is whisking up your recipe... This might take a moment!"):
                language_instruction = ""
                if selected_language != "Any (auto-detect)":
                    language_instruction = f"Please write the recipe in {selected_language}.\n"
                generated_text = generate_recipe(
                    language_instruction + ingredients_input_val,
                    diet_input_val,
                    cuisine_input_val,
                    meal_type_input_val,
                    skill_level_input_val,
                    total_time_input_val
                )
            st.session_state.current_generated_recipe_text = generated_text
            st.session_state.last_generated_inputs = {
                "ingredients": ingredients_input_val,
                "meal_type": meal_type_input_val,
                "cuisine": cuisine_input_val,
                "diet": diet_input_val,
                "skill_level": skill_level_input_val,
                "total_time": total_time_input_val
            } if generated_text else None
            if generated_text:
                recipe_name = extract_recipe_name(generated_text)
                st.session_state.recipe_history.append({
                    'name': recipe_name,
                    'text': generated_text,
                    'inputs': {
                        'ingredients': ingredients_input_val,
                        'meal_type': meal_type_input_val,
                        'cuisine': cuisine_input_val,
                        'diet': diet_input_val,
                        'skill_level': skill_level_input_val,
                        'total_time': total_time_input_val
                    }
                })
                save_recipe_history(st.session_state.recipe_history)
                st.success("🎉 Your custom recipe is ready!")
                st.subheader(f"✨ Your Custom Recipe: {recipe_name}")
                st.markdown(f"**Generated for:** Ingredients: `{ingredients_input_val}`, Meal: `{meal_type_input_val}`, Cuisine: `{cuisine_input_val}`, Diet: `{diet_input_val}`, Skill: `{skill_level_input_val}`, Max Time: `{total_time_input_val or 'Any'}` minutes")
                st.markdown("---")
                display_text = generated_text
                if view_lang_code != "original":
                    display_text = translate_text(generated_text, view_lang_code)
                st.markdown(display_text)
                # --- Export/Download Buttons ---
                st.markdown("#### 📤 Export Recipe")
                col_txt, col_pdf = st.columns(2)
                with col_txt:
                    st.download_button(
                        label="💾 Download as .txt",
                        data=display_text,
                        file_name=f"{recipe_name}.txt",
                        mime="text/plain"
                    )
                with col_pdf:
                    pdf_bytes = recipe_to_pdf(recipe_name, display_text)
                    st.download_button(
                        label="📄 Download as PDF",
                        data=pdf_bytes,
                        file_name=f"{recipe_name}.pdf",
                        mime="application/pdf"
                    )
            else:
                if ingredients_input_val.strip():
                    st.error("💥 Oops! Failed to generate a recipe. Please check error messages above or try adjusting your inputs.")
                st.session_state.last_generated_inputs = None
elif st.session_state.selected_history_index is not None:
    # Display a recipe from history if selected
    with main_placeholder.container():
        recipe = st.session_state.recipe_history[st.session_state.selected_history_index]
        recipe_name = recipe['name']
        st.subheader(f"✨ Your Custom Recipe: {recipe_name}")
        inputs = recipe['inputs']
        st.markdown(f"**Generated for:** Ingredients: `{inputs['ingredients']}`, Meal: `{inputs['meal_type']}`, Cuisine: `{inputs['cuisine']}`, Diet: `{inputs['diet']}`")
        st.markdown("---")
        display_text = recipe['text']
        if view_lang_code != "original":
            display_text = translate_text(recipe['text'], view_lang_code)
        st.markdown(display_text)
        # --- Export/Download Buttons ---
        st.markdown("#### 📤 Export Recipe")
        col_txt, col_pdf = st.columns(2)
        with col_txt:
            st.download_button(
                label="💾 Download as .txt",
                data=display_text,
                file_name=f"{recipe_name}.txt",
                mime="text/plain"
            )
        with col_pdf:
            pdf_bytes = recipe_to_pdf(recipe_name, display_text)
            st.download_button(
                label="📄 Download as PDF",
                data=pdf_bytes,
                file_name=f"{recipe_name}.pdf",
                mime="application/pdf"
            )
elif st.session_state.current_generated_recipe_text:
    # Display the last generated recipe if no specific action (new submit) is taken
    with main_placeholder.container():
        recipe_name = extract_recipe_name(st.session_state.current_generated_recipe_text)
        st.subheader(f"✨ Your Custom Recipe: {recipe_name}")
        if st.session_state.last_generated_inputs:
            inputs = st.session_state.last_generated_inputs
            st.markdown(f"**Generated for:** Ingredients: `{inputs['ingredients']}`, Meal: `{inputs['meal_type']}`, Cuisine: `{inputs['cuisine']}`, Diet: `{inputs['diet']}`")
        st.markdown("---")
        display_text = st.session_state.current_generated_recipe_text
        if view_lang_code != "original":
            display_text = translate_text(st.session_state.current_generated_recipe_text, view_lang_code)
        st.markdown(display_text)
        # --- Export/Download Buttons ---
        st.markdown("#### 📤 Export Recipe")
        col_txt, col_pdf = st.columns(2)
        with col_txt:
            st.download_button(
                label="💾 Download as .txt",
                data=display_text,
                file_name=f"{recipe_name}.txt",
                mime="text/plain"
            )
        with col_pdf:
            pdf_bytes = recipe_to_pdf(recipe_name, display_text)
            st.download_button(
                label="📄 Download as PDF",
                data=pdf_bytes,
                file_name=f"{recipe_name}.pdf",
                mime="application/pdf"
            )
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