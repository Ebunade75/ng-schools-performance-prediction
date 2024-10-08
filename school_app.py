import streamlit as st
import sqlite3
import pandas as pd
import joblib

# Load the pre-trained model and column transformer
column_transformer = joblib.load('column_transformer.pkl')
model = joblib.load('model.pkl')

# Database connection
def get_db_connection():
    conn = sqlite3.connect('school_data.db')
    return conn

# Function to register a school
def register_school(school_name, password, access_to_internet, teacher_student_ratio, public_private):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Schools (school_name, password, access_to_internet, teacher_student_ratio, public_private)
        VALUES (?, ?, ?, ?, ?)
    ''', (school_name, password, access_to_internet, teacher_student_ratio, public_private))
    conn.commit()
    conn.close()

# Function to check if a school exists
def school_exists(school_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Schools WHERE school_name = ?', (school_name,))
    return cursor.fetchone() is not None

# Function to validate login
def validate_login(school_name, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Schools WHERE school_name = ? AND password = ?', (school_name, password))
    return cursor.fetchone() is not None

# Function to fetch all students for prediction
def fetch_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Students')
    students = cursor.fetchall()
    conn.close()
    return students

# Add a new student
def add_student(student_name, gender, age, location, household_income, sports, academic_clubs):
    household_income = categorize_income(household_income)
    student_id = str(uuid.uuid4())  # Generate a unique student ID
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Students (student_id, student_name, gender, age, location, household_income, sports, academic_clubs) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (student_id, student_name, gender, age, location, household_income, sports, academic_clubs))
        conn.commit()
    return student_id 

def add_student_form():
    st.subheader("Add a New Student")
    with st.form(key='student_form'):
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
            student_id = add_student(student_name, gender, age, location, household_income, sports, academic_clubs)
            st.success(f"Student added successfully! ID: {student_id}")

# Categorize teacher-to-student ratio
def categorize_teacher_student_ratio(teacher_student_ratio):
    try:
        ratio = float(teacher_student_ratio)
        return "Good" if ratio <= 25 else "Bad"
    except ValueError:
        return "Invalid Ratio"
    
# Categorize household income
def categorize_income(household_income):
    if household_income < 70000:
        return "Low"
    elif 70000 <= household_income < 200000:
        return "Average"
    else:
        return "High"

# Function to predict end-of-term average using the model
def predict_end_of_term_average(features):
    transformed_features = column_transformer.transform(features)  # Transform the features using ColumnTransformer
    predicted_average = model.predict(transformed_features)  # Predict using the trained model
    return predicted_average[0]  # Return the first (and only) prediction

# Main app
def main():
    st.sidebar.title("Student Management App")
    menu = ["Register School", "Login"]
    choice = st.sidebar.selectbox("Select a page", menu)

    if choice == "Register School":
        st.title("Register a New School")

        # Input fields for school registration
        with st.form(key="school_form"):
            school_name = st.text_input("School Name")
            password = st.text_input("Password", type='password')
            access_to_internet = st.selectbox("Access to Internet in School", ['Yes', 'No'])
            teacher_student_ratio = st.number_input("Teacher to Student Ratio", min_value=1)
            public_private = st.selectbox("Public or Private", ['Public', 'Private'])
            submit = st.form_submit_button("Register School")

        if submit:
            if school_exists(school_name):
                st.error("School name already exists. Please choose another.")
            else:
                register_school(school_name, password, access_to_internet, teacher_student_ratio, public_private)
                st.success(f"School {school_name} registered successfully.")

    elif choice == "Login":
        st.title("School Login")

        # Input fields for school login
        with st.form(key="login_form"):
            school_name = st.text_input("School Name")
            password = st.text_input("Password", type='password')
            login = st.form_submit_button("Login")

        if login:
            if validate_login(school_name, password):
                st.success("Login successful!")
                st.session_state['logged_in'] = True
                st.session_state['school_name'] = school_name
                if st.session_state.logged_in:
                    dashboard()
            else:
                st.error("Invalid school name or password.")

# Dashboard after successful login
def dashboard():
    st.title(f"Welcome to the Dashboard, {st.session_state['school_name']}")
    menu = ["Home", "Register Student", "Upload Exam Scores", "Search Student", "Predict End-of-Term Average"]
    choice = st.selectbox("Select a function", menu)

    if choice == "Home":
        st.write("Use the sidebar to navigate through the app.")

    elif choice == "Register Student":
        st.title("Register a New Student")

        # Input fields for student registration
        with st.form(key="student_form"):
            student_id = st.text_input("Student ID")
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=1, max_value=100)
            gender = st.selectbox("Gender", ["Male", "Female"])
            submit = st.form_submit_button("Register Student")

        if submit:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Students (student_id, student_name, gender, age, location, household_income, sports, academic_clubs, average)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, name, gender, age, '', '', '', '', current_average))
            conn.commit()
            conn.close()
            st.success(f"Student {name} registered successfully.")

    elif choice == "Upload Exam Scores":
        st.title("Upload Exam Scores")

        # Placeholder for uploading exam scores
        uploaded_file = st.file_uploader("Choose an exam score file (CSV)")
        if uploaded_file is not None:
            scores_df = pd.read_csv(uploaded_file)
            st.dataframe(scores_df)  # Display uploaded data
            st.success("Exam scores uploaded successfully!")

    elif choice == "Search Student":
        st.title("Search for a Student")
        
        # Search functionality (for now, simple search by name)
        search_name = st.text_input("Enter student's name to search:")
        students_data = fetch_students()  # Fetch students from the database
        if search_name:
            filtered_students = [s for s in students_data if search_name.lower() in s[1].lower()]  # Assuming name is at index 1
            if filtered_students:
                st.write(f"Found {len(filtered_students)} student(s):")
                st.write(pd.DataFrame(filtered_students, columns=["ID", "Name", "Gender", "Age", "Average"]))
            else:
                st.error("No student found with that name.")

    elif choice == "Predict End-of-Term Average":
        st.title("Predict End-of-Term Average")

        # Input form to enter the student's current average and other relevant features
        with st.form(key="prediction_form"):
            current_average = st.number_input("Enter the student's current average:", min_value=0.0, max_value=100.0)
            # Include other features as necessary, e.g., gender, age, etc.
            age = st.number_input("Age", min_value=1, max_value=100)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            household_income = st.selectbox("Household Income", ["Low", "Average", "High"])
            predict_button = st.form_submit_button("Predict")

        if predict_button:
            # Prepare the input features for prediction
            features = pd.DataFrame({
                'Current Average': [current_average],
                'Age': [age],
                'Gender': [gender],
                'Household Income': [household_income]
            })
            prediction = predict_end_of_term_average(features)
            st.success(f"The predicted end-of-term average is: {prediction:.2f}")

            # Optionally, save the prediction to the student's record if they are registered
            if st.checkbox("Save prediction to student's record"):
                matching_students = [s for s in fetch_students() if s[8] == current_average]  # Assuming average is at index 8
                if matching_students:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE Students SET average = ? WHERE student_id = ?
                    ''', (prediction, matching_students[0][0]))  # Update the first match
                    conn.commit()
                    conn.close()
                    st.success("Prediction saved successfully!")
                else:
                    st.error("No matching student found.")

if __name__ == "__main__":
    main()
