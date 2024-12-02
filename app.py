# Import necessary libraries
import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
from PIL import Image
import fitz  # PyMuPDF
import plotly.graph_objects as go

# Load external CSS
with open("styles.css") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Configure Generative AI API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get a response from Gemini
def get_gemini_response(input):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(input)
    return response.text

# Function to extract text from uploaded PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

# Function to convert the first page of the PDF to an image
def pdf_to_image(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc.load_page(0)  # Load the first page
    pix = page.get_pixmap()  # Convert the page to a pixmap (image)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

# Progress circle with only progress bar color change
def circular_progress_bar(value, max_value):
    percentage = value / max_value * 100

    # Determine color for the progress bar
    if percentage <= 40:
        color = "darkred"
    elif 41 <= percentage <= 60:
        color = "lightcoral"
    elif 61 <= percentage <= 80:
        color = "orange"
    elif 81 <= percentage <= 90:
        color = "lightgreen"
    else:
        color = "darkgreen"

    # Plotly circular progress bar
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentage,
        title={"text": "Match %"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},  # Change only the progress bar color
            "steps": [  # Keep the background consistent
                {"range": [0, 100], "color": "#e0e0e0"}
            ],
            "threshold": {"line": {"color": "black", "width": 4}, "thickness": 0.75, "value": percentage},
        },
    ))
    st.plotly_chart(fig, use_container_width=True)

# Prompt template for ATS evaluation
input_prompt = """
Hey Act Like a skilled or very experienced ATS (Application Tracking System)
with a deep understanding of the tech field, software engineering, data science, data analytics,
and big data engineering. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive, and you should provide
the best assistance for improving the resumes. Assign the percentage matching based
on JD and
the missing keywords with high accuracy.
resume:{text}
description:{jd}

I want the response in one single string having the structure
{{"JD Match":"%","MissingKeywords:[]","Profile Summary":""}}
"""

# Streamlit app UI
st.markdown(
    """
    <div class="main-title">✨✨✨Smart ATS Resume Tracker✨✨✨</div>
    """,
    unsafe_allow_html=True,
)

# Subheader with reduced size and light white color
st.markdown(
    """
    <div class="subheader">Optimize Your Resume for ATS Systems</div>
    """,
    unsafe_allow_html=True,
)

# Description with reduced size and light white color
st.markdown(
    """
    <div class="description">
        <u class="underline">Upload your resume and optionally paste the job description to get insights!</u>
    </div>
    """,
    unsafe_allow_html=True,
)

# Input fields
jd = st.text_area(
    "📄 Paste the Job Description (Optional)",
    placeholder="Enter the job description here (optional)...",
    height=200,
)
uploaded_file = st.file_uploader(
    "📤 Upload Your Resume (PDF)", type="pdf", help="Upload your resume in PDF format."
)

# If a file is uploaded, display it and convert the first page to an image
if uploaded_file is not None:
    # Show a preview of the uploaded resume
    st.write("📂 **Uploaded Resume:**")
    img = pdf_to_image(uploaded_file)
    st.image(img, caption="Uploaded Resume (First Page)", use_column_width=True)

    st.download_button(
        label="📄 View/Download Uploaded Resume",
        data=uploaded_file.getvalue(),
        file_name=uploaded_file.name,
        mime="application/pdf",
    )

# Submit button
submit = st.button("🚀 Evaluate My Resume")

# Evaluation logic with caching to prevent redundant calculations
@st.cache_data
def evaluate_resume(jd_text, resume_text):
    jd_text = jd_text if jd_text.strip() else "N/A"  # Handle optional JD
    formatted_prompt = input_prompt.format(text=resume_text, jd=jd_text)
    response = get_gemini_response(formatted_prompt)
    return response

# Process on submit
if submit:
    if uploaded_file is not None:
        # Extract text from uploaded resume
        text = input_pdf_text(uploaded_file)

        # Evaluate resume
        response = evaluate_resume(jd, text)

        # Parse the response (assuming it's in JSON format)
        try:
            response_data = json.loads(response)

            st.success("🎉 Evaluation Complete!")
            st.subheader("💼 Your ATS Evaluation Results")
            
            # Match percentage as a progress bar
            match_percentage = int(response_data.get("JD Match", "0").replace("%", ""))
            circular_progress_bar(match_percentage, 100)

            # Display role status
            st.write("🎯 **Role Status:**")
            if 0 <= match_percentage <= 30:
                st.write("❌ You are not eligible for this job role.")
            elif 31 <= match_percentage <= 60:
                st.write("⚠️ Please update your resume for this job role.")
            elif 61 <= match_percentage <= 80:
                st.write("✅ Good, but you need to update your resume.")
            elif 81 <= match_percentage <= 100:
                st.write("🎉 Congrats, you are perfect for this job role!")

            # Display missing keywords
            st.write("📋 **Missing Keywords:**")
            missing_keywords = response_data.get("MissingKeywords", [])
            if missing_keywords:
                st.write(", ".join(missing_keywords))
            else:
                st.write("No keywords are missing. Great job!")

            # Display profile summary
            st.write("📝 **Profile Summary:**")
            st.write(response_data.get("Profile Summary", "No summary provided."))

        except json.JSONDecodeError:
            st.error("❌ Unable to process the response. Please try again!")

    else:
        st.warning("⚠️ Please upload your resume before submitting!")

# Footer styling and content
st.markdown(
    """
    <div class="footer">
        © <a href="https://www.linkedin.com/in/gunjan-kumar-sgv9752/" target="_blank">
        2024 | All Rights Reserved | Made By Gunjan<span class="blink-heart">❤️</span>Singh | 🌐LinkedIn</a>
    </div>
    """,
    unsafe_allow_html=True,
)
