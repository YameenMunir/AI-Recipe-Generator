import os
import json
from datetime import datetime

def load_meal_plan_history(history_file="meal_plan_history.json"):
    """Load meal plan history from JSON file."""
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_meal_plan_history(history, history_file="meal_plan_history.json"):
    """Save meal plan history to JSON file."""
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def add_meal_plan_to_history(meal_plan, inputs):
    """Add a new meal plan to the history."""
    history = load_meal_plan_history()
    
    # Create a new meal plan entry
    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "meal_plan": meal_plan,
        "inputs": inputs
    }
    
    # Add to history and save
    history.append(new_entry)
    save_meal_plan_history(history)
    return history 