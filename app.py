import streamlit as st
import base64
from github import Github, GithubException
import os
from cryptography.fernet import Fernet
import anthropic

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
    
    # Read GitHub token from secrets
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
    # Read Anthropic API key from secrets
    anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
    
    if not anthropic_api_key:
        st.error("Anthropic API key not found in secrets.")
        return None

    client = anthropic.Anthropic(api_key=anthropic_api_key)
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        temperature=0,
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
                            st.rerun()
                    
                    elif repo_action == "Delete Repository":
                        if st.button("Delete Repository"):
                            if st.checkbox("I understand this action is irreversible"):
                                user = g.get_user()
                                repo = user.get_repo(selected_repo)
                                repo.delete()
                                st.success(f"Repository '{selected_repo}' deleted successfully.")
                                st.rerun()
                
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
                            
                            # LLM Code Generation
                            st.subheader("Generate Code with LLM")
                            prompt = st.text_area("Enter your prompt for code generation:")
                            if st.button("Generate Code"):
                                with st.spinner("Generating code..."):
                                    generated_code = generate_code_with_llm(prompt)
                                    if generated_code:
                                        st.session_state.llm_response = generated_code
                                        st.code(st.session_state.llm_response, language="python")
                                    else:
                                        st.error("Failed to generate code. Please check your Anthropic API key.")
                            
                            if st.button("Copy LLM Code to File"):
                                new_content = st.session_state.llm_response
                                st.text_area("New File Content:", value=new_content, height=300)
                                if st.button("Update File with LLM Code"):
                                    commit_message = "Update file with LLM-generated code"
                                    update_file(g, selected_repo, selected_file, new_content, commit_message)
                    
                    elif file_action == "Delete File":
                        selected_file = st.selectbox("Select File to Delete:", files)
                        if st.button("Delete File"):
                            if st.checkbox("I understand this action is irreversible"):
                                repo = g.get_user().get_repo(selected_repo)
                                contents = repo.get_contents(selected_file)
                                repo.delete_file(contents.path, f"Delete {selected_file}", contents.sha)
                                st.success(f"File '{selected_file}' deleted successfully.")
                                st.rerun()
                    
                    elif file_action == "Upload File":
                        new_file_name = st.text_input("Enter File Name:")
                        new_file_content = st.text_area("Enter File Content:", height=300)
                        if st.button("Upload File"):
                            repo = g.get_user().get_repo(selected_repo)
                            repo.create_file(new_file_name, f"Create {new_file_name}", new_file_content)
                            st.success(f"File '{new_file_name}' uploaded successfully.")
                            st.rerun()

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
