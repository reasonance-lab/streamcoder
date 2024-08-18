import streamlit as st
import base64
from github import Github, GithubException
import os
from cryptography.fernet import Fernet
import anthropic
from streamlit_monaco import st_monaco

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

    github_token = st.secrets["GITHUB_TOKEN"]

    if github_token:
        try:
            g = Github(github_token)
            user = g.get_user()
            st.session_state.github_token = github_token
            st.session_state.authenticated = True
            st.sidebar.success(f"Authenticated as {user.login}")
            return g
        except GithubException:
            st.sidebar.error("Authentication failed. Please check your GitHub token in secrets.")
    else:
        st.sidebar.error("GitHub token not found in secrets.")
    return None

# New function for LLM code generation
def generate_code_with_llm(prompt):
    anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]

    if not anthropic_api_key:
        st.error("Anthropic API key not found in secrets.")
        return None

    client = anthropic.Anthropic(api_key=anthropic_api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=8192,
        temperature=0,
        extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"},
        system="You are an expert Python programmer. Respond only with Python code that addresses the user's request, without any additional explanations.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    return message.content[0].text

@st.fragment
def select_repository(g):
    repos = list_repos(g)
    selected_repo = st.sidebar.selectbox("Choose a repository:", repos)
    return selected_repo

# Fragment for file actions
@st.fragment
def file_actions(g, selected_repo):
    files = list_files(g, selected_repo)
    selected_file = st.sidebar.selectbox("Select File to Edit:", files)
    
    if selected_file and st.sidebar.button("Show Content"):
        content = get_file_content(g, selected_repo, selected_file)
        st.session_state.file_content = content
    
    return selected_file

# Fragment for repository actions
@st.fragment
def repository_actions(g):
    st.sidebar.divider()
    st.sidebar.subheader("Repository Actions")
    repo_action = st.sidebar.radio("Select Action", ["Create New Repository", "Delete Repository"])

    if repo_action == "Create New Repository":
        new_repo_name = st.sidebar.text_input("New Repository Name:")
        if st.sidebar.button("Create Repository"):
            user = g.get_user()
            user.create_repo(new_repo_name)
            st.sidebar.success(f"Repository '{new_repo_name}' created successfully.")
            st.rerun()

    elif repo_action == "Delete Repository":
        if st.sidebar.button("Delete Repository"):
            if st.sidebar.checkbox("I understand this action is irreversible"):
                user = g.get_user()
                repo = user.get_repo(st.session_state.selected_repo)
                repo.delete()
                st.sidebar.success(f"Repository '{st.session_state.selected_repo}' deleted successfully.")
                st.rerun()

# Fragment for code editing and prompt execution
@st.fragment
def code_editor_and_prompt(g, selected_repo, selected_file):
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""
    
    prompt = st.text_input("Enter your prompt:")
    
    code = st_monaco(value=st.session_state.file_content, language="python", height=600, key="monaco_editor")

    if st.button("Execute prompt"):
        with st.spinner("Executing your prompt..."):
            generated_code = generate_code_with_llm(prompt)
            if generated_code:
                st.session_state.file_content = generated_code
                st.rerun(scope="fragment")
            else:
                st.error("Failed to generate code. Please check your Anthropic API key.")

    return code

# Fragment for saving changes
@st.fragment
def save_changes(g, selected_repo, selected_file, code):
    commit_message = st.text_input("Commit Message:")
    if st.button("Save Changes"):
        if st.checkbox("Confirm changes"):
            update_file(g, selected_repo, selected_file, code, commit_message)
            st.success(f"File '{selected_file}' updated successfully.")

# Main app
def main():
    st.set_page_config(page_title="GitHub Repository Manager", layout="wide")
    st.title("GitHub Repository Manager")

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'llm_response' not in st.session_state:
        st.session_state.llm_response = ""

    if not st.session_state.authenticated:
        g = github_auth()
        if g:
            st.session_state.g = g
            st.rerun()
    else:
        g = st.session_state.g

    if st.session_state.authenticated:
        try:
            st.session_state.selected_repo = select_repository(g)

            if st.session_state.selected_repo:
                selected_file = file_actions(g, st.session_state.selected_repo)

                if selected_file:
                    code = code_editor_and_prompt(g, st.session_state.selected_repo, selected_file)
                    save_changes(g, st.session_state.selected_repo, selected_file, code)

            repository_actions(g)

            if st.sidebar.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.github_token = ''
                if 'g' in st.session_state:
                    del st.session_state.g
                st.rerun()

        except GithubException as e:
            st.error(f"An error occurred: {str(e)}")
            st.session_state.authenticated = False
            if 'g' in st.session_state:
                del st.session_state.g
            st.rerun()

if __name__ == "__main__":
    main()
