# Project: AutoDoc: AI-report generator.
# Author: S. Sandhys (San-0602)
# Created: 01-06-2025
# License: All Rights Reserved
# Note: This code is not to be reused, modified, or distributed without permission.

import streamlit as st
import tempfile
import os
import subprocess
import matplotlib.pyplot as plt
import requests
import datetime
import base64
import pandas as pd
from io import StringIO

# Your Cohere API config
COHERE_API_KEY = "yHD8B8Zl1AKzAZtLzsdtVjV9PUzNCTaj4iVmdMB7"
COHERE_API_URL = "https://api.cohere.ai/generate"

def generate_section_ai(section_name: str, topic: str, api_url: str, api_key: str) -> str:
    prompt = f"Write a detailed {section_name} section for a project report on the topic: {topic}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "command-xlarge",
        "prompt": prompt,
        "max_tokens": 600,
        "temperature": 0.7
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                return f"❌ API Error: {data['error'].get('message', 'Unknown error')}"
            if "generations" in data:
                return data["generations"][0]["text"].strip()
            if "generation" in data:
                return data["generation"][0]["text"].strip()
            if "choices" in data:
                return data["choices"][0]["text"].strip()
            return str(data)
        else:
            return f"❌ API request failed with status code {response.status_code}: {response.text}"
    except Exception as e:
        return f"⚠️ Exception during API call: {e}"


def create_sample_graph():
    plt.figure(figsize=(4, 3))
    plt.bar(["Part A", "Part B", "Part C"], [20, 35, 30])
    plt.title("Sample Graph: Project Data")
    
    # Save to bytes buffer and encode as base64
    buf = tempfile.SpooledTemporaryFile()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    img_bytes = buf.read()
    base64_img = base64.b64encode(img_bytes).decode()
    buf.close()
    return base64_img

def analyze_csv(csv_file) -> str:
    """
    Read the CSV and return a simple analysis summary as string.
    """
    try:
        df = pd.read_csv(csv_file)
        summary = df.describe().to_string()
        shape = f"Dataset contains {df.shape[0]} rows and {df.shape[1]} columns."
        return f"{shape}\n\nSummary statistics:\n{summary}"
    except Exception as e:
        return f"⚠️ Could not analyze CSV: {e}"

def generate_pdf_report(topic, author="Anonymous", csv_file=None):
    sections = ["Abstract", "Introduction", "Problem Statement", "Literature Survey", "Conclusion"]
    content = {}

    # Generate AI content for each section
    for section in sections:
        content[section] = generate_section_ai(section, topic, COHERE_API_URL, COHERE_API_KEY)

    # If CSV uploaded, analyze and add a Data Analysis section
    if csv_file:
        csv_analysis = analyze_csv(csv_file)
        content["Data Analysis"] = csv_analysis
        sections.insert(-1, "Data Analysis")  # Insert before Conclusion

    # Create graph image as base64 for embedding
    graph_base64 = create_sample_graph()
    today = datetime.date.today().strftime("%B %d, %Y")

    # Build HTML with Table of Contents
    toc_html = "".join(f"<li>{sec}</li>" for sec in sections + ["Graphs"])
    content_html = ""
    for sec in sections:
        content_html += f"<h2>{sec}</h2><pre style='white-space: pre-wrap;'>{content[sec]}</pre>\n"

    html_content = f"""
    <html>
    <head><title>Report on {topic}</title></head>
    <body>
        <h1>{topic}</h1>
        <h3>Author: {author}</h3>
        <p>Date: {today}</p>

        <h2>Table of Contents</h2>
        <ol>
            {toc_html}
            <li>Graphs</li>
        </ol>

        {content_html}

        <h2>Graphs</h2>
        <img src="data:image/png;base64,{graph_base64}" width="500"/>

    </body>
    </html>
    """

    # Save HTML temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        f.write(html_content.encode('utf-8'))
        html_path = f.name

    pdf_path = os.path.splitext(html_path)[0] + ".pdf"

    try:
        subprocess.run([
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            "--enable-local-file-access",
            html_path,
            pdf_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        st.error(f"❌ Error generating PDF: {e}")
        return None
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)

    return pdf_path

# ------------------ Streamlit App Interface ------------------ #

st.title("📄 AutoDoc: AI-Powered Project Report Generator")

topic = st.text_input("Enter your project topic")
author = st.text_input("Enter your name", "Anonymous")

country = st.selectbox("Select your country", ["India", "Other"])
st.markdown("---")

csv_file = st.file_uploader("Upload CSV File (optional)", type=["csv"])

payment_required = "₹1 only" if country == "India" else "$1 only"
st.info(f"⚠️ Report download costs {payment_required} — no actual transaction, just for demo 😄")

if st.button("Generate Full Report"):
    if not topic.strip():
        st.warning("Please enter a project topic.")
    else:
        with st.spinner("Generating report using AI..."):
            pdf_file = generate_pdf_report(topic, author, csv_file)

        if pdf_file:
            with open(pdf_file, "rb") as f:
                pdf_bytes = f.read()
            st.success("✅ Report generated successfully!")
            st.download_button(f"💾 Download Full Report ({payment_required})",
                               pdf_bytes, f"{topic}_report.pdf", "application/pdf")
            os.remove(pdf_file)
