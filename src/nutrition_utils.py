import streamlit as st

def get_nutritional_analysis(model, ingredients_text, language='en'):
    """
    Uses Gemini to estimate nutritional information for the given ingredients list.
    Returns a string with the nutritional breakdown (calories, protein, fat, carbs, etc.).
    """
    prompt = f"""
    Analyze the following list of ingredients and estimate the total nutritional content for the entire recipe. 
    Provide a table with Calories, Protein (g), Fat (g), Carbohydrates (g), Fiber (g), and Sugar (g) per recipe and per serving (assume 4 servings if not specified). 
    If possible, also estimate sodium and cholesterol. 
    List any assumptions you make. 
    Respond in {language}.
    Ingredients:\n{ingredients_text}
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.9,
                "max_output_tokens": 800
            }
        )
        return response.text if response.text else "Nutritional analysis not available."
    except Exception as e:
        return f"Nutritional analysis failed: {e}"
