import streamlit as st
from github import Github, GithubException
import base64
from os import environ
import importlib
import re

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
    
    import_pattern = re.compile(r'^import\s+(.+)$')
    from_import_pattern = re.compile(r'^from\s+(\S+)\s+import\s+(.+)$')
    
    for line in code_content.split('\n'):
        stripped_line = line.strip()
        if stripped_line.startswith('import '):
            match = import_pattern.match(stripped_line)
            if match:
                modules = match.group(1).split(',')
                for module in modules:
                    module = module.strip()
                    if ' as ' in module:
                        original, alias = module.split(' as ')
                        import_lines.append(f"{alias.strip()} = custom_import('{original.strip()}')")
                    else:
                        import_lines.append(f"{module} = custom_import('{module}')")
        elif stripped_line.startswith('from '):
            match = from_import_pattern.match(stripped_line)
            if match:
                module, attributes = match.groups()
                attrs = [attr.strip() for attr in attributes.split(',')]
                for attr in attrs:
                    if ' as ' in attr:
                        original, alias = attr.split(' as ')
                        import_lines.append(f"{alias.strip()} = custom_import('{module}').{original.strip()}")
                    else:
                        import_lines.append(f"{attr} = custom_import('{module}').{attr}")
        else:
            other_lines.append(line)
    
    return '\n'.join(import_lines + other_lines)

def execute_sandbox_code():
    github_token = environ.get("HUBGIT_TOKEN")
    g = Github(github_token)
    try:
        repo = g.get_user().get_repo("streamcoder")
        file_path = 'pages/sandbox.txt'
        code_content = get_file_content(repo, file_path)
        if code_content is not None:
            preprocessed_code = preprocess_code(code_content)
            
            st.text_area("Preprocessed Code", preprocessed_code, height=300)
            
            global_env = {
                "__builtins__": __builtins__,
                "st": st,
                "custom_import": custom_import
            }
            try:
                exec(preprocessed_code, global_env)
                st.success("Code executed successfully!")
            except Exception as e:
                st.error(f"Error executing code: {str(e)}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    execute_sandbox_code()
