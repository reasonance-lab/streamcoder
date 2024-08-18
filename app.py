import streamlit as st
import base64
from github import Github, GithubException
import os
from cryptography.fernet import Fernet
import anthropic
from streamlit_monaco import st_monaco
import time 
st.set_page_config(page_title="GitHub Repository Code Manager", layout="wide")

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

# Custom caching mechanism
def timed_cache(seconds):
    def wrapper_cache(func):
        cache = {}
        @st.cache_data
        def wrapped_func(*args, **kwargs):
            key = str(args) + str(kwargs)
            current_time = time.time()
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < seconds:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result
        return wrapped_func
    return wrapper_cache

@timed_cache(seconds=300)  # Cache for 5 minutes
def cached_list_repos():
    if 'g' in st.session_state:
        return list_repos(st.session_state.g)
    return []

@timed_cache(seconds=300)  # Cache for 5 minutes
def cached_list_files(repo_name):
    if 'g' in st.session_state:
        return list_files(st.session_state.g, repo_name)
    return []

@st.cache_data
def cached_get_file_content(repo_name, file_path):
    if 'g' in st.session_state:
        return get_file_content(st.session_state.g, repo_name, file_path)
    return ""

def repo_selection(repos):
    return st.selectbox("Choose a repository:", [""] + repos, key="selected_repo")

def file_selection(files):
    return st.selectbox("Select File to Edit:", [""] + files, key="selected_file")

def repo_actions(g):
    repo_action = st.radio("Select Action", ["Create New Repository", "Delete Repository"])
    if repo_action == "Create New Repository":
        new_repo_name = st.text_input("New Repository Name:")
        if st.button("Create Repository"):
            user = g.get_user()
            user.create_repo(new_repo_name)
            st.success(f"Repository '{new_repo_name}' created successfully.")
            st.rerun()

    elif repo_action == "Delete Repository":
        if st.button("Delete Repository"):
            if st.checkbox("I understand this action is irreversible"):
                user = g.get_user()
                repo = user.get_repo(st.session_state.selected_repo)
                repo.delete()
                st.success(f"Repository '{st.session_state.selected_repo}' deleted successfully.")
                st.rerun()

def logout_button():
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

@st.fragment
def code_editor_and_prompt():
    prompt = st.text_input("Enter your prompt:", placeholder="Load your file and enter your prompt. The code in the file editor will be sent along with your code in the editor.")
    
    if st.button("Execute prompt"):
        with st.spinner("Executing your prompt..."):
            generated_code = generate_code_with_llm(prompt)
            if generated_code:
                st.session_state.file_content = generated_code
            else:
                st.error("Failed to generate code. Please check your Anthropic API key.")
    st.write(f"temp: file content: {st.session_state.file_content}")
    code = st_monaco(value=st.session_state.file_content, language="python", height=600)
    return code

@st.fragment
def save_changes():
    commit_message = st.text_input("Commit Message:")
    if st.button("Save Changes"):
        if st.checkbox("Confirm changes"):
            if all(key in st.session_state for key in ['g', 'selected_repo', 'selected_file']):
                try:
                    update_file(st.session_state.g, st.session_state.selected_repo, st.session_state.selected_file, st.session_state.file_content, commit_message)
                    st.success(f"File '{st.session_state.selected_file}' updated successfully.")
                    # Clear the cache for the updated file
                    cached_get_file_content.clear()
                    st.rerun()
                except GithubException as e:
                    st.error(f"Failed to update file: {str(e)}")
            else:
                st.error("Missing required information to save changes.")

def main():
    st.title("LLM-assisted GitHub Repository Code Manager")

    # Initialize session state variables
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""
    if 'selected_repo' not in st.session_state:
        st.session_state.selected_repo = None
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None

    if not st.session_state.authenticated:
        g = github_auth()
        if g:
            st.session_state.g = g
            st.session_state.authenticated = True
            st.rerun()

    if st.session_state.authenticated:
        try:
            # Sidebar
            with st.sidebar.container(border=True):
                with st.spinner("Loading repositories..."):
                    repos = cached_list_repos()
                    selected_repo = repo_selection(repos)
                
                files = []
                if selected_repo:
                    with st.spinner("Loading files..."):
                        files = cached_list_files(selected_repo)
                
                selected_file = file_selection(files)
                
                if st.button("Show Content"):
                    if selected_repo and selected_file:
                        with st.spinner("Loading file content..."):
                            content = cached_get_file_content(selected_repo, selected_file)
                            st.session_state.file_content = content
                            st.session_state.selected_file=selected_file
                            st.write(f"temp: file content: {st.session_state.file_content}")
                            #loaded=st_monaco(value=st.session_state.file_content, height="600px", language="python")
                            st.rerun()
       
            with st.sidebar.container(border=True):
                repo_actions(st.session_state.g)
            logout_button()

            # Main area
            if st.session_state.selected_file:
                code = code_editor_and_prompt()
                st.session_state.file_content = code  # Update file_content with the latest code from the editor
                save_changes()

        except GithubException as e:
            st.error(f"An error occurred: {str(e)}")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
