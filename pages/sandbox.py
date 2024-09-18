import streamlit as st
from github import Github, GithubException
import base64
from os import environ
#sandbox file: read and exec a code
def get_file_content(repo, file_path):
    try:
        content = repo.get_contents(file_path)
        return base64.b64decode(content.content).decode()
    except GithubException as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def execute_sandbox_code():
    # Authenticate with GitHub
    github_token = environ.get("HUBGIT_TOKEN")
    g = Github(github_token)

    try:
        # Get the repository
        repo = g.get_user().get_repo("streamcoder")
        
        # Read the content of the sandbox.txt file
        file_path = 'pages/sandbox.txt'
        code_content = get_file_content(repo, file_path)

        if code_content is not None:
            # Define a restricted execution environment
            local_env = {}
            try:
                # Execute the code within a restricted local environment
                exec(code_content, {}, local_env)
                st.success("Code executed successfully!")
            except Exception as e:
                st.error(f"Error executing code: {str(e)}")

    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    execute_sandbox_code()