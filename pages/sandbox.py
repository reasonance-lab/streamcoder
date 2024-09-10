import streamlit as st

if not "sandbox_code" in st.session_state:
    st.write("No code found to execute. Click 'Save to Sandbox' in the bottom right corner to pass your code to sandbox.")
else:
    exec(st.session_state.sandbox_code)
