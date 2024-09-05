import streamlit as st
from streamlit_ace import st_ace
from code_editor import code_editor
from github import Github, GithubException
import base64
import os
from cryptography.fernet import Fernet
import anthropic
import time
from openai import OpenAI

st.set_page_config(page_title="GitHub Repository Manager", layout="wide")

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
@st.fragment
def list_repos(g):
    user = g.get_user()
    repos = user.get_repos()
    return [""] + [repo.name for repo in repos]

@st.fragment
def list_files(g, repo_name):
    if not repo_name:
        return []
    repo = g.get_user().get_repo(repo_name)
    contents = repo.get_contents("")
    files = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            files.append(file_content.path)
    return files

@st.fragment
def get_file_content(g, repo_name, file_path):
    repo = g.get_user().get_repo(repo_name)
    content = repo.get_contents(file_path)
    return base64.b64decode(content.content).decode()

@st.fragment
def update_file(g, repo_name, file_path, content, commit_message):
    try:
        repo = g.get_user().get_repo(repo_name)
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, commit_message, content, contents.sha)
        st.success(f"File '{file_path}' updated successfully.")
        return True
    except Exception as e:
        st.error(f"Error updating file '{file_path}': {str(e)}")
        return False

@st.fragment
def create_repo(g, repo_name):
    try:
        user = g.get_user()
        user.create_repo(repo_name)
        st.success(f"Repository '{repo_name}' created successfully.")
    except Exception as e:
        st.error(f"Error creating repository: {str(e)}")

@st.fragment
def delete_repo(g, repo_name):
    try:
        repo = g.get_user().get_repo(repo_name)
        repo.delete()
        st.success(f"Repository '{repo_name}' deleted successfully.")
    except Exception as e:
        st.error(f"Error deleting repository: {str(e)}")

@st.dialog("Create/Delete Repositories")
def repo_management_dialog():
    repo_action = st.radio("Choose an action:", ["Create Repository", "Delete Repository"])
    repo_name = st.text_input("Repository Name:")

    if st.button("Submit"):
        g = st.session_state.g
        if repo_action == "Create Repository":
            create_repo(g, repo_name)
        elif repo_action == "Delete Repository":
            delete_repo(g, repo_name)

@st.fragment
def create_file(g, repo_name, file_path, content, commit_message):
    try:
        repo = g.get_user().get_repo(repo_name)
        repo.create_file(file_path, commit_message, content)
        st.success(f"File '{file_path}' created successfully in '{repo_name}'.")
    except Exception as e:
        st.error(f"Error creating file: {str(e)}")

@st.fragment
def delete_file(g, repo_name, file_path, commit_message):
    try:
        repo = g.get_user().get_repo(repo_name)
        contents = repo.get_contents(file_path)
        repo.delete_file(contents.path, commit_message, contents.sha)
        st.success(f"File '{file_path}' deleted successfully from '{repo_name}'.")
    except Exception as e:
        st.error(f"Error deleting file: {str(e)}")

@st.dialog("Create/Delete Files in Repo")
def file_management_dialog():
    repos = list_repos(st.session_state.g)
    selected_repo = st.selectbox("Choose a repository:", repos)
    
    file_action = st.radio("Choose an action:", ["Create File", "Delete File"])
    file_path = st.text_input("File Path:")
    content = st.text_area("File Content:", height=150)
    commit_message = st.text_input("Commit Message:", key="file_manage_commit")
    
    if st.button("Submit"):
        g = st.session_state.g
        if file_action == "Create File":
            create_file(g, selected_repo, file_path, content, commit_message)
        elif file_action == "Delete File":
            delete_file(g, selected_repo, file_path, commit_message)

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

# LLM code generation
@st.fragment
def generate_code_with_llm(prompt, app_code):
    selected_llm = st.session_state.get('selected_llm', 'Sonnet-3.5')
    system_prompt="You are an expert Python programmer. Respond only with clean Python code that addresses the user's request, do not add (!) any of your explanations, do not add (!) any quote characters. You may comment the code using commenting markup. By default output full code unless specified by the user prompt."
    if selected_llm == 'Sonnet-3.5':
        anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]

        if not anthropic_api_key:
            st.error("Anthropic API key not found in secrets.")
            return None

        client = anthropic.Anthropic(api_key=anthropic_api_key)
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=8192,
            temperature=0,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt+" "+app_code
                        }
                    ]
                }
            ]
        )
        return message.content[0].text
    elif selected_llm == 'GPT-4o':
        openai_api_key = st.secrets["OPENAI_API_KEY"]

        if not openai_api_key:
            st.error("OpenAI API key not found in secrets.")
            return None

        client = OpenAI(api_key=openai_api_key)
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt + " " + app_code}
            ]
        )
        return completion.choices[0].message.content

@st.dialog("Choose file from a repo")
def file_selector_dialog():
    repos = list_repos(st.session_state.g)
    selected_repo = st.selectbox("Choose a repository:", repos)
    
    files = []
    if selected_repo:
        files = list_files(st.session_state.g, selected_repo)
    
    selected_file = st.selectbox("Select File to Edit:", files)
    
    if st.button("Load File Content"):
        if selected_repo and selected_file:
            content = get_file_content(st.session_state.g, selected_repo, selected_file)
            st.session_state.file_content = content
            st.session_state.selected_repo = selected_repo
            st.session_state.selected_file = selected_file
            st.rerun()

def code_editor_and_prompt():
    if 'file_content' not in st.session_state:
        st.session_state.file_content = ""
    
    with st.popover("Enter prompt", use_container_width=False):
        col1, col2 = st.columns([4, 2])
        with col1:
            prompt = st.text_area(label="", label_visibility="collapsed", placeholder="Enter your prompt for code generation and click.", 
            height=100)
        with col2:
            if st.button("Execute prompt"):
                with st.spinner("Executing your prompt..."):
                    generated_code = generate_code_with_llm(prompt, st.session_state.file_content)
                    if generated_code:
                        st.session_state.file_content = generated_code
                        st.rerun()
                    else:
                        st.error("Failed to generate code. Please check your API key.")    
    
    #content = st_ace(
    #        value=st.session_state.file_content,
    #        language="python",
    #        theme="dreamweaver",
    #        keybinding="vscode",
    #        font_size=12,
    #        tab_size=4,
    #        show_gutter=True,
    #        show_print_margin=False,
    #        wrap=False,
    #        auto_update=True,
    #        readonly=False,
    #        min_lines=30,
    #        key="ace_editor",)
    custom_btns =[
 {
   "name": "Copy",
   "feather": "Copy",
   "alwaysOn": True,
   "commands": ["copyAll", ["infoMessage", 
                    {
                     "text":"Copied to clipboard!",
                     "timeout": 2500, 
                     "classToggle": "show"
                    }
                   ]],
   "style": {"top": "0.46rem", "right": "0.4rem"}
 },
 {
   "name": "Shortcuts",
   "feather": "Type",
   "class": "shortcuts-button",
   "hasText": True,
   "commands": ["toggleKeyboardShortcuts"],
   "style": {"bottom": "calc(50% + 1.75rem)", "right": "0.4rem"}
 },
 {
   "name": "Save",
   "feather": "Save",
   "hasText": True,
   "commands": ["save-state", ["response","saved"]],
   "response": "saved",
   "style": {"bottom": "calc(50% - 4.25rem)", "right": "0.4rem"}
 },
 {
   "name": "Run",
   "feather": "Play",
   "primary": True,
   "hasText": True,
   "showWithIcon": True,
   "commands": ["submit"],
   "style": {"bottom": "0.44rem", "right": "0.4rem"}
 },
 {
   "name": "Command",
   "feather": "Terminal",
   "primary": True,
   "hasText": True,
   "commands": ["openCommandPallete"],
   "style": {"bottom": "3.5rem", "right": "0.4rem"}
 }
]
    # style dict for Ace Editor
    ace_style = {"borderRadius": "0px 0px 8px 8px"}

    # style dict for Code Editor
    code_style = {"width": "100%"}
    css_string = '''
        background-color: #bee1e5;
        body > #root .ace-streamlit-dark~& {background-color: #262830;}
        .ace-streamlit-dark~& span {color: #fff;opacity: 0.6;  }
        span {color: #000; opacity: 0.5;}
       .code_editor-info.message {width: inherit;margin-right: 75px;order: 2;text-align: center;opacity: 0;transition: opacity 0.7s ease-out;}
    .code_editor-info.message.show {opacity: 0.6;}
    .ace-streamlit-dark~& .code_editor-info.message.show {opacity: 0.5;} 
    '''
    info_bar = {
      "name": "language info",
      "css": css_string,
      "style": {
            "order": "1",
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "center",
            "width": "100%",
            "height": "2.0rem",
            "padding": "0rem 0.6rem",
            "padding-bottom": "0.2rem",
            "borderRadius": "8px 8px 0px 0px",
            "zIndex": "9993"
           },
      "info": [{"name": "python", "style": {"width": "100px"}}] }

    response_dict = code_editor(st.session_state.file_content,  buttons=custom_btns, options={"wrap": True}, 
    theme="contrast", height=[30, 50], focus=False, info=info_bar, props={"style": ace_style}, 
    component_props={"style": code_style})
    
    #st.write("Text:"+st.session_state.file_content)
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    #st.write(f'conten=st_ace... line triggered. {current_time}')
    if len(response_dict['id']) != 0:
        #st.write("THIS IS THE TRIGGER:"+ response_dict['type']+ "/n "+ response_dict['text'])
        if response_dict['type'] == "submit":
          execute_code_sandbox()
        elif response_dict['type'] == "selection":
            # Handle selection type
            pass
        elif response_dict['type'] == "saved":
            st.session_state.file_content=response_dict['text']
            dialog_update()    

@st.dialog("Confirm repo file update")
def dialog_update():
    st.write(f"**Confirm updating {st.session_state.selected_file}**")
    commit_message = st.text_input("Commit Message:", key='commit_message_txt') 
    save_button = st.button(f"Save Changes to {st.session_state.get('selected_file', 'No file selected')}")
    if save_button:
        if all(key in st.session_state for key in ['g', 'selected_repo', 'selected_file', 'file_content']):
            st.write("***Attempting to update the file...***")
            try:
                repo = st.session_state.g.get_user().get_repo(st.session_state.selected_repo)
                contents = repo.get_contents(st.session_state.selected_file)
                repo.update_file(contents.path, commit_message, st.session_state.file_content, contents.sha)
                st.success(f"File '{st.session_state.selected_file}' updated successfully. This message will self-destruct in 5 seconds...")
                time.sleep(5)
                st.rerun()
            except Exception as e:
                st.error(f"Error updating file: {str(e)}")
        else:
            st.error("Missing required information to save changes. This message will self-destruct in 5 seconds...")
            time.sleep(5)
            st.rerun()

@st.fragment
def save_changes():
    commit_message = st.text_input("Commit Message:", key='commit_message_txt') 
    save_button = st.button(f"Save Changes to {st.session_state.get('selected_file', 'No file selected')}")
    
    if save_button:
        dialog_update(commit_message)

@st.fragment
def execute_code_sandbox():
    exec_button = st.button("Execute code")
    if exec_button:
        # Write st.session_state.file_content to a code_output.py file which is saved in a Github repo
        try:
            repo = st.session_state.g.get_user().get_repo(st.session_state.selected_repo)
            file_path = 'pages/code_output.py'
            content = st.session_state.file_content
            commit_message = 'Update code_output.py'
            
            try:
                # Try to get the file contents (if it exists)
                contents = repo.get_contents(file_path)
                repo.update_file(file_path, commit_message, content, contents.sha)
            except GithubException as e:
                if e.status == 404:  # File not found
                    # If the file doesn't exist, create it
                    repo.create_file(file_path, commit_message, content)
                else:
                    raise  # Re-raise the exception if it's not a 404 error
            #st.page_link("Click to view the output of the file", "code_output.py")
            st.success(f"Code output saved to {file_path} in the repository.")
        except Exception as e:
            st.error(f"Error saving code output: {str(e)}")
 
    
#def main():
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    g = github_auth()
    if g:
        st.session_state.g = g
        st.session_state.authenticated = True
        st.rerun()

if st.session_state.authenticated:
    try:
        st.sidebar.title("GitHub Repository Manager")
        
        with st.sidebar:
            st.session_state.selected_llm = st.selectbox("Choose LLM:", ["Sonnet-3.5", "GPT-4o"])
            
            st.divider()
            if st.button("Choose file from a repo"):
                file_selector_dialog()
            
            st.divider()
            
            if st.button("Create/Delete Repositories"):
                repo_management_dialog()
            
            st.divider()

            if st.button("Create/Delete Files in Repo"):
                file_management_dialog()
            
            st.divider()
            
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.github_token = ''
                if 'g' in st.session_state:
                    del st.session_state.g
                st.rerun()
        
        if 'selected_file' in st.session_state:
            st.write(f"***Current repository/file***: {st.session_state.selected_repo} / {st.session_state.selected_file}")
            code_editor_and_prompt()
            #save_changes()
            execute_code_sandbox()

    except GithubException as e:
        st.error(f"An error occurred: {str(e)}")
        st.session_state.authenticated = False
        if 'g' in st.session_state:
            del st.session_state.g
        st.rerun()

#if __name__ == "__main__":
#    main()

# CSS to style the app
st.markdown("""
<style>
    .stApp {
        background-color: #f0f0f0;
        color: #333333;
    }
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
    }
    .stTextArea > div > div > textarea {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
    }
    .stSelectbox > div > div > select {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #e0e0e0;
    }
    .stLabel {
        color: #2196F3;
        font-weight: bold;
    }
    .stHeader {
        color: #1976D2;
    }
    .stAce {
        border: 1px solid #2196F3;
    }
    .streamlit-expanderHeader {
        background-color: #e0e0e0;
        color: #333333;
    }
    .stAlert {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
    }
</style>
""", unsafe_allow_html=True)
