import streamlit as st
import sqlite3
import pandas as pd
import random
import joblib

# Load the trained model and column transformer
model = joblib.load('model.pkl')  # Load your trained model
transformer = joblib.load('column_transformer.pkl')  # Load your column transformer

# Predict student average using the model
def predict_student_average(student_data):
    # Define the expected columns with their default values if needed
    default_data = {
        'Public_vs_Private': 'Private',
        'Access_to_Internet': 'Yes',
        'Teacher_to_Student_Ratio': 'Good',
        'Gender': student_data.get('gender'),
        'Location': student_data.get('location', 'Urban'),
        'Academic_Clubs': student_data.get('academic_clubs', 'No'),
        'Sports_Participation': student_data.get('sports', 'No'), 
        'Household_Income': student_data.get('High')  
    }
    
    # Update default_data with actual provided student_data
    default_data.update(student_data)

    # Convert to DataFrame to match model input
    data_to_predict = pd.DataFrame([default_data])

    # Transform the data
    transformed_data = transformer.transform(data_to_predict)
    
    # Predict the average
    predicted_average = model.predict(transformed_data)
    
    return predicted_average[0]


# Database connection
def get_db_connection():
    conn = sqlite3.connect('school_data.db')
    return conn

# Function to add student with predicted average
def add_student(student_id, student_name, gender, age, location, household_income, sports, academic_clubs):
    student_data = {
        'gender': gender,
        'age': age,
        'location': location,
        'household_income': household_income,
        'sports': sports,
        'academic_clubs': academic_clubs
    }
    predicted_avg = predict_student_average(student_data)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Students (student_id, student_name, gender, age, location, household_income, sports, academic_clubs, predicted_average) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (student_id, student_name, gender, age, location, household_income, sports, academic_clubs, predicted_avg))
    conn.commit()
    conn.close()

# Function to update student details and predicted average
def update_student(student_id, student_name, gender, age, location, household_income, sports, academic_clubs):
    student_data = {
        'gender': gender,
        'age': age,
        'location': location,
        'household_income': household_income,
        'sports': sports,
        'academic_clubs': academic_clubs
    }
    predicted_avg = predict_student_average(student_data)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Students SET student_name = ?, gender = ?, age = ?, location = ?, household_income = ?, sports = ?, academic_clubs = ?, predicted_average = ?
        WHERE student_id = ?
    ''', (student_name, gender, age, location, household_income, sports, academic_clubs, predicted_avg, student_id))
    conn.commit()
    conn.close()

# Function to fetch all students
def fetch_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Students')
    students = cursor.fetchall()
    conn.close()
    return students

# Function to display all students in a table with search capability
def display_students(search_query=''):
    students = fetch_students()
    if search_query:
        students = [s for s in students if search_query.lower() in s[1].lower()]
    df = pd.DataFrame(students, columns=[
        "Student ID", "Name", "Gender", "Age", "Location", "Household Income", "Sports", "Academic Clubs", "Average", "Predicted Average", "Date Created", "Last Updated"
    ])
    
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
            add_student(student_id, student_name, gender, age, location, household_income, sports, academic_clubs)
            st.success(f"Student added successfully! ID: {student_id}")

    elif choice == "Update Student":
        st.subheader("Update Student Information")
        search_name = st.text_input("Enter student's name to search:")
        if search_name:
            matching_students = search_students_by_name(search_name)
            if matching_students:
                student_data = matching_students[0]  # For simplicity, take the first match
                st.write(f"Updating details for: {student_data[1]}")
                st.write(f"Student ID: {student_data[0]}")
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

    elif choice == "View Students":
        st.subheader("View All Students")
        search_query = st.text_input("Search by Name")
        display_students(search_query)

# Main App
def main():
    dashboard()

if __name__ == "__main__":
    main()
