import streamlit as st
import streamlit.components.v1 as components

def calculate_creatinine_clearance(age, weight, serum_creatinine, gender):
    if gender == 'Male':
        creatinine_clearance = ((140 - age) * weight) / (72 * serum_creatinine)
    else:
        creatinine_clearance = (((140 - age) * weight) / (72 * serum_creatinine)) * 0.85
    return round(creatinine_clearance, 2)

st.set_page_config(page_title="Creatinine Clearance Calculator", layout="centered")

st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-6 text-center text-blue-600">Creatinine Clearance Calculator</h1>
    <p class="mb-4 text-gray-700">Calculate Creatinine Clearance using the Cockcroft-Gault Equation</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age (years)", min_value=0, max_value=120, step=1)
    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)

with col2:
    serum_creatinine = st.number_input("Serum Creatinine (mg/dL)", min_value=0.0, step=0.1)
    gender = st.selectbox("Gender", ["Male", "Female"])

if st.button("Calculate", key="calculate_button", help="Click to calculate Creatinine Clearance"):
    if age and weight and serum_creatinine:
        result = calculate_creatinine_clearance(age, weight, serum_creatinine, gender)
        st.markdown(f"""
        <div class="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mt-4" role="alert">
            <p class="font-bold">Result:</p>
            <p>Creatinine Clearance: {result} mL/min</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Please fill in all the fields.")

st.markdown("""
<div class="mt-8 text-sm text-gray-600">
    <p><strong>Note:</strong> This calculator uses the Cockcroft-Gault equation. The result is an estimate and should not replace professional medical advice.</p>
</div>
""", unsafe_allow_html=True)

# Add custom CSS for better styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #4299e1;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #3182ce;
    }
    .stNumberInput>div>div>input {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)