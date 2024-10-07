import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Database connection
def get_connection():
    conn = sqlite3.connect('school_data.db')
    return conn

# Fetch data from the database
def fetch_data(query):
    conn = get_connection()
    data = pd.read_sql(query, conn)
    conn.close()
    return data

# Add new student
def add_student(student_id, student_name, gender, age, location, household_income):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Students (student_id, student_name, gender, age, location, household_income) VALUES (?, ?, ?, ?, ?, ?)", 
                   (student_id, student_name, gender, age, location, household_income))
    conn.commit()
    conn.close()

# Update student information
def update_student(student_id, student_name, gender, age, location, household_income):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''UPDATE Students SET 
                      student_name = ?, 
                      gender = ?, 
                      age = ?, 
                      location = ?, 
                      household_income = ?, 
                      updated_at = CURRENT_TIMESTAMP 
                      WHERE student_id = ?''',
                   (student_name, gender, age, location, household_income, student_id))
    conn.commit()
    conn.close()

# Display Students Table
def display_students():
    st.subheader("Students")
    students = fetch_data("SELECT * FROM Students")
    st.write(students)

# Edit Student Info Form
def edit_student_info():
    st.subheader("Edit Student Information")
    
    # Fetch all student IDs for dropdown selection
    student_data = fetch_data("SELECT student_id, student_name FROM Students")
    student_options = student_data["student_id"].tolist()
    selected_student_id = st.selectbox("Select Student to Edit", student_options)

    # Display selected student's current info
    student_info = fetch_data(f"SELECT * FROM Students WHERE student_id = '{selected_student_id}'").iloc[0]
    
    with st.form(key='edit_student_form'):
        student_name = st.text_input("Student Name", value=student_info['student_name'])
        gender = st.selectbox("Gender", ['Male', 'Female'], index=0 if student_info['gender'] == 'Male' else 1)
        age = st.number_input("Age", min_value=10, max_value=100, value=int(student_info['age']))
        location = st.text_input("Location", value=student_info['location'])
        household_income = st.text_input("Household Income", value=student_info['household_income'])
        submit_button = st.form_submit_button("Update Student Info")

        if submit_button:
            update_student(selected_student_id, student_name, gender, age, location, household_income)
            st.success(f"Information updated for student ID: {selected_student_id}")

# Interactive Plotting
def interactive_plotting():
    st.subheader("Interactive Student Performance Plots")
    
    # Select student for plotting
    student_data = fetch_data("SELECT student_id, student_name FROM Students")
    student_options = student_data["student_id"].tolist()
    selected_student_id = st.selectbox("Select Student for Plotting", student_options)

    # Fetch scores for the selected student
    scores = fetch_data(f"SELECT Subjects.subject_name, Scores.score FROM Scores INNER JOIN Subjects ON Scores.subject_id = Subjects.subject_id WHERE Scores.student_id = '{selected_student_id}'")

    if not scores.empty:
        # Plot the scores
        st.write(f"Performance Data for Student ID: {selected_student_id}")
        fig = px.bar(scores, x="subject_name", y="score", title="Subject-wise Performance", labels={"score": "Exam Score", "subject_name": "Subject"})
        st.plotly_chart(fig)
    else:
        st.warning("No scores found for this student")

# Add a new student form
def add_student_form():
    st.subheader("Add a New Student")
    with st.form(key='student_form'):
        student_id = st.text_input("Student ID")
        student_name = st.text_input("Student Name")
        gender = st.selectbox("Gender", ['Male', 'Female'])
        age = st.number_input("Age", min_value=10, max_value=100)
        location = st.text_input("Location")
        household_income = st.text_input("Household Income")
        submit_button = st.form_submit_button("Add Student")

        if submit_button:
            add_student(student_id, student_name, gender, age, location, household_income)
            st.success("Student added successfully")

# Main App
def main():
    st.title("School Database Management")

    menu = ["View Students", "Add Student", "Edit Student Info", "Interactive Student Plots"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "View Students":
        display_students()

    elif choice == "Add Student":
        add_student_form()

    elif choice == "Edit Student Info":
        edit_student_info()

    elif choice == "Interactive Student Plots":
        interactive_plotting()

if __name__ == '__main__':
    main()
