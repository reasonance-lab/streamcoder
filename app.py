import streamlit as st
import requests
import base64
from github import Github
from github import GithubException
import os
from cryptography.fernet import Fernet

# Initialize session state
if 'github_token' not in st.session_state:
    st.session_state.github_token = ''
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Function to encrypt the token
def encrypt_token(token):
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted_token = fernet.encrypt(token.encode())
    return key, encrypted_token

# Function to decrypt the token
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

def github_auth():
    if st.session_state.github_token:
        token = st.session_state.github_token
    else:
        saved_token = load_token()
        if saved_token:
            token = st.text_input("Enter your GitHub Personal Access Token:", value=saved_token, type="password")
        else:
            token = st.text_input("Enter your GitHub Personal Access Token:", type="password")
    
    save_token_checkbox = st.checkbox("Save token for future use", value=True)
    
    if st.button("Authenticate"):
        if token:
            try:
                g = Github(token)
                user = g.get_user()
                st.session_state.github_token = token
                st.session_state.authenticated = True
                if save_token_checkbox:
                    save_token(token)
                st.success(f"Authenticated as {user.login}")
                return g
            except GithubException:
                st.error("Authentication failed. Please check your token.")
        else:
            st.error("Please enter a GitHub token.")
    return None

def list_repos(g):
    user = g.get_user()
    repos = user.get_repos()
    return [repo.name for repo in repos]

def create_repo(g, repo_name):
    user = g.get_user()
    user.create_repo(repo_name)
    st.success(f"Repository '{repo_name}' created successfully.")

def delete_repo(g, repo_name):
    user = g.get_user()
    repo = user.get_repo(repo_name)
    repo.delete()
    st.success(f"Repository '{repo_name}' deleted successfully.")

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

def delete_file(g, repo_name, file_path):
    repo = g.get_user().get_repo(repo_name)
    contents = repo.get_contents(file_path)
    repo.delete_file(contents.path, f"Delete {file_path}", contents.sha)
    st.success(f"File '{file_path}' deleted successfully.")

def upload_file(g, repo_name, file_name, content):
    repo = g.get_user().get_repo(repo_name)
    repo.create_file(file_name, f"Create {file_name}", content)
    st.success(f"File '{file_name}' uploaded successfully.")

def main():
    st.set_page_config(page_title="GitHub Repository Manager", layout="wide")
    st.title("GitHub Repository Manager")

    if not st.session_state.authenticated:
        g = github_auth()
        if not g:
            return
    else:
        g = Github(st.session_state.github_token)

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Repository Management")
        action = st.radio("Select Action", ["List Repositories", "Create Repository", "Delete Repository", "Manage Files"])

    with col2:
        if action == "List Repositories":
            repos = list_repos(g)
            st.write("Your Repositories:")
            for repo in repos:
                st.write(f"- {repo}")

        elif action == "Create Repository":
            new_repo_name = st.text_input("Enter new repository name:")
            if st.button("Create Repository"):
                create_repo(g, new_repo_name)

        elif action == "Delete Repository":
            repos = list_repos(g)
            repo_to_delete = st.selectbox("Select repository to delete:", repos)
            if st.button("Delete Repository"):
                if st.checkbox("I understand this action is irreversible"):
                    delete_repo(g, repo_to_delete)

        elif action == "Manage Files":
            repos = list_repos(g)
            selected_repo = st.selectbox("Select Repository:", repos)
            
            file_action = st.radio("Select File Action", ["List Files", "Edit File", "Delete File", "Upload File"])
            
            if file_action == "List Files":
                files = list_files(g, selected_repo)
                st.write("Files in the repository:")
                for file in files:
                    st.write(f"- {file}")
            
            elif file_action == "Edit File":
                files = list_files(g, selected_repo)
                selected_file = st.selectbox("Select File to Edit:", files)
                content = get_file_content(g, selected_repo, selected_file)
                new_content = st.text_area("Edit File Content:", value=content, height=300)
                commit_message = st.text_input("Commit Message:")
                if st.button("Save Changes"):
                    update_file(g, selected_repo, selected_file, new_content, commit_message)
            
            elif file_action == "Delete File":
                files = list_files(g, selected_repo)
                selected_file = st.selectbox("Select File to Delete:", files)
                if st.button("Delete File"):
                    if st.checkbox("I understand this action is irreversible"):
                        delete_file(g, selected_repo, selected_file)
            
            elif file_action == "Upload File":
                new_file_name = st.text_input("Enter File Name:")
                new_file_content = st.text_area("Enter File Content:", height=300)
                if st.button("Upload File"):
                    upload_file(g, selected_repo, new_file_name, new_file_content)

    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.github_token = ''
        st.experimental_rerun()

if __name__ == "__main__":
    main()
