import streamlit as st

if not "sandbox_code" in st.session_state:
    st.write("No code found to run.")
else
    exec(st.session_state.sandbox_code)
