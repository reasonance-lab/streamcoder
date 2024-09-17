# llm_utils.py
import streamlit as st
import logging
from typing import Optional
import anthropic
from openai import OpenAI
from os import environ

def generate_code_with_llm(prompt: str, app_code: str) -> Optional[str]:
    """
    Generates code using the selected LLM based on the provided prompt and application code.

    Args:
        prompt (str): User's prompt for code generation.
        app_code (str): Existing application code.

    Returns:
        Optional[str]: Generated code if successful, else None.
    """
    selected_llm = st.session_state.get('selected_llm', 'Sonnet-3.5')
    system_prompt = (
        "You are an expert Python programmer. Respond only with clean Python code that "
        "addresses the user's request, do not add (!) any of your explanations, do not add (!) "
        "any quote characters. You may comment the code using commenting markup ONLY! "
        "By default, output full code unless specified by the user prompt."
    )
    full_prompt = f"{prompt} {app_code}"

    if selected_llm == 'Sonnet-3.5':
        return generate_with_anthropic(system_prompt, full_prompt)
    elif selected_llm == 'GPT-4o':
        return generate_with_openai(system_prompt, full_prompt)
    else:
        st.error("Selected LLM is not supported.", icon=':material/sentiment_dissatisfied:')
        return None

def generate_with_anthropic(system_prompt: str, user_prompt: str) -> Optional[str]:
    """
    Generates code using the Anthropic LLM.

    Args:
        system_prompt (str): System-level instructions for the LLM.
        user_prompt (str): User's prompt.

    Returns:
        Optional[str]: Generated code if successful, else None.
    """
    anthropic_api_key = environ("ANTHROPIC_API_KEY", "")
    if not anthropic_api_key: 
        st.error("Anthropic API key not found in secrets.", icon=':material/sentiment_dissatisfied:')
        return None

    client = anthropic.Anthropic(api_key=anthropic_api_key)
    try:
        # Note: The Anthropic library may have different methods; adjust accordingly
        client = anthropic.Anthropic(api_key=anthropic_api_key)
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=8192,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}])
        return message.content[0].text
    except Exception as e:
        logging.exception(f"Anthropic API error: {e}")
        st.error(f"Anthropic API error: {str(e)}", icon=':material/sentiment_dissatisfied:')
        return None

def generate_with_openai(system_prompt: str, user_prompt: str) -> Optional[str]:
    """
    Generates code using the OpenAI LLM.

    Args:
        system_prompt (str): System-level instructions for the LLM.
        user_prompt (str): User's prompt.

    Returns:
        Optional[str]: Generated code if successful, else None.
    """
    openai_api_key =environ("OPENAI_API_KEY", "")
    if not openai_api_key:
        st.error("OpenAI API key not found in secrets.", icon=':material/sentiment_dissatisfied:')
        return None

    client = OpenAI(api_key=openai_api_key)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logging.exception(f"OpenAI API error: {e}")
        st.error(f"OpenAI API error: {str(e)}", icon=':material/sentiment_dissatisfied:')
        return None
