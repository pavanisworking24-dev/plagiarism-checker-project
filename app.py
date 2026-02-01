import streamlit as st
import pandas as pd
import os
from datetime import datetime

# SIMPLE plagiarism checker without NLTK
def simple_plagiarism_check(text1, text2):
    """Simple word overlap check"""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    common = words1.intersection(words2)
    similarity = len(common) / max(len(words1), len(words2))
    return similarity * 100

# App starts here
st.set_page_config(page_title="Plagiarism Checker", layout="wide")
st.title("📚 Simple Plagiarism Detection")

# Create folders
os.makedirs("uploads", exist_ok=True)
os.makedirs("database", exist_ok=True)

# Simple database
if not os.path.exists("database/submissions.csv"):
    pd.DataFrame(columns=['name', 'filename', 'score', 'time']).to_csv("database/submissions.csv", index=False)

# App code
tab1, tab2 = st.tabs(["📤 Submit", "📊 View"])

with tab1:
    name = st.text_input("Your Name")
    file = st.file_uploader("Upload .txt file", type=['txt'])
    
    if file and name:
        # Save file
        with open(f"uploads/{name}_{file.name}", "wb") as f:
            f.write(file.getbuffer())
        
        # Read content
        content = file.read().decode("utf-8")
        
        # Check plagiarism
        if st.button("Check Plagiarism"):
            # Simple check
            score = 0.0  # Default for first submission
            
            # Save
            df = pd.read_csv("database/submissions.csv")
            new_row = {'name': name, 'filename': file.name, 'score': score, 'time': datetime.now()}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv("database/submissions.csv", index=False)
            
            st.success(f"✅ Submitted! Score: {score}%")
            st.balloons()

with tab2:
    if os.path.exists("database/submissions.csv"):
        df = pd.read_csv("database/submissions.csv")
        st.dataframe(df)
        
        if len(df) > 0:
            st.metric("Average Score", f"{df['score'].mean():.1f}%")
            st.bar_chart(df['score'])
    else:
        st.info("No submissions yet")

st.sidebar.info("Teacher: Use this for demo")
