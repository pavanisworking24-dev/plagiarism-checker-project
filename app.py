import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# ========== CONFIGURATION ==========
st.set_page_config(
    page_title="Plagiarism Detection System",
    page_icon="🎓",
    layout="wide"
)

# Streamlit Cloud settings
MAX_FILE_SIZE_MB = 200  # Streamlit Cloud maximum
ALLOWED_EXTENSIONS = ['.txt', '.pdf', '.docx', '.doc']
MAX_TEXT_LENGTH = 1000000  # Characters to process

# ========== SIMPLE PLAGIARISM CHECKER ==========
def simple_plagiarism_check(new_text, existing_texts):
    """Simple plagiarism check without heavy dependencies"""
    if not existing_texts or not new_text:
        return 0.0
    
    # Simple word overlap method
    new_words = set(new_text.lower().split())
    max_similarity = 0.0
    
    for existing in existing_texts:
        if not existing:
            continue
        
        existing_words = set(existing.lower().split())
        
        if not new_words or not existing_words:
            continue
        
        common = new_words.intersection(existing_words)
        similarity = len(common) / max(len(new_words), len(existing_words))
        
        if similarity > max_similarity:
            max_similarity = similarity
    
    return max_similarity * 100

# ========== FILE PROCESSING ==========
def extract_text_safely(file):
    """Safe text extraction with limits"""
    content = ""
    
    try:
        # Check file size
        file_size = len(file.getvalue()) / (1024 * 1024)  # MB
        if file_size > MAX_FILE_SIZE_MB:
            st.error(f"❌ File too large: {file_size:.1f}MB > {MAX_FILE_SIZE_MB}MB limit")
            return ""
        
        # Extract based on file type
        if file.name.lower().endswith('.txt'):
            # Read text file
            content = file.read(MAX_TEXT_LENGTH).decode('utf-8', errors='ignore')
            file.seek(0)
            
        elif file.name.lower().endswith('.pdf'):
            # Extract from PDF (first 20 pages only)
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file)
            page_limit = min(20, len(pdf_reader.pages))
            
            for i in range(page_limit):
                try:
                    page_text = pdf_reader.pages[i].extract_text()
                    if page_text:
                        content += page_text + "\n"
                except:
                    continue
            
            if len(content.strip()) < 50:
                content = "[SCANNED PDF - Text extraction limited]"
                
        elif file.name.lower().endswith(('.docx', '.doc')):
            # Extract from Word
            try:
                from docx import Document
                doc = Document(file)
                for para in doc.paragraphs[:500]:  # Limit paragraphs
                    content += para.text + "\n"
            except:
                content = "[Could not read Word document fully]"
    
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return ""
    
    return content[:MAX_TEXT_LENGTH]  # Truncate if too long

# ========== DATABASE FUNCTIONS ==========
def init_database():
    os.makedirs("database", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    if not os.path.exists("database/submissions.csv"):
        df = pd.DataFrame(columns=[
            'id', 'student_name', 'filename', 'file_size_mb',
            'submission_time', 'plagiarism_score', 'status'
        ])
        df.to_csv("database/submissions.csv", index=False)
    
    if not os.path.exists("database/users.csv"):
        df = pd.DataFrame(columns=['username', 'password', 'name', 'role'])
        df = pd.concat([df, pd.DataFrame([{
            'username': 'teacher',
            'password': 'password123',
            'name': 'Admin Teacher',
            'role': 'teacher'
        }])], ignore_index=True)
        df.to_csv("database/users.csv", index=False)

def login_user(username, password):
    try:
        users_df = pd.read_csv("database/users.csv")
        user = users_df[(users_df['username'] == username) & (users_df['password'] == password)]
        return user.iloc[0].to_dict() if len(user) > 0 else None
    except:
        return None

def save_submission(student_name, filename, file_size_mb, plagiarism_score):
    try:
        df = pd.read_csv("database/submissions.csv")
        new_row = pd.DataFrame([{
            'id': len(df) + 1,
            'student_name': student_name,
            'filename': filename,
            'file_size_mb': file_size_mb,
            'submission_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'plagiarism_score': plagiarism_score,
            'status': 'Submitted'
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("database/submissions.csv", index=False)
    except Exception as e:
        st.error(f"Error saving submission: {e}")

# ========== APP PAGES ==========
def show_login_page():
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.user_name = user['name']
                st.success(f"Welcome {user['name']}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid credentials!")
    
    with tab2:
        st.header("Register as Student")
        new_username = st.text_input("Choose Username")
        new_password = st.text_input("Choose Password", type="password")
        student_name = st.text_input("Full Name")
        
        if st.button("Register"):
            try:
                users_df = pd.read_csv("database/users.csv")
                new_user = pd.DataFrame([{
                    'username': new_username,
                    'password': new_password,
                    'name': student_name,
                    'role': 'student'
                }])
                users_df = pd.concat([users_df, new_user], ignore_index=True)
                users_df.to_csv("database/users.csv", index=False)
                st.success("✅ Registration successful! Please login.")
            except:
                st.error("❌ Registration failed. Try different username.")

def show_student_dashboard():
    st.title(f"👨‍🎓 Welcome, {st.session_state.user_name}")
    
    tab1, tab2 = st.tabs(["📤 Submit Assignment", "📋 My Submissions"])
    
    with tab1:
        st.header("Submit Assignment")
        
        # File upload with size info
        st.info(f"""
        📁 **Supported files:** TXT, PDF, DOCX (up to {MAX_FILE_SIZE_MB}MB)
        ⚠️ **Note:** Large files are processed partially (first 20 pages for PDF)
        """)
        
        uploaded_file = st.file_uploader(
            "Upload your assignment",
            type=['txt', 'pdf', 'docx', 'doc'],
            help=f"Maximum size: {MAX_FILE_SIZE_MB}MB"
        )
        
        if uploaded_file:
            # Show file info
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.write(f"📄 **File:** {uploaded_file.name}")
            st.write(f"📊 **Size:** {file_size_mb:.2f} MB")
            
            # Extract text
            with st.spinner("Reading file..."):
                content = extract_text_safely(uploaded_file)
            
            if content:
                # Show preview
                with st.expander("📄 Preview (first 500 chars)"):
                    st.text(content[:500] + "..." if len(content) > 500 else content)
                
                # Check plagiarism
                if st.button("🔍 Check Plagiarism", type="primary"):
                    with st.spinner("Checking against previous submissions..."):
                        # Get existing texts
                        existing_texts = []
                        if os.path.exists("database/submissions.csv"):
                            df = pd.read_csv("database/submissions.csv")
                            for _, row in df.iterrows():
                                filepath = f"uploads/{row['filename']}"
                                if os.path.exists(filepath) and filepath.endswith('.txt'):
                                    try:
                                        with open(filepath, 'r', encoding='utf-8') as f:
                                            existing_texts.append(f.read(100000))
                                    except:
                                        continue
                        
                        # Calculate plagiarism
                        plagiarism_score = simple_plagiarism_check(content, existing_texts)
                        
                        # Show result
                        col1, col2 = st.columns(2)
                        with col1:
                            if plagiarism_score < 20:
                                st.success(f"✅ **Score:** {plagiarism_score:.1f}%")
                                st.write("**Status:** Low plagiarism")
                            elif plagiarism_score < 50:
                                st.warning(f"⚠️ **Score:** {plagiarism_score:.1f}%")
                                st.write("**Status:** Moderate plagiarism")
                            else:
                                st.error(f"❌ **Score:** {plagiarism_score:.1f}%")
                                st.write("**Status:** High plagiarism")
                        
                        with col2:
                            # Save file
                            filename = f"{st.session_state.user_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                            filepath = f"uploads/{filename}"
                            with open(filepath, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Save to database
                            save_submission(
                                st.session_state.user_name,
                                filename,
                                file_size_mb,
                                plagiarism_score
                            )
                            
                            st.success("✅ Submission saved!")
                            st.balloons()
            else:
                st.error("❌ Could not read file content")
    
    with tab2:
        st.header("My Submissions")
        if os.path.exists("database/submissions.csv"):
            df = pd.read_csv("database/submissions.csv")
            if 'student_name' in df.columns:
                student_df = df[df['student_name'] == st.session_state.user_name]
                if len(student_df) > 0:
                    # Format for display
                    display_df = student_df[['filename', 'file_size_mb', 'plagiarism_score', 'submission_time']]
                    display_df.columns = ['File', 'Size (MB)', 'Plagiarism %', 'Time']
                    st.dataframe(display_df)
                    
                    # Summary
                    avg_score = student_df['plagiarism_score'].mean()
                    total_submissions = len(student_df)
                    st.metric("Average Plagiarism Score", f"{avg_score:.1f}%")
                    st.metric("Total Submissions", total_submissions)
                else:
                    st.info("📭 No submissions yet")
        else:
            st.info("📭 No submissions yet")

def show_teacher_dashboard():
    st.title("👨‍🏫 Teacher Dashboard")
    
    tab1, tab2 = st.tabs(["📊 All Submissions", "📈 Analytics"])
    
    with tab1:
        st.header("All Student Submissions")
        if os.path.exists("database/submissions.csv"):
            df = pd.read_csv("database/submissions.csv")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                min_score = st.slider("Min plagiarism %", 0, 100, 0)
            with col2:
                max_score = st.slider("Max plagiarism %", 0, 100, 100)
            
            # Filter and display
            filtered_df = df[(df['plagiarism_score'] >= min_score) & 
                           (df['plagiarism_score'] <= max_score)]
            
            if len(filtered_df) > 0:
                # Color code high plagiarism
                def highlight_plagiarism(val):
                    color = 'red' if val > 50 else 'orange' if val > 20 else 'green'
                    return f'color: {color}; font-weight: bold'
                
                styled_df = filtered_df.style.applymap(
                    highlight_plagiarism, 
                    subset=['plagiarism_score']
                )
                st.dataframe(styled_df, use_container_width=True)
                
                # Download
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV Report",
                    data=csv,
                    file_name="plagiarism_report.csv",
                    mime="text/csv"
                )
            else:
                st.info("No submissions match filters")
        else:
            st.info("No submissions yet")
    
    with tab2:
        st.header("Analytics")
        if os.path.exists("database/submissions.csv"):
            df = pd.read_csv("database/submissions.csv")
            
            if len(df) > 0:
                # Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Submissions", len(df))
                with col2:
                    avg = df['plagiarism_score'].mean()
                    st.metric("Avg. Plagiarism", f"{avg:.1f}%")
                with col3:
                    high = len(df[df['plagiarism_score'] > 50])
                    st.metric("High (>50%)", high)
                with col4:
                    students = df['student_name'].nunique()
                    st.metric("Unique Students", students)
                
                # Charts
                st.subheader("Plagiarism Distribution")
                st.bar_chart(df['plagiarism_score'])
                
                # High plagiarism list
                high_df = df[df['plagiarism_score'] > 50]
                if len(high_df) > 0:
                    st.subheader("🚨 High Plagiarism Cases")
                    st.dataframe(high_df[['student_name', 'plagiarism_score', 'filename']])
        else:
            st.info("No data for analytics")

# ========== MAIN APP ==========
def main():
    # Initialize
    init_database()
    
    # Sidebar
    st.sidebar.title("🎓 Plagiarism System")
    st.sidebar.info(f"File limit: {MAX_FILE_SIZE_MB}MB")
    
    # Login state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None
    
    # Show appropriate page
    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.user_role == 'student':
            show_student_dashboard()
        else:
            show_teacher_dashboard()

if __name__ == "__main__":
    main()
