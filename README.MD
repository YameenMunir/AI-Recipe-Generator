# 🧑‍🍳 AI Chef - Recipe Generator

This Streamlit application allows users to generate custom recipes based on ingredients they have, along with their dietary preferences, desired cuisine style, and meal type. The recipes are generated using Google's Gemini AI model.

## Features

- **Dynamic Recipe Generation:** Leverages the Gemini AI (specifically `gemini-1.5-flash-latest`) to create unique recipes.
- **Customizable Inputs:**
  - Main ingredients (comma-separated).
  - Meal type (Dinner, Lunch, Breakfast, etc.).
  - Cuisine style (Italian, Indian, Mexican, Any, etc.).
  - Dietary preferences (Vegetarian, Vegan, Gluten-Free, None, etc.).
- **Detailed Recipe Output:** Generated recipes include:
  - Creative Recipe Name
  - Enticing Description
  - Prep Time, Cook Time, Total Time
  - Servings
  - Ingredients list (with measurements, categorized if needed)
  - Optional Equipment list
  - Numbered Preparation Steps (with temperatures and timings)
  - Serving Suggestions
  - Optional Chef's Tips
- **User-Friendly Interface:**
  - Clean layout with inputs in the sidebar and recipe display in the main area.
  - Loading spinners and success/error messages for better user experience.
  - Responsive design for different screen sizes.
- **Session State Management:** Remembers and displays the last generated recipe within the current session until a new one is created.
- **Recipe History with Delete Option:**
  - The sidebar displays a list of all previously generated recipes for the current session and from the `recipe_history.json` file.
  - Each recipe in the history has a delete (🗑️) button next to it. Clicking this button will permanently remove the recipe from the history and update the file.
  - You can click a recipe name to view it again in the main area.

## 🌍 Multi-Language Support

- **Recipe Language Selection:** Choose the language for recipe generation (English, Spanish, French, German, and more coming soon).
- **View/Export in Any Language:** Instantly translate and view/export recipes in your preferred language, including Urdu, Hindi, and Chinese.
- **Unicode PDF Export:** All recipe text (including CJK, Urdu, Hindi, etc.) is exported to PDF using the included DejaVuSans.ttf font for full Unicode support.
- **Font Setup:**
  - The app requires `DejaVuSans.ttf` in the project directory for Unicode PDF export. Download it from [dejavu-fonts.github.io](https://dejavu-fonts.github.io/) if not present.

## 🥗 AI-Powered Nutritional Analysis

- **Automatic Nutrition Info:** Each recipe includes an AI-estimated nutritional breakdown (calories, protein, fat, carbs, fiber, sugar, sodium, cholesterol, etc.).
- **Multi-Language Nutrition:** Nutritional analysis is provided in your selected language.
- **History Nutrition:** View nutrition info for any recipe in your history.

## 📤 Export & History Features

- **Download as PDF or TXT:** Recipes can be exported in any language, with correct Unicode rendering in PDFs.
- **Recipe History:**
  - All recipes are saved in `recipe_history.json` (not committed to git).
  - Advanced filtering and search by name, ingredient, cuisine, meal type, or diet.
  - Delete recipes from history with one click.

## ⚠️ Error Handling & Dependencies

- **Translation/Nutrition Fallbacks:** If translation or nutrition analysis fails, the app displays a warning and continues gracefully.
- **Dependencies:**
  - `googletrans==4.0.0-rc1` for translation
  - `fpdf` for PDF export
  - `DejaVuSans.ttf` for Unicode PDF support

## 🛠️ Development & Contribution

- **Branch Naming:**
  - For multi-language and PDF features: `feature/multilang-unicode-pdf-export`
  - For nutrition features: `feature/nutritional-analysis-multilang-pdf`
- **Commit Messages:**
  - Use short, descriptive messages (e.g., `add nutritional analysis to PDF export`, `fix Unicode PDF for Chinese`)
- **Files to Commit:**
  - `app.py`, `requirements.txt`, `README.MD`
  - Do **not** commit: `recipe_history.json`, font cache files (`DejaVuSans.cw127.pkl`, `DejaVuSans.pkl`)

## Project Structure

The application is primarily contained within a single Python script (`app.py` or similar).

- **AI Configuration & Generation (`generate_recipe`):**
  - Loads the `GEMINI_API_KEY` from a `.env` file.
  - Configures the `google.generativeai` client.
  - Constructs a detailed prompt for the Gemini model based on user inputs.
  - Handles API responses and potential errors during generation.
- **Recipe Name Extraction (`extract_recipe_name`):**
  - A utility function to parse the AI-generated text and extract a suitable recipe name, looking for specific prefixes like "CREATIVE RECIPE NAME:".
- **Streamlit UI:**
  - Sets up the page configuration, title, and main layout.
  - Uses `st.sidebar` for input forms.
  - Uses `st.empty()` and `st.container()` for dynamically updating the main content area to display either a newly generated recipe or a welcome message.
  - Manages application flow and display logic using `st.session_state`.

## Setup and Installation

1. **Clone the Repository (if applicable):**
   ```bash
   git clone <your-repository-url>
   cd <your-repository-directory>
   ```
2. **Create a Virtual Environment (Recommended):**
   ```bash
   python -m venv .venv
   # On Windows
   .\.venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```
3. **Install Dependencies:**
   Make sure you have a `requirements.txt` file with the necessary packages. If not, create one with at least:
   ```txt
   streamlit
   python-dotenv
   google-generativeai
   ```
   Then install:
   ```bash
   pip install -r requirements.txt
   ```
   (If you don't have a `requirements.txt`, you can install them directly: `pip install streamlit python-dotenv google-generativeai`)
4. **Set up Environment Variables:**
   - Create a file named `.env` in the root directory of the project.
   - Add your Google Gemini API key to this file:
     ```env
     GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
     ```
   - **Important:** Add `.env` to your `.gitignore` file to prevent committing your API key.
     ```gitignore
     .env
     .venv/
     __pycache__/
     ```

## How to Run the Application

1. **Activate your virtual environment** (if you created one):
   ```powershell
   .venv\Scripts\activate
   ```
   Or, if you are using a different environment, activate it as appropriate for your OS.
2. **Set up your Gemini API Key:**
   - Create a file named `.env` in the root directory of your project (if it does not already exist).
   - Add the following line to your `.env` file, replacing `YOUR_ACTUAL_GEMINI_API_KEY` with your real Gemini API key:
     ```env
     GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
     ```
   - **Note:** You must have a valid Gemini API key from Google. If you do not have one, visit the [Google AI Studio](https://aistudio.google.com/app/apikey) to generate your key.
   - Make sure `.env` is listed in your `.gitignore` so your API key is not committed to version control.
3. **Install dependencies** (if you haven't already):
   ```powershell
   pip install -r requirements.txt
   ```
4. **Run the Streamlit application:**
   ```powershell
   streamlit run app.py
   ```
   If you encounter an error like `'streamlit' is not recognized`, try:
   ```powershell
   python -m streamlit run app.py
   ```
5. **Open your browser** and go to the local URL provided by Streamlit (usually `http://localhost:8501`).
6. **Usage:**
   - Enter your main ingredients, select your preferences, and click "✨ Generate Recipe".
   - The AI-generated recipe will appear in the main area of the app.

---

## API Key Requirements

- The application requires a valid Google Gemini API key to function.
- You can obtain your API key from the [Google AI Studio API Key page](https://aistudio.google.com/app/apikey).
- Place your API key in a `.env` file as described above.
- If the key is missing or invalid, the app will display an error and stop.



## Files

- `app.py` (or your main script name): Contains all the Python code for the Streamlit application and AI interaction.
- `.env`: Stores your `GEMINI_API_KEY` (should be in `.gitignore`).
- `.gitignore`: Specifies intentionally untracked files that Git should ignore.
- `README.md`: This file.
- `requirements.txt` (optional but recommended): Lists project dependencies.

## Recipe History and Deletion

- All generated recipes are saved in a file called `recipe_history.json`.
- The sidebar displays your recipe history for the current session and from this file.
- To delete a recipe, click the 🗑️ button next to it in the sidebar. The recipe will be removed from both the session and the file.
- If you delete a recipe that is currently being viewed, the selection will be cleared.

## Potential Future Enhancements

- Integrate an alternative image generation API (e.g., Stable Diffusion via Replicate or Hugging Face) for recipe images.
- Add user authentication and personal recipe collections.
- Enable sharing recipes via social media or email.
- Allow users to rate and comment on generated recipes.
- Add a shopping list generator based on recipe ingredients.
---

This README provides an overview of the AI Recipe Generator. Feel free to adjust any details to better match your specific implementation.