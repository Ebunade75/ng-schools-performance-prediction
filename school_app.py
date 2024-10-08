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
def register_school(school_name, password, access_to_internet, teacher_student_ratio, public_private):
    teacher_student_ratio = categorize_teacher_student_ratio(teacher_student_ratio)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Schools (school_name, password, access_to_internet, teacher_student_ratio, public_private)
                          VALUES (?, ?, ?, ?, ?)''', 
                       (school_name, hash_password(password), access_to_internet, teacher_student_ratio, public_private))
        conn.commit()

# Login a school
def login_school(school_name, password):
    with get_connection() as conn:
        cursor = conn.cursor()
        return fetch_data('''SELECT * FROM Schools WHERE school_name = ? AND password = ?''', 
                          (school_name, hash_password(password)))

# Fetch data from the database
def fetch_data(query, params=()):
    with get_connection() as conn:
        return pd.read_sql(query, conn, params=params)

# Generate a unique student ID
def generate_student_id():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(student_id) FROM Students")
        result = cursor.fetchone()[0]
        if result:
            return f"S{int(result[1:]) + 1:03d}"  # Increment last ID
        else:
            return "S001"  # Start with S001 if no students exist

# Add a new student
def add_student(student_name, gender, age, location, household_income, sports, academic_clubs):
    student_id = generate_student_id()
    household_income = categorize_income(household_income)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Students (student_id, student_name, gender, age, location, household_income, sports, academic_clubs) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (student_id, student_name, gender, age, location, household_income, sports, academic_clubs))
        conn.commit()
    return student_id

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
    search_term = st.text_input("Search Student by Name or ID")
    if search_term:
        query = '''SELECT * FROM Students WHERE student_name LIKE ? OR student_id LIKE ?'''
        student_data = fetch_data(query, (f"%{search_term}%", f"%{search_term}%"))
        
        if not student_data.empty:
            selected_student = student_data.iloc[0]
            with st.form(key='edit_student_form'):
                student_name = st.text_input("Student Name", value=selected_student['student_name'])
                gender = st.selectbox("Gender", ['Male', 'Female'], index=0 if selected_student['gender'] == 'Male' else 1)
                age = st.number_input("Age", min_value=10, max_value=100, value=int(selected_student['age']))
                location = st.text_input("Location", value=selected_student['location'])
                household_income = st.text_input("Household Income", value=selected_student['household_income'])
                sports = st.selectbox("Sports", ['Yes', 'No'], index=0 if selected_student['sports'] == 'Yes' else 1)
                academic_clubs = st.selectbox("Academic Clubs", ['Yes', 'No'], index=0 if selected_student['academic_clubs'] == 'Yes' else 1)
                submit_button = st.form_submit_button("Update Student Info")
                
                if submit_button:
                    update_student(selected_student['student_id'], student_name, gender, age, location, household_income, sports, academic_clubs)
                    st.success(f"Information updated for student ID: {selected_student['student_id']}")
        else:
            st.error("No student found.")

# Add a new student form
def add_student_form():
    st.subheader("Add a New Student")
    with st.form(key='student_form'):
        student_name = st.text_input("Student Name")
        gender = st.selectbox("Gender", ['Male', 'Female'])
        age = st.number_input("Age", min_value=10, max_value=100)
        location = st.selectbox("Location", ['Rural', 'Urban'])
        
        household_income = st.text_input("Household Income")
        try:
            household_income = float(household_income)
        except ValueError:
            st.error("Please enter a valid number for household income.")
            household_income = None
        
        sports = st.selectbox("Sports", ['Yes', 'No'])
        academic_clubs = st.selectbox("Academic Clubs", ['Yes', 'No'])
        submit_button = st.form_submit_button("Add Student")

        if submit_button and household_income is not None:
            student_id = add_student(student_name, gender, age, location, household_income, sports, academic_clubs)
            st.success(f"Student added successfully with ID: {student_id}")

# Predicting End-of-Term Average
def predict_average_section():
    st.subheader("Predict End-of-Term Average")
    search_term = st.text_input("Search Student by Name or ID")
    
    if search_term:
        query = '''
            SELECT student_id, student_name, average, gender, location, household_income, sports, academic_clubs 
            FROM Students WHERE student_name LIKE ? OR student_id LIKE ?
        '''
        student_data = fetch_data(query, (f"%{search_term}%", f"%{search_term}%"))

        if not student_data.empty:
            selected_student = student_data.iloc[0]
            current_average = selected_student["average"]
            gender = selected_student["gender"]
            location = selected_student["location"]
            household_income = selected_student["household_income"]
            sports = selected_student["sports"]
            academic_clubs = selected_student["academic_clubs"]

            st.write(f"Current Average Score: {current_average:.2f}")
            st.write(f"Gender: {gender}")
            st.write(f"Location: {location}")
            st.write(f"Household Income: {household_income}")
            st.write(f"Participates in Sports: {sports}")
            st.write(f"Member of Academic Clubs: {academic_clubs}")

            if st.button("Predict End-of-Term Average"):
                predicted_average = predict_end_of_term_average(
                    current_average, gender, location, household_income, sports, academic_clubs
                )
                st.success(f"Predicted End-of-Term Average: {predicted_average:.2f}")
        else:
            st.error("No student found.")

# Main function to run the app
def main():
    st.title("School Management System")

    if 'login_successful' not in st.session_state:
        st.session_state['login_successful'] = False

    if not st.session_state['login_successful']:
        menu = ["Login", "Register School"]
    else:
        menu = ["Student Management", "Predictive Analytics", "Logout"]
    choice = st.sidebar.selectbox("Select an option", menu)

    if choice == "Login":
        st.subheader("Login")
        school_name = st.text_input("School Name")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            school_data = login_school(school_name, password)
            if not school_data.empty:
                st.session_state['login_successful'] = True
                st.success(f"Welcome, {school_name}!")
            else:
                st.error("Incorrect school name or password. Please try again.")

    elif choice == "Register School":
        st.subheader("Register a New School")
        with st.form(key='school_form'):
            school_name = st.text_input("School Name")
            password = st.text_input("Password", type='password')
            confirm_password = st.text_input("Confirm Password", type='password')
            access_to_internet = st.selectbox("Does the school have access to internet?", ["Yes", "No"])
            teacher_student_ratio = st.number_input("Teacher-to-Student Ratio", min_value=1, max_value=100)
            public_private = st.selectbox("School Type", ["Public", "Private"])
            submit_button = st.form_submit_button("Register School")

            if submit_button:
                if password == confirm_password:
                    register_school(school_name, password, access_to_internet, teacher_student_ratio, public_private)
                    st.success(f"School {school_name} registered successfully!")
                else:
                    st.error("Passwords do not match. Please try again.")

    elif choice == "Student Management" and st.session_state['login_successful']:
        st.subheader("Student Management")
        management_menu = ["Add Student", "Edit Student Info", "View Students"]
        management_choice = st.selectbox("Select Action", management_menu)

        if management_choice == "Add Student":
            add_student_form()

        elif management_choice == "Edit Student Info":
            edit_student_info()

        elif management_choice == "View Students":
            display_students()

    elif choice == "Predictive Analytics" and st.session_state['login_successful']:
        predict_average_section()

    elif choice == "Logout":
        st.session_state['login_successful'] = False
        st.success("Logged out successfully!")

if __name__ == '__main__':
    main()
