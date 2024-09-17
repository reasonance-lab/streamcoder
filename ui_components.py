# ui_components.py

import streamlit as st
import time
import logging
from github_ops import list_repos, list_files, get_file_content, create_repo, delete_repo, create_file, delete_file, update_file

@st.dialog("Create/Delete Repositories")
def repo_management_dialog():
    """
    Dialog for creating or deleting repositories.
    """
    repo_action = st.radio("Choose an action:", ["Create Repository", "Delete Repository"])
    repo_name = st.text_input("Repository Name:")

    if st.button("Submit"):
        g = st.session_state.g
        if repo_action == "Create Repository":
            if repo_name.strip():
                create_repo(g, repo_name.strip())
            else:
                st.error("Repository name cannot be empty.", icon=':material/sentiment_dissatisfied:')
        elif repo_action == "Delete Repository":
            if repo_name.strip():
                delete_repo(g, repo_name.strip())
            else:
                st.error("Repository name cannot be empty.", icon=':material/sentiment_dissatisfied:')

@st.dialog("Create/Delete Files in Repo")
def file_management_dialog():
    """
    Dialog for creating or deleting files within a repository.
    """
    repos = list_repos(st.session_state.g)
    selected_repo = st.selectbox("Choose a repository:", repos)

    if not selected_repo:
        st.warning("Please select a repository first.", icon=':material/info:')
        return

    file_action = st.radio("Choose an action:", ["Create File", "Delete File"])
    file_path = st.text_input("File Path:")
    content = st.text_area("File Content:", height=150) if file_action == "Create File" else None
    commit_message = st.text_input("Commit Message:", key="file_manage_commit")

    if st.button("Submit"):
        g = st.session_state.g
        if file_action == "Create File":
            if file_path.strip() and commit_message.strip():
                create_file(g, selected_repo, file_path.strip(), content, commit_message.strip())
            else:
                st.error("File path and commit message cannot be empty.", icon=':material/sentiment_dissatisfied:')
        elif file_action == "Delete File":
            if file_path.strip() and commit_message.strip():
                delete_file(g, selected_repo, file_path.strip(), commit_message.strip())
            else:
                st.error("File path and commit message cannot be empty.", icon=':material/sentiment_dissatisfied:')

@st.dialog("Choose file from a repo")
def file_selector_dialog():
    """
    Dialog for selecting a file from a repository to edit.
    """
    repos = list_repos(st.session_state.g)
    selected_repo = st.selectbox("Choose a repository:", repos)

    if not selected_repo:
        st.warning("Please select a repository first.", icon=':material/info:')
        return

    files = list_files(st.session_state.g, selected_repo)
    if not files:
        st.warning(f"No files found in repository '{selected_repo}'.", icon=':material/info:')
        return

    selected_file = st.selectbox("Select File to Edit:", files)

    if st.button("Load File Content"):
        if selected_repo and selected_file:
            content = get_file_content(st.session_state.g, selected_repo, selected_file)
            if content is not None:
                st.session_state.file_content = content
                st.session_state.selected_repo = selected_repo
                st.session_state.selected_file = selected_file
                st.experimental_rerun()
        else:
            st.error("Please select both repository and file.", icon=':material/sentiment_dissatisfied:')

@st.dialog("Confirm repo file update")
def dialog_update():
    """
    Dialog to confirm and commit file updates to the repository.
    """
    st.write(f"**Confirm updating {st.session_state.selected_file}**")
    commit_message = st.text_input("Commit Message:", key='commit_message_txt') 
    save_button = st.button(f"Save Changes to {st.session_state.get('selected_file', 'No file selected')}")

    if save_button:
        required_keys = ['g', 'selected_repo', 'selected_file', 'file_content']
        if all(key in st.session_state and st.session_state[key] for key in required_keys):
            st.write("***Attempting to update the file...***")
            try:
                success = update_file(
                    st.session_state.g,
                    st.session_state.selected_repo,
                    st.session_state.selected_file,
                    st.session_state.file_content,
                    commit_message.strip()
                )
                if success:
                    st.success(
                        f"File '{st.session_state.selected_file}' updated successfully. This message will self-destruct in 5 seconds...",
                        icon=':material/sentiment_satisfied:'
                    )
                    time.sleep(5)
                    st.experimental_rerun()
            except Exception as e:
                logging.exception(f"Error updating file '{st.session_state.selected_file}': {e}")
                st.error(f"Error updating file: {str(e)}", icon=':material/sentiment_dissatisfied:')
        else:
            st.error(
                "Missing required information to save changes. This message will self-destruct in 5 seconds...",
                icon=':material/sentiment_dissatisfied:'
            )
            time.sleep(5)
            st.experimental_rerun()

def execute_code_sandbox():
    """
    Executes the code in the sandbox repository by saving it to a specific file.
    """
    try:
        repo = st.session_state.g.get_user().get_repo("streamcoder")  # Update as needed
        file_path = 'pages/sandbox.txt'
        editor_content = st.session_state.file_content
        commit_message = 'Update sandbox.py'
        try:
            # Try to get the file contents (if it exists)
            contents = repo.get_contents(file_path)
            repo.update_file(file_path, commit_message, editor_content, contents.sha)
            st.success(f"Code output saved to {file_path} in the repository.", icon=':material/sentiment_satisfied:')
            logging.info(f"Code saved to '{file_path}' in repo 'streamcoder'.")
        except GithubException as e:
            if e.status == 404:  # File not found
                # If the file doesn't exist, create it
                repo.create_file(file_path, commit_message, editor_content)
                st.success(f"File '{file_path}' created and code saved in the repository.", icon=':material/sentiment_satisfied:')
                logging.info(f"File '{file_path}' created and code saved in repo 'streamcoder'.")
            else:
                raise  # Re-raise the exception if it's not a 404 error
    except Exception as e:
        logging.exception(f"Error saving code output to sandbox: {e}")
        st.error(f"Error saving code output: {str(e)}", icon=':material/sentiment_dissatisfied:')
