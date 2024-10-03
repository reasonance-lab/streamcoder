import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Set page title
st.set_page_config(page_title="Sepsis Prediction")

# Create a header
st.title("Sepsis Prediction Model")

# Create input fields for patient parameters
st.header("Patient Parameters")
age = st.number_input("Age", min_value=0, max_value=120, value=50)
heart_rate = st.number_input("Heart Rate (bpm)", min_value=0, max_value=300, value=80)
systolic_bp = st.number_input("Systolic Blood Pressure (mmHg)", min_value=0, max_value=300, value=120)
temperature = st.number_input("Temperature (°C)", min_value=30.0, max_value=45.0, value=37.0, step=0.1)
respiratory_rate = st.number_input("Respiratory Rate (breaths/min)", min_value=0, max_value=100, value=16)
white_blood_cell_count = st.number_input("White Blood Cell Count (x10^9/L)", min_value=0.0, max_value=100.0, value=7.5, step=0.1)

# Create a button to trigger prediction
if st.button("Predict Sepsis Risk"):
    # Create a dummy dataset for demonstration purposes
    np.random.seed(42)
    X = np.random.rand(1000, 6)
    y = np.random.randint(0, 2, 1000)

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a dummy model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Create input array from user inputs
    input_data = np.array([[age, heart_rate, systolic_bp, temperature, respiratory_rate, white_blood_cell_count]])

    # Make prediction
    prediction = model.predict_proba(input_data)[0]

    # Display results
    st.header("Prediction Results")
    st.write(f"Probability of Sepsis: {prediction[1]:.2%}")
    
    if prediction[1] > 0.5:
        st.error("High risk of sepsis. Please consult a healthcare professional immediately.")
    else:
        st.success("Low risk of sepsis. Continue monitoring the patient's condition.")

    # Display a disclaimer
    st.warning("Disclaimer: This is a fictional model for demonstration purposes only. Do not use for actual medical diagnosis.")

# Add information about the app
st.sidebar.header("About")
st.sidebar.info("This Streamlit app demonstrates a fictional sepsis prediction model. It uses dummy data and a simple random forest classifier for illustration purposes.")