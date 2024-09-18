import streamlit as st
from github import Github, GithubException
import base64
from os import environ
import importlib

def custom_import(module_name):
    return importlib.import_module(module_name)

def get_file_content(repo, file_path):
    try:
        content = repo.get_contents(file_path)
        return base64.b64decode(content.content).decode()
    except GithubException as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def preprocess_code(code_content):
    import_lines = []
    other_lines = []
    for line in code_content.split('\n'):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            module = line.split()[1].split('.')[0]
            import_lines.append(f"{module} = custom_import('{module}')")
        else:
            other_lines.append(line)
    return '\n'.join(import_lines + other_lines)

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
            # Preprocess the code
            preprocessed_code = preprocess_code(code_content)
            
            # Define a partially restricted global execution environment
            global_env = {
                "__builtins__": __builtins__,
                "st": st,
                "custom_import": custom_import
            }
            local_env = {}
            try:
                # Execute the preprocessed code within a partially restricted global environment
                exec(preprocessed_code, global_env, local_env)
                st.success("Code executed successfully!")
            except Exception as e:
                st.error(f"Error executing code: {str(e)}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    execute_sandbox_code()