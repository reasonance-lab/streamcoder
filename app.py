# app.py

import streamlit as st
import logging
from utils import initialize_session_state, load_css
from auth import github_auth
from github_ops import list_repos, list_files, get_file_content, update_file
from ui_components import (
    repo_management_dialog,
    file_management_dialog,
    file_selector_dialog,
    dialog_update,
    execute_code_sandbox
)
from llm_utils import generate_code_with_llm
from code_editor import code_editor
from github import GithubException  

def code_editor_and_prompt():
    """
    Displays the code editor and handles prompt-based code generation.
    """
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""

    custom_btns = [
        {
            "name": "Copy",
            "feather": "Copy",
            "alwaysOn": True,
            "commands": ["copyAll", ["infoMessage", 
                            {"text":"Copied to clipboard!",
                             "timeout": 2500, 
                             "classToggle": "show"}
                           ]],
            "style": {"top": "0.46rem", "right": "0.4rem"}
        },
        {
            "name": "Save",
            "feather": "Save",
            "hasText": True,
            "commands": ["save-state", ["response","saved"]],
            "response": "saved",
            "style": {"bottom": "calc(50% - 4.25rem)", "right": "0.4rem"}
        },
        {
            "name": "Save to Sandbox",
            "feather": "Play",
            "primary": True,
            "hasText": True,
            "showWithIcon": True,
            "commands": ["submit"],
            "style": {"bottom": "0.44rem", "right": "0.4rem"}
        },
        {
            "name": "Command",
            "feather": "Terminal",
            "primary": True,
            "hasText": True,
            "commands": ["openCommandPallete"],
            "style": {"bottom": "3.5rem", "right": "0.4rem"}
        }
    ]

    # Style dictionaries
    ace_style = {"borderRadius": "0px 0px 8px 8px"}
    code_style = {"width": "100%"}

    css_string = '''
        background-color: #bee1e5;
        body > #root .ace-streamlit-dark~& {background-color: #262830;}
        .ace-streamlit-dark~& span {color: #fff;opacity: 0.6;  }
        span {color: #000; opacity: 0.5;}
        .code_editor-info.message {width: inherit;margin-right: 75px;order: 2;text-align: center;opacity: 0;transition: opacity 0.7s ease-out;}
        .code_editor-info.message.show {opacity: 0.6;}
        .ace-streamlit-dark~& .code_editor-info.message.show {opacity: 0.5;} 
    '''

    info_msg = (
        f"Current repository/file: {st.session_state.selected_repo} / {st.session_state.selected_file}"
        if 'selected_file' in st.session_state
        else "Create/choose a file from a repository to be able to use Sandbox feature"
    )

    info_bar = {
        "name": "language info",
        "css": css_string,
        "style": {
            "order": "1",
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            "width": "100%",
            "height": "2.0rem",
            "padding": "0rem 0.6rem",
            "padding-bottom": "0.2rem",
            "borderRadius": "8px 8px 0px 0px",
            "zIndex": "9993"
        },
        "info": [{"name": info_msg, "style": {"width": "100%"}}]
    }

    response_dict = code_editor(
        st.session_state.file_content,
        buttons=custom_btns,
        options={"wrap": True, "showLineNumbers": True},
        theme="contrast",
        height=[30, 50],
        focus=True,
        info=info_bar,
        props={"style": ace_style},
        component_props={"style": code_style}
    )

    if len(response_dict['id']) != 0:
        if response_dict['type'] == "submit":
            execute_code_sandbox()
        elif response_dict['type'] == "selection":
            # Handle selection type - FUTURE FEATURE
            pass
        elif response_dict['type'] == "saved":
            st.session_state.file_content = response_dict['text']
            dialog_update()

def main():
    """
    Main function to run the Streamlit application.
    """
    # Initialize session state
    initialize_session_state()

    # Set page configuration
    st.set_page_config(page_title="Streamcoder=LLM+GitHub", layout="wide")

    # Load custom CSS
    load_css()

    # Authentication
    if not st.session_state.authenticated:
        g = github_auth()
        if g:
            st.session_state.g = g
        else:
            st.stop()  # Stop execution if authentication fails

    # UI Layout
    try:
        link_col1, link_col2, popmenu_col3, prompt_col = st.columns([1, 1, 1, 6], vertical_alignment="bottom")
        with link_col1:
            st.page_link("app.py", label="Code editor", icon=":material/terminal:")
        with link_col2:
            st.page_link("https://streamcoder.ploomberapp.io/sandbox", label="Sandbox", icon=":material/play_circle:")
            st.page_link("https://streamcoder.streamlit.app/sandbox", label="Sandbox", icon=":material/play_circle:")
        with popmenu_col3:
            with st.popover("Repo actions", use_container_width=True):
                repo_col1, repo_col2, repo_col3, repo_col4 = st.columns([5, 5, 5, 5], vertical_alignment="bottom")
                with repo_col1:
                    if st.button("Choose file from a repo"):
                        file_selector_dialog()
                with repo_col2:
                    if st.button("Create/Delete Repositories"):
                        repo_management_dialog()
                with repo_col3:
                    if st.button("Create/Delete Files in Repo"):
                        file_management_dialog()
                with repo_col4:
                    if st.button("Logout"):  # FUTURE FEATURE
                        st.session_state.authenticated = False
                        st.session_state.github_token = ''
                        if 'g' in st.session_state:
                            del st.session_state.g
                        st.rerun()
        with prompt_col:
            editor_col1, editor_col2 = st.columns([4, 1], vertical_alignment="bottom")
            with editor_col1:
                user_prompt=""
                with st.popover("Enter prompt", use_container_width=True):
                    st.session_state.selected_llm = st.selectbox("Choose LLM:", ["Sonnet-3.5", "GPT-4o"])
                    user_prompt = st.text_area(
                        label="User prompt",
                        label_visibility="collapsed",
                        placeholder="Enter your prompt for code generation and click.",
                        height=300
                    )
                    if st.button("Execute prompt", key='exec_prompt'):
                        if user_prompt.strip():
                            with st.spinner("Executing your prompt..."):
                                generated_code = generate_code_with_llm(user_prompt, st.session_state.file_content)
                                if generated_code:
                                    st.session_state.file_content = generated_code
                                    st.success("Code generated successfully!", icon=':material/sentiment_satisfied:')
                                    st.rerun()
                                else:
                                    st.error("Failed to generate code. Please check your API key.", icon=':material/sentiment_dissatisfied:')
                        else:
                            st.error("Prompt cannot be empty.", icon=':material/sentiment_dissatisfied:')
            with editor_col2:
                pass  # Placeholder for potential future features

        # Display the code editor and prompt section
        code_editor_and_prompt()

    except GithubException as e:
        logging.error(f"An error occurred: {e}")
        st.error(f"An error occurred: {str(e)}")
        st.session_state.authenticated = False
        if 'g' in st.session_state:
            del st.session_state.g
        st.rerun()

if __name__ == "__main__":
    main()
