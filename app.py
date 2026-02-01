import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import plotly.express as px
from plagiarism_checker import check_plagiarism

# ========== CONFIGURATION ==========
st.set_page_config(
    page_title="Plagiarism Detection System",
    page_icon="🎓",
    layout="wide"
)

# ========== DATABASE FUNCTIONS ==========
def init_database():
    """Initialize CSV database"""
    os.makedirs("database", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    # Create submissions file if not exists
    if not os.path.exists("database/submissions.csv"):
        df = pd.DataFrame(columns=[
            'id', 'student_name', 'roll_number', 'filename',
            'submission_time', 'plagiarism_score', 'status'
        ])
        df.to_csv("database/submissions.csv", index=False)
    
    # Create users file if not exists
    if not os.path.exists("database/users.csv"):
        df = pd.DataFrame(columns=[
            'username', 'password', 'name', 'role'  # role: student/teacher
        ])
        # Add default teacher
        default_teacher = pd.DataFrame([{
            'username': 'teacher',
            'password': 'password123',  # In real app, use hashed passwords
            'name': 'Admin Teacher',
            'role': 'teacher'
        }])
        df = pd.concat([df, default_teacher], ignore_index=True)
        df.to_csv("database/users.csv", index=False)

# ========== AUTHENTICATION ==========
def login_user(username, password):
    """Simple login function"""
    users_df = pd.read_csv("database/users.csv")
    user = users_df[(users_df['username'] == username) & (users_df['password'] == password)]
    
    if len(user) > 0:
        return user.iloc[0].to_dict()
    return None

# ========== HELPER FUNCTIONS ==========
def extract_text(file):
    """Extract text from different file types"""
    content = ""
    
    if file.name.endswith('.txt'):
        content = file.read().decode("utf-8")
        file.seek(0)  # Reset file pointer
    elif file.name.endswith('.pdf'):
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            content += page.extract_text() or ""
    elif file.name.endswith('.docx'):
        from docx import Document
        doc = Document(file)
        for para in doc.paragraphs:
            content += para.text + "\n"
    
    return content

def save_submission(student_name, filename, plagiarism_score):
    """Save submission to CSV"""
    df = pd.read_csv("database/submissions.csv")
    
    new_row = pd.DataFrame([{
        'id': len(df) + 1,
        'student_name': student_name,
        'roll_number': 'N/A',
        'filename': filename,
        'submission_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'plagiarism_score': plagiarism_score,
        'status': 'Submitted'
    }])
    
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv("database/submissions.csv", index=False)

# ========== PAGES ==========
def show_login_page():
    """Show login/register page"""
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.header("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
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
        roll_number = st.text_input("Roll Number")
        
        if st.button("Register"):
            # Add to users.csv
            users_df = pd.read_csv("database/users.csv")
            new_user = pd.DataFrame([{
                'username': new_username,
                'password': new_password,
                'name': student_name,
                'role': 'student'
            }])
            users_df = pd.concat([users_df, new_user], ignore_index=True)
            users_df.to_csv("database/users.csv", index=False)
            st.success("Registration successful! Please login.")

def show_student_dashboard():
    """Student dashboard"""
    st.title(f"👨‍🎓 Welcome, {st.session_state.user_name}")
    
    tab1, tab2 = st.tabs(["📤 Submit Assignment", "📋 My Submissions"])
    
    with tab1:
        st.header("Submit New Assignment")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload your assignment (TXT, PDF, DOCX)",
            type=['txt', 'pdf', 'docx']
        )
        
        if uploaded_file:
            # Save file
            filename = f"{st.session_state.user_name}_{uploaded_file.name}"
            filepath = f"uploads/{filename}"
            
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Extract text
            content = extract_text(uploaded_file)
            
            # Show preview
            with st.expander("📄 Preview your file"):
                st.text_area("Content", content[:1000] + "..." if len(content) > 1000 else content, height=200)
            
            # Check plagiarism
            st.subheader("🔍 Plagiarism Check")
            if st.button("Check for Plagiarism", type="primary"):
                with st.spinner("Analyzing..."):
                    # Get existing submissions (simplified version)
                    if os.path.exists("database/submissions.csv"):
                        submissions_df = pd.read_csv("database/submissions.csv")
                        # For demo, use sample texts
                        existing_texts = [
                            "This is a sample assignment about machine learning.",
                            "Machine learning is a subset of artificial intelligence.",
                            "Artificial intelligence is transforming the world."
                        ]
                    else:
                        existing_texts = []
                    
                    plagiarism_score = check_plagiarism(content, existing_texts)
                    
                    # Show result
                    if plagiarism_score < 20:
                        st.success(f"✅ Low plagiarism: {plagiarism_score:.1f}%")
                    elif plagiarism_score < 50:
                        st.warning(f"⚠️ Moderate plagiarism: {plagiarism_score:.1f}%")
                    else:
                        st.error(f"❌ High plagiarism: {plagiarism_score:.1f}%")
                    
                    # Save submission
                    save_submission(st.session_state.user_name, filename, plagiarism_score)
                    st.balloons()
    
    with tab2:
        st.header("My Submission History")
        if os.path.exists("database/submissions.csv"):
            df = pd.read_csv("database/submissions.csv")
            if 'student_name' in df.columns:
                student_df = df[df['student_name'] == st.session_state.user_name]
                
                if len(student_df) > 0:
                    st.dataframe(student_df)
                else:
                    st.info("No submissions yet!")
            else:
                st.info("No submissions yet!")
        else:
            st.info("No submissions yet!")

def show_teacher_dashboard():
    """Teacher dashboard"""
    st.title(f"👨‍🏫 Teacher Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["📊 All Submissions", "📈 Analytics", "⚙️ Settings"])
    
    with tab1:
        st.header("All Student Submissions")
        
        if os.path.exists("database/submissions.csv"):
            df = pd.read_csv("database/submissions.csv")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                min_score = st.slider("Min plagiarism score", 0, 100, 0)
            with col2:
                max_score = st.slider("Max plagiarism score", 0, 100, 100)
            
            # Filter data
            filtered_df = df[(df['plagiarism_score'] >= min_score) & 
                           (df['plagiarism_score'] <= max_score)]
            
            # Show table
            st.dataframe(filtered_df, use_container_width=True)
            
            # Download button
            st.download_button(
                label="📥 Download as CSV",
                data=filtered_df.to_csv(index=False),
                file_name="submissions.csv",
                mime="text/csv"
            )
        else:
            st.info("No submissions yet!")
    
    with tab2:
        st.header("Analytics Dashboard")
        
        if os.path.exists("database/submissions.csv"):
            df = pd.read_csv("database/submissions.csv")
            
            if len(df) > 0:
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Submissions", len(df))
                with col2:
                    avg_score = df['plagiarism_score'].mean()
                    st.metric("Avg. Plagiarism", f"{avg_score:.1f}%")
                with col3:
                    high_plagiarism = len(df[df['plagiarism_score'] > 50])
                    st.metric("High Plagiarism (>50%)", high_plagiarism)
                with col4:
                    unique_students = df['student_name'].nunique()
                    st.metric("Unique Students", unique_students)
                
                # Charts
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Plagiarism Distribution")
                    st.bar_chart(df['plagiarism_score'])
        else:
            st.info("No submissions yet!")
    
    with tab3:
        st.header("System Settings")
        
        # Add new assignment
        st.subheader("Create New Assignment")
        assignment_name = st.text_input("Assignment Name")
        deadline = st.date_input("Deadline")
        
        if st.button("Create Assignment"):
            st.success(f"Assignment '{assignment_name}' created with deadline {deadline}")

# ========== MAIN APP ==========
def main():
    # Initialize database
    init_database()
    
    # Sidebar
    st.sidebar.title("🎓 Plagiarism System")
    st.sidebar.info("Submit assignments and check for plagiarism")
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None
    
    # Show different pages based on login
    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.user_role == 'student':
            show_student_dashboard()
        else:
            show_teacher_dashboard()

# ========== RUN APP ==========
if __name__ == "__main__":
    main()