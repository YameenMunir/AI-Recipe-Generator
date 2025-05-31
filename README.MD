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

## 📁 Project Structure

```
AI-Recipe-Generator/
│
├── app.py                # Main Streamlit app and UI logic
├── recipe_generation.py  # Gemini AI recipe generation logic
├── recipe_utils.py       # Helper functions for recipe formatting/processing
├── nutrition_utils.py    # AI-powered nutrition analysis
├── pdf_utils.py          # Unicode PDF export (multi-language)
├── translation_utils.py  # Recipe translation functions
├── history_utils.py      # Recipe history load/save/delete
│
├── recipe_history.json   # Stores all generated recipes (not in git)
├── requirements.txt      # Python dependencies
├── README.MD             # Project documentation
├── DejaVuSans.ttf        # Font for Unicode PDF export
├── DejaVuSans.cw127.pkl  # Font cache (auto-generated)
├── DejaVuSans.pkl        # Font cache (auto-generated)
└── __pycache__/          # Python bytecode cache
```

### Module Overview
- **app.py**: Main Streamlit entry point and UI logic. Handles user interaction and calls functions from other modules.
- **recipe_generation.py**: Connects to Gemini AI and generates recipes based on user input.
- **recipe_utils.py**: Formats and processes recipe data for display and export.
- **nutrition_utils.py**: Analyzes recipes for nutrition info using AI.
- **pdf_utils.py**: Exports recipes to PDF with full Unicode support for all languages.
- **translation_utils.py**: Translates recipes and nutrition info to supported languages.
- **history_utils.py**: Manages recipe history (save, load, delete) in `recipe_history.json`.
- **recipe_history.json**: Stores all generated recipes (auto-created, not versioned).
- **DejaVuSans.ttf**: Required for Unicode PDF export (download from [dejavu-fonts.github.io](https://dejavu-fonts.github.io/)).
- **DejaVuSans.cw127.pkl**, **DejaVuSans.pkl**: Font cache files (auto-generated, not versioned).
- **__pycache__/**: Python bytecode cache directory.

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
   googletrans==4.0.0-rc1
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
     GEMINI_API_KEY="YOUR ACTUAL GEMINI API KEY"
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
- Place
