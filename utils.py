# utils.py

import streamlit as st

def initialize_session_state():
    """
    Initializes the Streamlit session state with default values.
    """
    keys_defaults = {
        'authenticated': False,
        'github_token': '',
        'g': None,
        'selected_repo': '',
        'selected_file': '',
        'file_content': '',
        'selected_llm': 'Sonnet-3.5',
        'sandbox_code': '',
    }
    for key, default in keys_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

def load_css():
    """
    Loads custom CSS to style the Streamlit app.
    """
    css = """
    <style>
        .stApp {
            background-color: #f0f0f0;
            color: #333333;
        }
        .stTextInput > div > div > input {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
        }
        .stTextArea > div > div > textarea {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
        }
        .stSelectbox > div > div > select {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
        }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
        }
        .sidebar .sidebar-content {
            background-color: #e0e0e0;
        }
        .stLabel {
            color: #2196F3;
            font-weight: bold;
        }
        .stHeader {
            color: #1976D2;
        }
        .stAce {
            border: 1px solid #2196F3;
        }
        .streamlit-expanderHeader {
            background-color: #e0e0e0;
            color: #333333;
        }
        .stAlert {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
