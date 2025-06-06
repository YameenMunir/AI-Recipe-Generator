import os
import io
from fpdf import FPDF
import streamlit as st

def recipe_to_pdf(recipe_name, recipe_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    font_path = os.path.join(os.path.dirname(__file__), "..", "DejaVuSans.ttf")
    if not os.path.exists(font_path):
        st.error("DejaVuSans.ttf font file not found in the project root directory. Please download it from https://dejavu-fonts.github.io/ and place it in the project root for full Unicode PDF support.")
        return io.BytesIO(b"")
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", "", 16)
    pdf.cell(0, 10, recipe_name, ln=True)
    pdf.set_font("DejaVu", "", 12)
    for line in recipe_text.split('\n'):
        pdf.multi_cell(0, 8, line)
    pdf_bytes = pdf.output(dest='S').encode('latin1', 'ignore')
    return io.BytesIO(pdf_bytes)

def meal_plan_to_pdf(meal_plan):
    """
    meal_plan: dict of {day: (recipe_name, recipe_text)}
    Returns: BytesIO PDF
    """
    pdf = FPDF()
    font_path = os.path.join(os.path.dirname(__file__), "..", "DejaVuSans.ttf")
    if not os.path.exists(font_path):
        st.error("DejaVuSans.ttf font file not found in the project root directory. Please download it from https://dejavu-fonts.github.io/ and place it in the project root for full Unicode PDF support.")
        return io.BytesIO(b"")
    pdf.add_font("DejaVu", "", font_path, uni=True)
    for day, (recipe_name, recipe_text) in meal_plan.items():
        pdf.add_page()
        pdf.set_font("DejaVu", "", 16)
        pdf.cell(0, 10, f"{day}: {recipe_name}", ln=True)
        pdf.set_font("DejaVu", "", 12)
        for line in recipe_text.split('\n'):
            pdf.multi_cell(0, 8, line)
    pdf_bytes = pdf.output(dest='S').encode('latin1', 'ignore')
    return io.BytesIO(pdf_bytes)
