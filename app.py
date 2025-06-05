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
from src.recipe_generation import configure_gemini, generate_recipe
from src.pdf_utils import recipe_to_pdf, meal_plan_to_pdf
from src.translation_utils import translate_text
from src.nutrition_utils import get_nutritional_analysis
from src.history_utils import load_recipe_history, save_recipe_history
from src.meal_plan_utils import load_meal_plan_history, save_meal_plan_history, add_meal_plan_to_history

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
model = configure_gemini()

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
    if st.button("Show Example Ingredients", key="show_example_ingredients"):
        st.info("e.g., 1 lb chicken breast, 2 cups cooked rice, 1 tbsp olive oil, 1 onion, chopped")
    with st.form("recipe_form_sidebar"):
        ingredients_input_val = st.text_input(
            "Main Ingredients (comma separated)",
            placeholder="e.g., chicken, broccoli, rice",
            help="List the main ingredients you have or want to use.",
            key="ingredients_input_box"
        )
        meal_type_input_val = st.selectbox(
            "Meal Type",
            ["Dinner", "Lunch", "Breakfast", "Dessert", "Snack", "Appetizer", "Side Dish"],
            index=0,
            help="What type of meal are you preparing?"
        )
        # Remove cuisine_options and selectbox, only allow user to type their own cuisine
        cuisine_input_val = st.text_input(
            "Cuisine Style (type any cuisine)",
            value="",
            key="custom_cuisine_input",
            help="Type any cuisine style you want (e.g., Italian, Fusion, Street Food, etc.). Leave blank for no preference."
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
        language_options = ["Any (auto-detect)", "English", "Spanish", "French", "German"]
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

    # --- Recipe History Section with Advanced Filtering and Search ---
    st.markdown("---")
    st.header("📜 Recipe History")
    # --- Clear History Button ---
    if st.button("🗑 Clear All History", key="clear_all_history"):
        st.session_state.recipe_history = []
        save_recipe_history([])
        st.session_state.selected_history_index = None
        st.success("Recipe history cleared!")
        st.rerun()
    # Filtering/search UI
    with st.expander("🔍 Filter & Search History", expanded=False):
        with st.form("history_filter_form"):
            search_query = st.text_input("Search by keyword (name, ingredient, cuisine, etc.)", "", key="history_search")
            filter_meal = st.selectbox("Filter by Meal Type", ["All"] + sorted(list(set(r['inputs']['meal_type'] for r in st.session_state.recipe_history))), key="filter_meal")
            filter_cuisine = st.text_input("Filter by Cuisine (partial match)", "", key="filter_cuisine")
            filter_diet = st.selectbox("Filter by Diet", ["All"] + sorted(list(set(r['inputs']['diet'] for r in st.session_state.recipe_history))), key="filter_diet")
            filter_submitted = st.form_submit_button("Apply Filter/Search")

    # Only apply filters if the form is submitted, otherwise show all
    filtered_history = st.session_state.recipe_history
    if 'filter_applied' not in st.session_state:
        st.session_state.filter_applied = False
    if filter_submitted:
        st.session_state.filter_applied = True
        st.session_state.last_search_query = search_query
        st.session_state.last_filter_meal = filter_meal
        st.session_state.last_filter_cuisine = filter_cuisine
        st.session_state.last_filter_diet = filter_diet
    if st.session_state.filter_applied:
        search_query = st.session_state.last_search_query
        filter_meal = st.session_state.last_filter_meal
        filter_cuisine = st.session_state.last_filter_cuisine
        filter_diet = st.session_state.last_filter_diet
        if search_query.strip():
            sq = search_query.lower()
            filtered_history = [r for r in filtered_history if sq in r['name'].lower() or sq in r['text'].lower() or sq in r['inputs']['ingredients'].lower() or sq in r['inputs']['cuisine'].lower()]
        if filter_meal != "All":
            filtered_history = [r for r in filtered_history if r['inputs']['meal_type'] == filter_meal]
        if filter_cuisine.strip():
            fc = filter_cuisine.lower()
            filtered_history = [r for r in filtered_history if fc in r['inputs']['cuisine'].lower()]
        if filter_diet != "All":
            filtered_history = [r for r in filtered_history if r['inputs']['diet'] == filter_diet]

    if filtered_history:
        for idx, recipe in enumerate(reversed(filtered_history)):
            display_idx = len(filtered_history) - 1 - idx
            label = recipe['name'] if recipe['name'] else f"Recipe {display_idx+1}"
            col1, col2 = st.columns([4,1])
            with col1:
                if st.button(label, key=f"history_{display_idx}"):
                    st.session_state.selected_history_index = st.session_state.recipe_history.index(recipe)
            with col2:
                if st.button("🗑️", key=f"delete_{display_idx}"):
                    # Remove the recipe from history
                    del st.session_state.recipe_history[st.session_state.recipe_history.index(recipe)]
                    save_recipe_history(st.session_state.recipe_history)
                    st.session_state.selected_history_index = None
                    st.rerun()
    else:
        st.caption("No recipes match your search/filter.")
        
    st.markdown("---")
    st.header("🗓️ Weekly Meal Planning")
    if 'meal_plan_inputs' not in st.session_state:
        st.session_state.meal_plan_inputs = {day: {'ingredients': '', 'meal_type': 'Dinner', 'cuisine': '', 'diet': 'None'} for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']}
    if 'meal_plan_results' not in st.session_state:
        st.session_state.meal_plan_results = None
    if 'meal_plan_history' not in st.session_state:
        st.session_state.meal_plan_history = load_meal_plan_history()

    with st.expander("Plan Your Week", expanded=False):
        # Add meal plan history section
        if st.session_state.meal_plan_history:
            st.subheader("📜 Meal Plan History")
            for idx, plan in enumerate(reversed(st.session_state.meal_plan_history)):
                col1, col2 = st.columns([4,1])
                with col1:
                    if st.button(f"Meal Plan from {plan['date']}", key=f"mp_history_{idx}"):
                        st.session_state.meal_plan_results = plan['meal_plan']
                        st.session_state.meal_plan_inputs = plan['inputs']
                with col2:
                    if st.button("🗑️", key=f"mp_delete_{idx}"):
                        del st.session_state.meal_plan_history[idx]
                        save_meal_plan_history(st.session_state.meal_plan_history)
                        st.rerun()
            st.markdown("---")

        for day in st.session_state.meal_plan_inputs:
            st.markdown(f"**{day}**")
            st.session_state.meal_plan_inputs[day]['ingredients'] = st.text_input(f"Ingredients for {day}", value=st.session_state.meal_plan_inputs[day]['ingredients'], key=f"mp_ing_{day}")
            st.session_state.meal_plan_inputs[day]['meal_type'] = st.selectbox(f"Meal Type for {day}", ["Dinner", "Lunch", "Breakfast"], index=["Dinner", "Lunch", "Breakfast"].index(st.session_state.meal_plan_inputs[day]['meal_type']), key=f"mp_type_{day}")
            st.session_state.meal_plan_inputs[day]['cuisine'] = st.text_input(f"Cuisine for {day}", value=st.session_state.meal_plan_inputs[day]['cuisine'], key=f"mp_cuisine_{day}")
            st.session_state.meal_plan_inputs[day]['diet'] = st.selectbox(f"Diet for {day}", ["None", "Vegetarian", "Vegan", "Gluten-Free", "Keto", "Paleo", "Dairy-Free", "Low-Carb", "Pescatarian"], index=["None", "Vegetarian", "Vegan", "Gluten-Free", "Keto", "Paleo", "Dairy-Free", "Low-Carb", "Pescatarian"].index(st.session_state.meal_plan_inputs[day]['diet']), key=f"mp_diet_{day}")
            st.markdown("---")
        if st.button("Generate Weekly Meal Plan", key="generate_meal_plan_btn"):
            st.session_state.meal_plan_results = None
            with st.spinner("Generating meal plan for the week..."):
                from src.recipe_generation import generate_recipe, configure_gemini
                from src.recipe_utils import extract_recipe_name
                model = configure_gemini()
                meal_plan = {}
                failed_days = []
                for day, vals in st.session_state.meal_plan_inputs.items():
                    if not vals['ingredients'].strip():
                        st.warning(f"⚠️ No ingredients provided for {day}. Skipping...")
                        continue
                    recipe_text = generate_recipe(model, vals['ingredients'], vals['diet'], vals['cuisine'], vals['meal_type'])
                    if recipe_text:
                        recipe_name = extract_recipe_name(recipe_text)
                        meal_plan[day] = (recipe_name, recipe_text)
                    else:
                        failed_days.append(day)
                        meal_plan[day] = ('Failed Recipe', 'Recipe generation failed. Please try again with different ingredients or preferences.')
                
                if failed_days:
                    st.warning(f"⚠️ Failed to generate recipes for: {', '.join(failed_days)}")
                if meal_plan:
                    st.session_state.meal_plan_results = meal_plan
                    # Save to history
                    st.session_state.meal_plan_history = add_meal_plan_to_history(meal_plan, st.session_state.meal_plan_inputs)
                    st.success("🎉 Weekly meal plan generated!")
                else:
                    st.error("💥 Failed to generate any recipes. Please check your inputs and try again.")

# --- Main Area for Displaying Recipes ---
main_placeholder = st.empty()

if st.session_state.get('meal_plan_results'):
    # Display the meal plan in the main area
    with main_placeholder.container():
        st.header("🗓️ Your Weekly Meal Plan")
        for day, (recipe_name, recipe_text) in st.session_state.meal_plan_results.items():
            st.subheader(f"{day}: {recipe_name}")
            st.markdown(recipe_text)
            st.markdown("---")
        # Add download button for the entire meal plan
        pdf_bytes = meal_plan_to_pdf(st.session_state.meal_plan_results)
        st.download_button(
            label="📄 Download Meal Plan as PDF",
            data=pdf_bytes,
            file_name="Weekly_Meal_Plan.pdf",
            mime="application/pdf"
        )
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
            with st.spinner("Translating..."):
                display_text = translate_text(recipe['text'], view_lang_code)
        st.markdown(display_text)
        # --- Nutritional Analysis for History ---
        st.markdown("#### 🥗 Nutritional Analysis (AI Estimated)")
        nutrition_lang = view_lang_code if view_lang_code != "original" else "en"
        with st.spinner("Analyzing nutrition..."):
            nutrition = get_nutritional_analysis(model, inputs['ingredients'], language=nutrition_lang)
        st.markdown(nutrition)
        # --- Export/Download Buttons ---
        st.markdown("#### Export Recipe")
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
        # --- Print Recipe Button ---
        st.markdown("#### Print Recipe")
        safe_display_text = display_text.replace("'", "&#39;").replace('"', '&quot;').replace("\n", "<br>")
        st.markdown(f'<button onclick="window.print()">🖨️ Print Recipe</button>', unsafe_allow_html=True)
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
            with st.spinner("Translating..."):
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
        # --- Print Recipe Button ---
        st.markdown("#### Print Recipe")
        safe_display_text = display_text.replace("'", "&#39;").replace('"', '&quot;').replace("\n", "<br>")
        st.markdown(f'<button onclick="window.print()">🖨️ Print Recipe</button>', unsafe_allow_html=True)
else:
    # Initial state or after clearing everything
    with main_placeholder.container():
        # Add Meal Plan History section
        if st.session_state.meal_plan_history:
            st.header("📜 Meal Plan History")
            st.markdown("View and manage your previously generated meal plans.")
            
            # Filtering/search UI for meal plans
            with st.expander("🔍 Filter & Search Meal Plans", expanded=False):
                with st.form("meal_plan_filter_form"):
                    search_query = st.text_input("Search by date or recipe name", "", key="mp_search")
                    filter_submitted = st.form_submit_button("Apply Filter/Search")
            
            # Display meal plans
            filtered_plans = st.session_state.meal_plan_history
            if 'meal_plan_filter_applied' not in st.session_state:
                st.session_state.meal_plan_filter_applied = False
            
            if filter_submitted:
                st.session_state.meal_plan_filter_applied = True
                st.session_state.last_meal_plan_search = search_query
            if st.session_state.meal_plan_filter_applied:
                search_query = st.session_state.last_meal_plan_search
                if search_query.strip():
                    sq = search_query.lower()
                    filtered_plans = [plan for plan in filtered_plans if 
                        sq in plan['date'].lower() or 
                        any(sq in recipe_name.lower() for day, (recipe_name, _) in plan['meal_plan'].items())]
            
            for idx, plan in enumerate(reversed(filtered_plans)):
                with st.expander(f"Meal Plan from {plan['date']}", expanded=False):
                    col1, col2 = st.columns([4,1])
                    with col1:
                        if st.button("Load This Meal Plan", key=f"load_mp_{idx}"):
                            st.session_state.meal_plan_results = plan['meal_plan']
                            st.session_state.meal_plan_inputs = plan['inputs']
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"delete_mp_{idx}"):
                            del st.session_state.meal_plan_history[idx]
                            save_meal_plan_history(st.session_state.meal_plan_history)
                            st.rerun()
                    
                    # Display a preview of the meal plan
                    st.markdown("**Preview:**")
                    for day, (recipe_name, _) in plan['meal_plan'].items():
                        st.markdown(f"- **{day}:** {recipe_name}")
            
            st.markdown("---")
        
        # Recipe History section
        if st.session_state.recipe_history:
            st.header("📜 Recipe History")
            st.markdown("View and manage your previously generated recipes.")
            
            # Filtering/search UI for recipes
            with st.expander("🔍 Filter & Search Recipes", expanded=False):
                with st.form("recipe_filter_form"):
                    search_query = st.text_input("Search by keyword (name, ingredient, cuisine, etc.)", "", key="recipe_search")
                    filter_meal = st.selectbox("Filter by Meal Type", ["All"] + sorted(list(set(r['inputs']['meal_type'] for r in st.session_state.recipe_history))), key="recipe_filter_meal")
                    filter_cuisine = st.text_input("Filter by Cuisine (partial match)", "", key="recipe_filter_cuisine")
                    filter_diet = st.selectbox("Filter by Diet", ["All"] + sorted(list(set(r['inputs']['diet'] for r in st.session_state.recipe_history))), key="recipe_filter_diet")
                    filter_submitted = st.form_submit_button("Apply Filter/Search")
            
            # Display recipes
            filtered_history = st.session_state.recipe_history
            if 'recipe_filter_applied' not in st.session_state:
                st.session_state.recipe_filter_applied = False
            
            if filter_submitted:
                st.session_state.recipe_filter_applied = True
                st.session_state.last_recipe_search = search_query
                st.session_state.last_filter_meal = filter_meal
                st.session_state.last_filter_cuisine = filter_cuisine
                st.session_state.last_filter_diet = filter_diet
            
            if st.session_state.recipe_filter_applied:
                search_query = st.session_state.last_recipe_search
                filter_meal = st.session_state.last_filter_meal
                filter_cuisine = st.session_state.last_filter_cuisine
                filter_diet = st.session_state.last_filter_diet
                
                if search_query.strip():
                    sq = search_query.lower()
                    filtered_history = [r for r in filtered_history if 
                        sq in r['name'].lower() or 
                        sq in r['text'].lower() or 
                        sq in r['inputs']['ingredients'].lower() or 
                        sq in r['inputs']['cuisine'].lower()]
                if filter_meal != "All":
                    filtered_history = [r for r in filtered_history if r['inputs']['meal_type'] == filter_meal]
                if filter_cuisine.strip():
                    fc = filter_cuisine.lower()
                    filtered_history = [r for r in filtered_history if fc in r['inputs']['cuisine'].lower()]
                if filter_diet != "All":
                    filtered_history = [r for r in filtered_history if r['inputs']['diet'] == filter_diet]
            
            for idx, recipe in enumerate(reversed(filtered_history)):
                with st.expander(f"{recipe['name']}", expanded=False):
                    col1, col2 = st.columns([4,1])
                    with col1:
                        if st.button("View Recipe", key=f"view_recipe_{idx}"):
                            st.session_state.selected_history_index = st.session_state.recipe_history.index(recipe)
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"delete_recipe_{idx}"):
                            del st.session_state.recipe_history[st.session_state.recipe_history.index(recipe)]
                            save_recipe_history(st.session_state.recipe_history)
                            st.session_state.selected_history_index = None
                            st.rerun()
                    
                    # Display a preview of the recipe
                    st.markdown("**Preview:**")
                    st.markdown(f"**Generated for:** Ingredients: `{recipe['inputs']['ingredients']}`, Meal: `{recipe['inputs']['meal_type']}`, Cuisine: `{recipe['inputs']['cuisine']}`, Diet: `{recipe['inputs']['diet']}`")
            
            st.markdown("---")
        
        # Initial welcome message
        if not st.session_state.recipe_history and not st.session_state.meal_plan_history:
            st.info("🍽️ Fill in your preferences in the sidebar and click '✨ Generate Recipe' to begin!")
            st.markdown("""
            ### How to Use:
            1.  **Enter Ingredients:** List the main ingredients you have on hand in the sidebar.
            2.  **Select Preferences:** Choose your desired meal type, cuisine style, and any dietary needs.
            3.  **Generate:** Click the "Generate Recipe" button.
            4.  **View:** Your custom recipe will appear here.

            Happy cooking! 🍳
            """)