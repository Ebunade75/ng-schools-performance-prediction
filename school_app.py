import streamlit as st
import pandas as pd
import numpy as np
import uuid
import sqlite3
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
import pickle
from sqlalchemy import create_engine, Column, String, Integer, Float, MetaData, Table

# Set up SQLite database using SQLAlchemy
engine = create_engine('sqlite:///students.db')
meta = MetaData()

# Define the student table schema
students_table = Table(
    'students', meta,
    Column('student_id', String, primary_key=True),
    Column('student_name', String),
    Column('gender', String),
    Column('location', String),
    Column('public_private', String),
    Column('sports_participation', String),
    Column('academic_clubs', String),
    Column('cultural_debate_clubs', String),
    Column('access_to_internet', String),
    Column('infrastructure_challenges', String),
    Column('teacher_to_student_ratio', String),
    Column('household_income', String),
)

# Create the table
meta.create_all(engine)

# Assume the model and column transformer have already been trained and loaded
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('column_transformer.pkl', 'rb') as f:
    ct = pickle.load(f)

# Feature Inputs Function for Simulation
def feature_input_form():
    gender = st.selectbox('Gender', ['Male', 'Female'])
    location = st.selectbox('Location', ['Urban', 'Rural'])
    public_private = st.selectbox('Public/Private', ['Public', 'Private'])
    sports_participation = st.selectbox('Sports Participation', ['Yes', 'No'])
    academic_clubs = st.selectbox('Academic Clubs Participation', ['Yes', 'No'])
    cultural_debate_clubs = st.selectbox('Cultural and Debate Clubs Participation', ['Yes', 'No'])
    access_to_internet = st.selectbox('Access to Internet', ['Yes', 'No'])
    infrastructure_challenges = st.selectbox('Infrastructure Challenges', ['Yes', 'No'])
    teacher_to_student_ratio = st.selectbox('Teacher to Student Ratio', ['Good', 'Average', 'Poor'])
    household_income = st.selectbox('Household Income', ['Excellent', 'Good', 'Average'])
    
    return {
        'Gender': gender,
        'Location': location,
        'Public_vs_Private': public_private,
        'Sports_Participation': sports_participation,
        'Academic_Clubs': academic_clubs,
        'Cultural_and_Debate_Clubs': cultural_debate_clubs,
        'Access_to_Internet': access_to_internet,
        'Infrastructure_Challenges': infrastructure_challenges,
        'Teacher_to_Student_Ratio': teacher_to_student_ratio,
        'Household_Income': household_income
    }

# Function to simulate grade change
def simulate_grade_change(features, model, ct):
    input_df = pd.DataFrame([features])
    
    # Map household income
    income_mapping = {'Excellent': 1, 'Good': 2, 'Average': 3}
    input_df['Household_Income'] = input_df['Household_Income'].map(income_mapping)
    
    input_data_encoded = ct.transform(input_df)
    
    predicted_grade = model.predict(input_data_encoded)
    return predicted_grade[0]

# Function to add a student to the SQLite database
def add_student_to_db(student_id, student_name, features):
    conn = engine.connect()
    insert_query = students_table.insert().values(
        student_id=student_id,
        student_name=student_name,
        gender=features['Gender'],
        location=features['Location'],
        public_private=features['Public_vs_Private'],
        sports_participation=features['Sports_Participation'],
        academic_clubs=features['Academic_Clubs'],
        cultural_debate_clubs=features['Cultural_and_Debate_Clubs'],
        access_to_internet=features['Access_to_Internet'],
        infrastructure_challenges=features['Infrastructure_Challenges'],
        teacher_to_student_ratio=features['Teacher_to_Student_Ratio'],
        household_income=features['Household_Income']
    )
    conn.execute(insert_query)
    conn.close()

# Function to retrieve a student by ID from the SQLite database
def get_student_from_db(student_id):
    conn = engine.connect()
    select_query = students_table.select().where(students_table.c.student_id == student_id)
    result = conn.execute(select_query).fetchone()
    conn.close()
    return result

# Streamlit App
st.title("Student Grade Management System")

# Tabs for functionality
tab1, tab2 = st.tabs(["Add Student", "Search & Simulate"])

# Tab 1: Add New Student
with tab1:
    st.header("Add New Student")

    student_name = st.text_input("Student Name")
    student_id = str(uuid.uuid4())[:8]  # Generate a unique ID for each student
    features = feature_input_form()

    if st.button("Add Student"):
        add_student_to_db(student_id, student_name, features)
        st.success(f"Student {student_name} added successfully! Student ID: {student_id}")

# Tab 2: Search & Simulate
with tab2:
    st.header("Search Student by ID")
    
    search_id = st.text_input("Enter Student ID")
    
    if st.button("Search"):
        student_record = get_student_from_db(search_id)
        
        if student_record:
            student_dict = {
                'Gender': student_record.gender,
                'Location': student_record.location,
                'Public_vs_Private': student_record.public_private,
                'Sports_Participation': student_record.sports_participation,
                'Academic_Clubs': student_record.academic_clubs,
                'Cultural_and_Debate_Clubs': student_record.cultural_debate_clubs,
                'Access_to_Internet': student_record.access_to_internet,
                'Infrastructure_Challenges': student_record.infrastructure_challenges,
                'Teacher_to_Student_Ratio': student_record.teacher_to_student_ratio,
                'Household_Income': student_record.household_income
            }

            st.write(f"**Student Name**: {student_record.student_name}")
            st.write("**Current Features**:")
            st.write(student_dict)

            predicted_grade = simulate_grade_change(student_dict, model, ct)
            st.write(f"**Current Projected Grade**: {predicted_grade:.2f}%")

            st.subheader("Simulate Grade Change")
            new_features = feature_input_form()
            new_predicted_grade = simulate_grade_change(new_features, model, ct)
            st.write(f"**New Projected Grade**: {new_predicted_grade:.2f}%")
        else:
            st.error("Student not found!")
