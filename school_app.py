import streamlit as st
import sqlite3
import pandas as pd
import random

# Database connection
def get_db_connection():
    conn = sqlite3.connect('school_data.db')
    return conn

# Fetch all students
def fetch_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Students')
    students = cursor.fetchall()
    conn.close()
    return students

# Fetch exam scores for a particular student
def fetch_exam_scores(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT exam_id, subject, score FROM ExamScores WHERE student_id = ?', (student_id,))
    scores = cursor.fetchall()
    conn.close()
    return scores

# Function to add exam scores for a student
def add_exam_score(student_id, subject, score):
    exam_id = str(random.randint(100000, 999999))  # Generate a random 6-digit exam ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ExamScores (exam_id, student_id, subject, score)
        VALUES (?, ?, ?, ?)
    ''', (exam_id, student_id, subject, score))
    conn.commit()
    conn.close()

# Update existing exam score by exam_id
def update_exam_score(exam_id, new_score):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE ExamScores SET score = ? WHERE exam_id = ?', (new_score, exam_id))
    conn.commit()
    conn.close()

# Function to calculate a student's overall average
def calculate_student_average(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT AVG(score) FROM ExamScores WHERE student_id = ?', (student_id,))
    avg = cursor.fetchone()[0]
    cursor.execute('UPDATE Students SET average = ? WHERE student_id = ?', (avg, student_id))
    conn.commit()
    conn.close()
    return avg

# Display student exam scores and allow editing
def display_and_edit_scores(student_id):
    # Fetch the exam scores for the selected student
    exam_scores = fetch_exam_scores(student_id)
    if not exam_scores:
        st.write("No exam scores found for this student.")
        return
    
    # Create a DataFrame for easier editing
    df = pd.DataFrame(exam_scores, columns=["Exam ID", "Subject", "Score"])

    # Display the editable table using Streamlit
    st.write("Existing exam scores for this student:")
    edited_df = st.experimental_data_editor(df, num_rows="dynamic")  # Allow dynamic number of rows

    # Check if any changes have been made
    if not df.equals(edited_df):
        # Update the edited scores in the database
        for index, row in edited_df.iterrows():
            update_exam_score(row["Exam ID"], row["Score"])
        st.success("Exam scores updated successfully!")

# Dashboard style with Add Exam Scores functionality
def dashboard():
    st.sidebar.title("Student Management Dashboard")
    menu = ["Home", "Register Student", "Update Student", "Add Exam Scores", "View Students"]
    choice = st.sidebar.selectbox("Select an action", menu)

    if choice == "Home":
        st.title("Welcome to the Student Management Dashboard")
        st.write("Use the sidebar to manage students, add exam scores, or update student information.")

    elif choice == "Add Exam Scores":
        st.subheader("Add or Edit Exam Scores for a Student")
        
        # Search for student by ID
        student_id = st.text_input("Enter Student ID to search:")
        
        if student_id:
            students = fetch_students()
            student_ids = [s[0] for s in students]
            if student_id in student_ids:
                st.write(f"Selected Student ID: {student_id}")
                
                # Display and edit existing exam scores
                display_and_edit_scores(student_id)
                
                # Add new exam score
                st.subheader("Add a New Exam Score")
                subject = st.text_input("Subject")
                score = st.number_input("Score", min_value=0.0, max_value=100.0)
                submit_score_button = st.button("Add Exam Score")
                
                if submit_score_button:
                    add_exam_score(student_id, subject, score)
                    avg = calculate_student_average(student_id)
                    st.success(f"Exam score added successfully! New overall average: {avg:.2f}")
            else:
                st.error("Student ID not found.")

    elif choice == "View Students":
        st.subheader("View All Students")
        students = fetch_students()
        df = pd.DataFrame(students, columns=["Student ID", "Name", "Gender", "Age", "Location", "Household Income", "Sports", "Academic Clubs", "Average"])
        st.dataframe(df)

# Main App
def main():
    dashboard()

if __name__ == "__main__":
    main()
