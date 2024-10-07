import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import joblib
import hashlib

# Load the model and column transformer
model = joblib.load('model.pkl')  # Update with your model path
column_transformer = joblib.load('column_transformer.pkl')  # Update with your column transformer path

# Database connection
def get_connection():
    return sqlite3.connect('school_data.db')

# Hash the password for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Register a new school
def register_school(school_name, password, access_to_internet, teacher_student_ratio, infrastructure_challenges, public_private):
    teacher_student_ratio_category = categorize_teacher_student_ratio(teacher_student_ratio)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Schools (school_name, password, access_to_internet, teacher_student_ratio, teacher_student_ratio_category, infrastructure_challenges, public_private)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                       (school_name, hash_password(password), access_to_internet, teacher_student_ratio, teacher_student_ratio_category, infrastructure_challenges, public_private))
        conn.commit()

# Login a school
def login_school(school_name, password):
    with get_connection() as conn:
        cursor = conn.cursor()
        return fetch_data('''SELECT * FROM Schools WHERE school_name = ? AND password = ?''', 
                          (school_name, hash_password(password)))

# Categorize teacher-to-student ratio
def categorize_teacher_student_ratio(teacher_student_ratio):
    try:
        ratio = float(teacher_student_ratio)
        return "Good" if ratio <= 25.0 else "Bad"
    except ValueError:
        return "Invalid Ratio"

# Fetch data from the database
def fetch_data(query, params=()):
    with get_connection() as conn:
        return pd.read_sql(query, conn, params=params)

# Add a new student
def add_student(student_id, student_name, gender, age, location, household_income, sports, academic_clubs):
    household_income = categorize_income(household_income)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Students (student_id, student_name, gender, age, location, household_income, sports, academic_clubs) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (student_id, student_name, gender, age, location, household_income, sports, academic_clubs))
        conn.commit()

# Categorize household income
def categorize_income(household_income):
    if household_income < 70000:
        return "Low"
    elif 70000 <= household_income < 200000:
        return "Average"
    else:
        return "High"

# Update student information
def update_student(student_id, student_name, gender, age, location, household_income, sports, academic_clubs):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''UPDATE Students SET 
                          student_name = ?, 
                          gender = ?, 
                          age = ?, 
                          location = ?, 
                          household_income = ?, 
                          sports = ?,
                          academic_clubs = ?, 
                          updated_at = CURRENT_TIMESTAMP 
                          WHERE student_id = ?''',
                       (student_name, gender, age, location, household_income, sports, academic_clubs, student_id))
        conn.commit()

# Update the student's average score
def update_student_average(student_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT AVG(score) FROM Scores WHERE student_id = ?''', (student_id,))
        average_score = cursor.fetchone()[0]
        cursor.execute('''UPDATE Students SET average = ? WHERE student_id = ?''', (average_score, student_id))
        conn.commit()

# Predict end-of-term average
def predict_end_of_term_average(current_average, gender, location, household_income, sports, academic_clubs):
    input_data = pd.DataFrame({
        'Overall_Percentage': [current_average],
        'Gender': [gender],
        'Location': [location],
        'household_income': [household_income],
        'sports': [sports],
        'academic_clubs': [academic_clubs]
    })
    transformed_data = column_transformer.transform(input_data)
    return model.predict(transformed_data)[0]

# Display Students Table
def display_students():
    st.subheader("Students")
    students = fetch_data('''SELECT * FROM Students''')
    st.write(students)

# Edit Student Info Form
def edit_student_info():
    st.subheader("Edit Student Information")
    student_data = fetch_data('''SELECT student_id, student_name FROM Students''')
    student_options = student_data["student_id"].tolist()
    selected_student_id = st.selectbox("Select Student to Edit", student_options)

    student_info = fetch_data(f'''SELECT * FROM Students WHERE student_id = ?''', (selected_student_id,)).iloc[0]
    
    with st.form(key='edit_student_form'):
        student_name = st.text_input("Student Name", value=student_info['student_name'])
        gender = st.selectbox("Gender", ['Male', 'Female'], index=0 if student_info['gender'] == 'Male' else 1)
        age = st.number_input("Age", min_value=10, max_value=100, value=int(student_info['age']))
        location = st.text_input("Location", value=student_info['location'])
        household_income = st.text_input("Household Income", value=student_info['household_income'])
        sports = st.selectbox("Sports", ['Yes', 'No'])
        academic_clubs = st.selectbox("Academic Clubs", ['Yes', 'No'])
        submit_button = st.form_submit_button("Update Student Info")

        if submit_button:
            update_student(selected_student_id, student_name, gender, age, location, household_income, sports, academic_clubs)
            st.success(f"Information updated for student ID: {selected_student_id}")

# Add a new student form
def add_student_form():
    st.subheader("Add a New Student")
    with st.form(key='student_form'):
        student_id = st.text_input("Student ID")
        student_name = st.text_input("Student Name")
        gender = st.selectbox("Gender", ['Male', 'Female'])
        age = st.number_input("Age", min_value=10, max_value=100)
        location = st.selectbox("Location", ['Rural', 'Urban'])
        
        # Input validation for household income
        household_income = st.text_input("Household Income")
        if household_income:
            try:
                household_income = float(household_income)
            except ValueError:
                st.error("Please enter a valid number for household income.")
                household_income = None
        
        sports = st.selectbox("Sports", ['Yes', 'No'])
        academic_clubs = st.selectbox("Academic Clubs", ['Yes', 'No'])
        submit_button = st.form_submit_button("Add Student")

        if submit_button and household_income is not None:
            add_student(student_id, student_name, gender, age, location, household_income, sports, academic_clubs)
            st.success("Student added successfully")

# Subject and Exam Scores Entry
def subject_scores_entry(student_id):
    st.subheader("Enter Exam Scores")
    subject_data = fetch_data("SELECT subject_id, subject_name FROM Subjects")
    subjects = subject_data["subject_name"].tolist()
    
    scores = {}
    for subject in subjects:
        score = st.number_input(f"Score for {subject}", min_value=0, max_value=100, step=1)
        scores[subject] = score

    if st.button("Submit Scores"):
        with get_connection() as conn:
            cursor = conn.cursor()
            for subject_name, score in scores.items():
                subject_id = subject_data[subject_data["subject_name"] == subject_name]["subject_id"].values[0]
                cursor.execute('''INSERT INTO Scores (student_id, subject_id, score) VALUES (?, ?, ?)''', 
                               (student_id, subject_id, score))
            conn.commit()
            st.success("Scores added successfully!")

# Predicting End-of-Term Average
def predict_average_section():
    st.subheader("Predict End-of-Term Average")

    # Fetch student data for selection
    student_data = fetch_data('''SELECT student_id, student_name, average, gender, location, household_income, sports, academic_clubs FROM Students''')
    student_options = student_data["student_id"].tolist()
    
    selected_student_id = st.selectbox("Select Student", student_options)

    # Get selected student's details
    selected_student_info = student_data[student_data["student_id"] == selected_student_id].iloc[0]

    current_average = selected_student_info["average"]
    gender = selected_student_info["gender"]
    location = selected_student_info["location"]
    household_income = selected_student_info["household_income"]
    sports = selected_student_info["sports"]
    academic_clubs = selected_student_info["academic_clubs"]

    # Display the current average and additional features
    st.write(f"Current Average Score: {current_average:.2f}")
    st.write(f"Gender: {gender}")
    st.write(f"Location: {location}")
    st.write(f"Household Income: {household_income}")
    st.write(f"Participates in Sports: {sports}")
    st.write(f"Member of Academic Clubs: {academic_clubs}")

    if st.button("Predict End-of-Term Average"):
        predicted_average = predict_end_of_term_average(current_average, gender, location, household_income, sports, academic_clubs)
        st.success(f"Predicted End-of-Term Average: {predicted_average:.2f}")

# Main function to run the app
def main():
    st.title("School Management System")

    menu = ["Login", "Register School"]
    choice = st.sidebar.selectbox("Select an option", menu)

    if choice == "Login":
        st.subheader("School Login")
        school_name = st.text_input("School Name")
        password = st.text_input("Password", type='password')
        
        if st.button("Login"):
            school = login_school(school_name, password)
            if school:
                st.session_state['login_successful'] = True
                st.success("Login successful!")

                # Update menu after successful login
                menu.extend(["Student Management", "Predictive Analytics"])
                choice = st.sidebar.selectbox("Select an option", menu)

                if "Student Management" in menu and choice == "Student Management":
                    st.subheader("Student Management")
                    add_student_form()
                    display_students()
                    edit_student_info()
                    student_id = st.text_input("Enter Student ID to Add Scores")
                    if student_id:
                        subject_scores_entry(student_id)

                elif "Predictive Analytics" in menu and choice == "Predictive Analytics":
                    predict_average_section()

            else:
                st.error("Invalid credentials")

    elif choice == "Register School":
        st.subheader("Register New School")
        school_name = st.text_input("School Name")
        password = st.text_input("Password", type='password')
        access_to_internet = st.selectbox("Access to Internet", ['Yes', 'No'])
        teacher_student_ratio = st.number_input("Teacher to Student Ratio", min_value=0.0)
        infrastructure_challenges = st.text_area("Infrastructure Challenges")
        public_private = st.selectbox("Public or Private", ['Public', 'Private'])
        
        if st.button("Register"):
            register_school(school_name, password, access_to_internet, teacher_student_ratio, infrastructure_challenges, public_private)
            st.success("School registered successfully!")

if __name__ == '__main__':
    main()
