# auth.py

from github import Github, GithubException
import streamlit as st
import logging
from os import environ

def github_auth() -> Github:
    """
    Authenticates the user with GitHub using the provided token.

    Returns:
        Github: Authenticated GitHub client.
    """
    github_token = environ.get("HUBGIT_TOKEN") or st.secrets["HUBGIT_TOKEN"]
    if github_token:
        try:
            g = Github(github_token)
            user = g.get_user()
            st.session_state.github_token = github_token
            st.session_state.authenticated = True
            logging.info(f"Authenticated as {user.login}")
            return g
        except GithubException as e:
            logging.error(f"GitHub Authentication Failed: {e.status} - {e.data}")
            st.error(
                "Authentication failed. Please check your GitHub token in secrets.",
                icon=':material/sentiment_dissatisfied:'
            )
    else:
        st.error("GitHub token not found in secrets.", icon=':material/sentiment_dissatisfied:')
    return None
