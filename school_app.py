import streamlit as st
import sqlite3
import pandas as pd
import random

# Database connection
def get_db_connection():
    conn = sqlite3.connect('school_data.db')
    return conn


# Function to fetch all students
def fetch_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Students')
    students = cursor.fetchall()
    conn.close()
    return students

# Function to search for students by name
def search_students_by_name(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Students WHERE student_name LIKE ?', ('%' + name + '%',))
    students = cursor.fetchall()
    conn.close()
    return students
# Function to fetch exam scores for a student by student ID
def fetch_exam_scores_by_student_id(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ExamScores WHERE student_id = ?', (student_id,))
    exam_scores = cursor.fetchall()
    conn.close()
    return exam_scores

# Function to update an exam score
def update_exam_score(exam_id, subject, score):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE ExamScores SET subject = ?, score = ? WHERE exam_id = ?
    ''', (subject, score, exam_id))
    conn.commit()
    conn.close()


# Function to update student details
def update_student(student_id, student_name, gender, age, location, household_income, sports, academic_clubs):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Students SET student_name = ?, gender = ?, age = ?, location = ?, household_income = ?, sports = ?, academic_clubs = ?
        WHERE student_id = ?
    ''', (student_name, gender, age, location, household_income, sports, academic_clubs, student_id))
    conn.commit()
    conn.close()

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

# Function to display all students in a table with search capability
def display_students(search_query=''):
    students = fetch_students()
    if search_query:
        students = [s for s in students if search_query.lower() in s[1].lower()]
    df = pd.DataFrame(students, columns=["Student ID", "Name", "Gender", "Age", "Location", "Household Income", "Sports", "Academic Clubs", "Average", "Date Created", "Last Updated"])

    st.dataframe(df)

# Dashboard style
def dashboard():
    st.sidebar.title("Student Management Dashboard")
    menu = ["Home", "Register Student", "Update Student", "Add Exam Scores", "View Students"]
    choice = st.sidebar.selectbox("Select an action", menu)

    if choice == "Home":
        st.title("Welcome to the Student Management Dashboard")
        st.write("Use the sidebar to manage students, add exam scores, or update student information.")

    elif choice == "Register Student":
        st.subheader("Register a New Student")
        student_name = st.text_input("Student Name")
        gender = st.selectbox("Gender", ['Male', 'Female'])
        age = st.number_input("Age", min_value=10, max_value=100)
        location = st.selectbox("Location", ['Rural', 'Urban'])
        household_income = st.text_input("Household Income")
        sports = st.selectbox("Sports", ['Yes', 'No'])
        academic_clubs = st.selectbox("Academic Clubs", ['Yes', 'No'])
        submit_button = st.button("Add Student")

        if submit_button:
            student_id = str(random.randint(100000, 999999))  # Generate a random 6-digit student ID
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO Students (student_id, student_name, gender, age, location, household_income, sports, academic_clubs) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (student_id, student_name, gender, age, location, household_income, sports, academic_clubs))
            conn.commit()
            conn.close()
            st.success(f"Student added successfully! ID: {student_id}")

    elif choice == "Update Student":
        st.subheader("Update Student Information")
        search_name = st.text_input("Enter student's name to search:")
        if search_name:
            matching_students = search_students_by_name(search_name)
            if matching_students:
                student_data = matching_students[0]  # For simplicity, take the first match
                st.write(f"Updating details for: {student_data[1]}")
                student_name = st.text_input("Student Name", value=student_data[1])
                gender = st.selectbox("Gender", ['Male', 'Female'], index=0 if student_data[2] == 'Male' else 1)
                age = st.number_input("Age", min_value=10, max_value=100, value=student_data[3])
                location = st.selectbox("Location", ['Rural', 'Urban'], index=0 if student_data[4] == 'Rural' else 1)
                household_income = st.text_input("Household Income", value=student_data[5])
                sports = st.selectbox("Sports", ['Yes', 'No'], index=0 if student_data[6] == 'Yes' else 1)
                academic_clubs = st.selectbox("Academic Clubs", ['Yes', 'No'], index=0 if student_data[7] == 'Yes' else 1)
                update_button = st.button("Update Student")

                if update_button:
                    update_student(student_data[0], student_name, gender, age, location, household_income, sports, academic_clubs)
                    st.success(f"Student {student_name} updated successfully!")
            else:
                st.error("No student found with that name.")

    elif choice == "Add Exam Scores":
        st.subheader("Add Exam Scores for a Student")
        student_id = st.text_input("Enter Student ID:")
        
        if student_id:
            student_scores = fetch_exam_scores_by_student_id(student_id)
            if student_scores:
                st.write("Existing Exam Scores:")
                for exam in student_scores:
                    exam_id, student_id, subject, score = exam
                    st.text_input(f"Subject for Exam ID {exam_id}", value=subject, key=f"subject_{exam_id}")
                    new_score = st.number_input(f"Score for {subject}", min_value=0.0, max_value=100.0, value=score, key=f"score_{exam_id}")
                    if st.button(f"Update Score for Exam ID {exam_id}"):
                        update_exam_score(exam_id, subject, new_score)
                        st.success(f"Score updated for {subject}")
                        avg = calculate_student_average(student_id)
                        st.info(f"New Overall Average: {avg:.2f}")
            else:
                st.write("No exam scores found for this student.")
            
            st.write("Add a New Exam Score:")
            new_subject = st.text_input("New Subject")
            new_score = st.number_input("New Score", min_value=0.0, max_value=100.0)
            if st.button("Add New Exam Score"):
                add_exam_score(student_id, new_subject, new_score)
                avg = calculate_student_average(student_id)
                st.success(f"Exam score added successfully! New overall average: {avg:.2f}")

    elif choice == "View Students":
        st.subheader("View All Students")
        search_query = st.text_input("Search by Name")
        display_students(search_query)

# Main App
def main():
    dashboard()

if __name__ == "__main__":
    main()
