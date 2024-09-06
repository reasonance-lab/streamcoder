import streamlit as st
import math

def scientific_calculator():
    st.title("Scientific Calculator")

    # Input
    num1 = st.number_input("Enter a number:", value=0.0)

    # Operation selection
    operation = st.selectbox("Select operation:", 
                             ["Add", "Subtract", "Multiply", "Divide", 
                              "Power", "Square Root", "Sine", "Cosine", "Tangent", 
                              "Logarithm (base 10)", "Natural Logarithm", "Exponential"])

    # Second number input for binary operations
    if operation in ["Add", "Subtract", "Multiply", "Divide", "Power"]:
        num2 = st.number_input("Enter second number:", value=0.0)

    # Calculation
    if st.button("Calculate"):
        try:
            if operation == "Add":
                result = num1 + num2
            elif operation == "Subtract":
                result = num1 - num2
            elif operation == "Multiply":
                result = num1 * num2
            elif operation == "Divide":
                result = num1 / num2
            elif operation == "Power":
                result = num1 ** num2
            elif operation == "Square Root":
                result = math.sqrt(num1)
            elif operation == "Sine":
                result = math.sin(num1)
            elif operation == "Cosine":
                result = math.cos(num1)
            elif operation == "Tangent":
                result = math.tan(num1)
            elif operation == "Logarithm (base 10)":
                result = math.log10(num1)
            elif operation == "Natural Logarithm":
                result = math.log(num1)
            elif operation == "Exponential":
                result = math.exp(num1)
            
            st.success(f"Result: {result}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # History
    if 'calculation_history' not in st.session_state:
        st.session_state.calculation_history = []

    if st.button("Add to History"):
        if 'result' in locals():
            st.session_state.calculation_history.append(f"{operation}: {result}")
            st.success("Calculation added to history.")

    if st.button("Show History"):
        if st.session_state.calculation_history:
            st.write("Calculation History:")
            for item in st.session_state.calculation_history:
                st.write(item)
        else:
            st.info("No calculations in history.")

    if st.button("Clear History"):
        st.session_state.calculation_history = []
        st.success("History cleared.")

scientific_calculator()