# github_ops.py

from github import Github, GithubException
import streamlit as st
import base64
import logging
from typing import List, Optional

def get_repo(g: Github, repo_name: str):
    """
    Retrieves a repository object by name.

    Args:
        g (Github): Authenticated GitHub client.
        repo_name (str): Name of the repository.

    Returns:
        Repository object if found, else None.
    """
    try:
        return g.get_user().get_repo(repo_name)
    except GithubException as e:
        st.error(
            f"Error accessing repository '{repo_name}': {e.data.get('message', str(e))}",
            icon=':material/sentiment_dissatisfied:'
        )
        logging.error(f"GitHub Exception while accessing repo '{repo_name}': {e}")
    return None

def encode_content(content: str) -> str:
    """
    Encodes content to base64.

    Args:
        content (str): Content to encode.

    Returns:
        str: Base64 encoded content.
    """
    return base64.b64encode(content.encode()).decode()

def decode_content(encoded_content: str) -> str:
    """
    Decodes base64 encoded content.

    Args:
        encoded_content (str): Base64 encoded content.

    Returns:
        str: Decoded content.
    """
    return base64.b64decode(encoded_content).decode()

def list_repos(g: Github) -> List[str]:
    """
    Fetches and returns a list of repository names for the authenticated user.

    Args:
        g (Github): Authenticated GitHub client.

    Returns:
        List[str]: List of repository names.
    """
    try:
        user = g.get_user()
        repos = user.get_repos()
        return [""] + [repo.name for repo in repos]
    except GithubException as e:
        logging.error(f"Error listing repositories: {e}")
        st.error(f"Error listing repositories: {e.data.get('message', str(e))}", icon=':material/sentiment_dissatisfied:')
        return []

def list_files(g: Github, repo_name: str) -> List[str]:
    """
    Lists all files in the specified repository.

    Args:
        g (Github): Authenticated GitHub client.
        repo_name (str): Name of the repository.

    Returns:
        List[str]: List of file paths.
    """
    if not repo_name:
        return []
    repo = get_repo(g, repo_name)
    if not repo:
        return []
    try:
        contents = repo.get_contents("")
        files = []
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                files.append(file_content.path)
        return files
    except GithubException as e:
        logging.error(f"Error listing files in repo '{repo_name}': {e}")
        st.error(f"Error listing files in repository '{repo_name}': {e.data.get('message', str(e))}", icon=':material/sentiment_dissatisfied:')
        return []

def get_file_content(g: Github, repo_name: str, file_path: str) -> Optional[str]:
    """
    Retrieves the content of a specific file in a repository.

    Args:
        g (Github): Authenticated GitHub client.
        repo_name (str): Name of the repository.
        file_path (str): Path to the file.

    Returns:
        Optional[str]: Content of the file if successful, else None.
    """
    repo = get_repo(g, repo_name)
    if not repo:
        return None
    try:
        content = repo.get_contents(file_path)
        return decode_content(content.content)
    except GithubException as e:
        logging.error(f"Error fetching file '{file_path}' from repo '{repo_name}': {e}")
        st.error(f"Error fetching file '{file_path}': {e.data.get('message', str(e))}", icon=':material/sentiment_dissatisfied:')
    return None

def update_file(g: Github, repo_name: str, file_path: str, content: str, commit_message: str) -> bool:
    """
    Updates an existing file in the repository.

    Args:
        g (Github): Authenticated GitHub client.
        repo_name (str): Name of the repository.
        file_path (str): Path to the file.
        content (str): New content for the file.
        commit_message (str): Commit message.

    Returns:
        bool: True if update was successful, else False.
    """
    repo = get_repo(g, repo_name)
    if not repo:
        return False
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, commit_message, content, contents.sha)
        st.success(f"File '{file_path}' updated successfully.", icon=':material/sentiment_satisfied:')
        logging.info(f"File '{file_path}' in repo '{repo_name}' updated successfully.")
        return True
    except GithubException as e:
        logging.error(f"GitHub Exception while updating file '{file_path}': {e}")
        st.error(f"Error updating file '{file_path}': {e.data.get('message', str(e))}", icon=':material/sentiment_dissatisfied:')
    except Exception as e:
        logging.exception(f"Unexpected error while updating file '{file_path}': {e}")
        st.error(f"Unexpected error: {str(e)}", icon=':material/sentiment_dissatisfied:')
    return False

def create_repo(g: Github, repo_name: str) -> None:
    """
    Creates a new repository under the authenticated user's account.

    Args:
        g (Github): Authenticated GitHub client.
        repo_name (str): Name of the repository to create.
    """
    try:
        user = g.get_user()
        user.create_repo(repo_name)
        st.success(f"Repository '{repo_name}' created successfully.", icon=':material/sentiment_satisfied:')
        logging.info(f"Repository '{repo_name}' created successfully.")
    except GithubException as e:
        logging.error(f"GitHub Exception while creating repo '{repo_name}': {e}")
        st.error(f"Error creating repository: {e.data.get('message', str(e))}", icon=':material/sentiment_dissatisfied:')
    except Exception as e:
        logging.exception(f"Unexpected error while creating repo '{repo_name}': {e}")
        st.error(f"Unexpected error: {str(e)}", icon=':material/sentiment_dissatisfied:')

def delete_repo(g: Github, repo_name: str) -> None:
    """
    Deletes an existing repository under the authenticated user's account.

    Args:
        g (Github): Authenticated GitHub client.
        repo_name (str): Name of the repository to delete.
    """
    repo = get_repo(g, repo_name)
    if not repo:
        return
    try:
        repo.delete()
        st.success(f"Repository '{repo_name}' deleted successfully.", icon=':material/sentiment_satisfied:')
        logging.info(f"Repository '{repo_name}' deleted successfully.")
    except GithubException as e:
        logging.error(f"GitHub Exception while deleting repo '{repo_name}': {e}")
        st.error(f"Error deleting repository: {e.data.get('message', str(e))}", icon=':material/sentiment_dissatisfied:')
    except Exception as e:
        logging.exception(f"Unexpected error while deleting repo '{repo_name}': {e}")
        st.error(f"Unexpected error: {str(e)}", icon=':material/sentiment_dissatisfied:')

def create_file(g: Github, repo_name: str, file_path: str, content: str, commit_message: str) -> None:
    """
    Creates a new file in the specified repository.

    Args:
        g (Github): Authenticated GitHub client.
        repo_name (str): Name of the repository.
        file_path (str): Path where the file will be created.
        content (str): Content of the file.
        commit_message (str): Commit message.
    """
    repo = get_repo(g, repo_name)
    if not repo:
        return
    try:
        repo.create_file(file_path, commit_message, content)
        st.success(f"File '{file_path}' created successfully in '{repo_name}'.", icon=':material/sentiment_satisfied:')
        logging.info(f"File '{file_path}' created in repo '{repo_name}'.")
    except GithubException as e:
        logging.error(f"GitHub Exception while creating file '{file_path}' in repo '{repo_name}': {e}")
        st.error(f"Error creating file: {e.data.get('message', str(e))}", icon=':material/sentiment_dissatisfied:')
    except Exception as e:
        logging.exception(f"Unexpected error while creating file '{file_path}' in repo '{repo_name}': {e}")
        st.error(f"Unexpected error: {str(e)}", icon=':material/sentiment_dissatisfied:')

def delete_file(g: Github, repo_name: str, file_path: str, commit_message: str) -> None:
    """
    Deletes a file from the specified repository.

    Args:
        g (Github): Authenticated GitHub client.
        repo_name (str): Name of the repository.
        file_path (str): Path to the file to delete.
        commit_message (str): Commit message.
    """
    repo = get_repo(g, repo_name)
    if not repo:
        return
    try:
        contents = repo.get_contents(file_path)
        repo.delete_file(contents.path, commit_message, contents.sha)
        st.success(f"File '{file_path}' deleted successfully from '{repo_name}'.", icon=':material/sentiment_satisfied:')
        logging.info(f"File '{file_path}' deleted from repo '{repo_name}'.")
    except GithubException as e:
        logging.error(f"GitHub Exception while deleting file '{file_path}' from repo '{repo_name}': {e}")
        st.error(f"Error deleting file: {e.data.get('message', str(e))}", icon=':material/sentiment_dissatisfied:')
    except Exception as e:
        logging.exception(f"Unexpected error while deleting file '{file_path}' from repo '{repo_name}': {e}")
        st.error(f"Unexpected error: {str(e)}", icon=':material/sentiment_dissatisfied:')
