import streamlit as st
import base64
from github import Github, GithubException
import os
from cryptography.fernet import Fernet

# Encryption and token management functions
def encrypt_token(token):
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted_token = fernet.encrypt(token.encode())
    return key, encrypted_token

def decrypt_token(key, encrypted_token):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_token).decode()

def save_token(token):
    key, encrypted_token = encrypt_token(token)
    with open('github_token.key', 'wb') as key_file:
        key_file.write(key)
    with open('github_token.enc', 'wb') as token_file:
        token_file.write(encrypted_token)

def load_token():
    if os.path.exists('github_token.key') and os.path.exists('github_token.enc'):
        with open('github_token.key', 'rb') as key_file:
            key = key_file.read()
        with open('github_token.enc', 'rb') as token_file:
            encrypted_token = token_file.read()
        return decrypt_token(key, encrypted_token)
    return None

# GitHub operations
def list_repos(g):
    user = g.get_user()
    repos = user.get_repos()
    return [repo.name for repo in repos]

def list_files(g, repo_name):
    repo = g.get_user().get_repo(repo_name)
    contents = repo.get_contents("")
    return [content.path for content in contents if content.type == "file"]

def get_file_content(g, repo_name, file_path):
    repo = g.get_user().get_repo(repo_name)
    content = repo.get_contents(file_path)
    return base64.b64decode(content.content).decode()

def update_file(g, repo_name, file_path, content, commit_message):
    repo = g.get_user().get_repo(repo_name)
    contents = repo.get_contents(file_path)
    repo.update_file(contents.path, commit_message, content, contents.sha)
    st.success(f"File '{file_path}' updated successfully.")

# Authentication function
def github_auth():
    st.sidebar.title("GitHub Authentication")
    
    if st.session_state.get('github_token'):
        token = st.session_state.github_token
    else:
        saved_token = load_token()
        if saved_token:
            token = st.sidebar.text_input("GitHub Token:", value=saved_token, type="password")
        else:
            token = st.sidebar.text_input("GitHub Token:", type="password")
    
    save_token_checkbox = st.sidebar.checkbox("Save token for future use", value=True)
    
    if st.sidebar.button("Authenticate"):
        if token:
            try:
                g = Github(token)
                user = g.get_user()
                st.session_state.github_token = token
                st.session_state.authenticated = True
                if save_token_checkbox:
                    save_token(token)
                st.sidebar.success(f"Authenticated as {user.login}")
                return g
            except GithubException:
                st.sidebar.error("Authentication failed. Please check your token.")
        else:
            st.sidebar.error("Please enter a GitHub token.")
    return None

# Main app
def main():
    st.set_page_config(page_title="GitHub Repository Manager", layout="wide")
    st.title("GitHub Repository Manager")

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    g = github_auth()

    if st.session_state.authenticated:
        repos = list_repos(g)
        selected_repo = st.selectbox("Select Repository:", repos)

        if selected_repo:
            files = list_files(g, selected_repo)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Repository Actions")
                repo_action = st.radio("Select Action", ["Create New Repository", "Delete Repository"])
                
                if repo_action == "Create New Repository":
                    new_repo_name = st.text_input("New Repository Name:")
                    if st.button("Create Repository"):
                        user = g.get_user()
                        user.create_repo(new_repo_name)
                        st.success(f"Repository '{new_repo_name}' created successfully.")
                        st.experimental_rerun()
                
                elif repo_action == "Delete Repository":
                    if st.button("Delete Repository"):
                        if st.checkbox("I understand this action is irreversible"):
                            user = g.get_user()
                            repo = user.get_repo(selected_repo)
                            repo.delete()
                            st.success(f"Repository '{selected_repo}' deleted successfully.")
                            st.experimental_rerun()
            
            with col2:
                st.subheader("File Actions")
                file_action = st.radio("Select Action", ["List Files", "Edit File", "Delete File", "Upload File"])
                
                if file_action == "List Files":
                    st.write("Files in the repository:")
                    for file in files:
                        st.write(f"- {file}")
                
                elif file_action == "Edit File":
                    selected_file = st.selectbox("Select File to Edit:", files)
                    if selected_file:
                        content = get_file_content(g, selected_repo, selected_file)
                        new_content = st.text_area("Edit File Content:", value=content, height=300)
                        commit_message = st.text_input("Commit Message:")
                        if st.button("Save Changes"):
                            update_file(g, selected_repo, selected_file, new_content, commit_message)
                
                elif file_action == "Delete File":
                    selected_file = st.selectbox("Select File to Delete:", files)
                    if st.button("Delete File"):
                        if st.checkbox("I understand this action is irreversible"):
                            repo = g.get_user().get_repo(selected_repo)
                            contents = repo.get_contents(selected_file)
                            repo.delete_file(contents.path, f"Delete {selected_file}", contents.sha)
                            st.success(f"File '{selected_file}' deleted successfully.")
                            st.experimental_rerun()
                
                elif file_action == "Upload File":
                    new_file_name = st.text_input("Enter File Name:")
                    new_file_content = st.text_area("Enter File Content:", height=300)
                    if st.button("Upload File"):
                        repo = g.get_user().get_repo(selected_repo)
                        repo.create_file(new_file_name, f"Create {new_file_name}", new_file_content)
                        st.success(f"File '{new_file_name}' uploaded successfully.")
                        st.experimental_rerun()

        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.github_token = ''
            st.experimental_rerun()

if __name__ == "__main__":
    main()
