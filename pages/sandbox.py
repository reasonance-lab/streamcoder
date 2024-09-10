import streamlit as st
from github import Github, GithubException
import base64
from os import environ

def get_file_content(repo, file_path):
    try:
        content = repo.get_contents(file_path)
        return base64.b64decode(content.content).decode()
    except GithubException as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def execute_sandbox_code():
    #st.title("Sandbox Code Execution")

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
            # Display the code content
            #st.subheader("Code Content:")
            #st.code(code_content, language='python')

            # Remove 'import streamlit' line
            code_lines = code_content.split('\n')
            code_lines = [line for line in code_lines if not line.strip().startswith('import streamlit')]
            cleaned_code = '\n'.join(code_lines)
            try:
                # Execute the code
                exec(cleaned_code)
                st.success("Code executed successfully!")
            except Exception as e:
                st.error(f"Error executing code: {str(e)}")
            # # Execute the code
            # if st.button("Execute Code"):
            #     st.subheader("Execution Output:")

    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    execute_sandbox_code()

# if not "sandbox_code" in st.session_state:
#     st.write("No code found to execute. Click 'Save to Sandbox' in the bottom right corner to pass your code to sandbox.")
# else:
#     exec(st.session_state.sandbox_code)
