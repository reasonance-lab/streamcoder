import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

# Set page title
st.set_page_config(page_title="Sepsis Prediction Model")

# Create a header
st.title("Sepsis Prediction Model")

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=["txt", "psv"])

if uploaded_file is not None:
    # Read the file
    content = uploaded_file.read().decode("utf-8")
    
    # Split the content into lines
    lines = content.strip().split('\n')
    
    # Get the header
    header = lines[0].split('|')
    
    # Parse the data, handling missing columns
    data = []
    for line in lines[1:]:
        row = line.split('|')
        # Pad the row with NaN if it's shorter than the header
        row += [np.nan] * (len(header) - len(row))
        data.append(row)
    
    # Create a DataFrame
    df = pd.DataFrame(data, columns=header)
    
    # Display the first few rows of the data
    st.write("First few rows of the uploaded data:")
    st.write(df.head())

    # Preprocess the data
    # Replace 'NaN' strings with np.nan
    df = df.replace('NaN', np.nan)
    
    # Convert all columns to numeric, errors will be set as NaN
    df = df.apply(pd.to_numeric, errors='coerce')

    # Check if 'SepsisLabel' is in the DataFrame
    if 'SepsisLabel' not in df.columns:
        st.error("Error: 'SepsisLabel' column is missing from the data.")
    else:
        # Split features and target
        X = df.drop(['SepsisLabel'], axis=1)
        y = df['SepsisLabel']

        # Impute missing values
        imputer = SimpleImputer(strategy='mean')
        X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

        # Scale the features
        scaler = StandardScaler()
        X_scaled = pd.DataFrame(scaler.fit_transform(X_imputed), columns=X_imputed.columns)

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        # Train the model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Make predictions
        y_pred = model.predict(X_test)

        # Calculate accuracy
        accuracy = accuracy_score(y_test, y_pred)

        # Display results
        st.write(f"Model Accuracy: {accuracy:.2f}")

        # Display classification report
        st.write("Classification Report:")
        st.text(classification_report(y_test, y_pred))

        # Feature importance
        feature_importance = pd.DataFrame({'feature': X.columns, 'importance': model.feature_importances_})
        feature_importance = feature_importance.sort_values('importance', ascending=False)
        st.write("Top 10 Most Important Features:")
        st.write(feature_importance.head(10))

        # Allow user to input values for prediction
        st.header("Predict Sepsis")
        user_input = {}
        for feature in X.columns:
            user_input[feature] = st.number_input(f"Enter value for {feature}", value=0.0)

        # Create a dataframe from user input
        user_df = pd.DataFrame([user_input])

        # Impute and scale user input
        user_imputed = pd.DataFrame(imputer.transform(user_df), columns=user_df.columns)
        user_scaled = pd.DataFrame(scaler.transform(user_imputed), columns=user_imputed.columns)

        # Make prediction
        if st.button("Predict"):
            prediction = model.predict(user_scaled)
            probability = model.predict_proba(user_scaled)
            st.write(f"Prediction: {'Sepsis' if prediction[0] == 1 else 'No Sepsis'}")
            st.write(f"Probability of Sepsis: {probability[0][1]:.2f}")
else:
    st.write("Please upload a text file (.txt) or pipe-separated values file (.psv) to proceed.")
