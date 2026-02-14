"""
services/ai_service.py - Anthropic / AI Business Logic

WHY SEPARATE FROM THE ROUTER?
  The router's job is HTTP: receive a request, call a service, return a response.
  The AI service's job is: build a prompt, call Anthropic, return the answer.

  Keeping them separate means:
  - You can swap Claude for OpenAI by editing ONE file, not hunting through routes.
  - You can unit-test prompt_builder() without making real API calls.
  - If Anthropic adds streaming or tool use, you add it here — routers don't change.

PROMPT ENGINEERING NOTE:
  We send a system-style instruction in the user message (Claude's API doesn't
  require a separate system turn). The data context is truncated to stay within
  token limits — describe() + head(10) + tail(5) gives Claude enough signal
  without sending thousands of rows.
"""

import anthropic
import pandas as pd

from core.config import Settings


def build_data_context(df: pd.DataFrame) -> str:
    """
    Produce a compact text summary of a DataFrame for use in a prompt.

    WHY NOT SEND ALL THE DATA?
      LLMs have context limits, and sending 10,000 rows is wasteful.
      Descriptive stats + a sample of rows gives the model enough signal
      to answer most analytical questions accurately.
    """
    return (
        f"Dataset Overview:\n"
        f"- Rows: {len(df)}, Columns: {len(df.columns)}\n"
        f"- Columns: {', '.join(df.columns.tolist())}\n\n"
        f"Summary Statistics:\n{df.describe().to_string()}\n\n"
        f"First 10 rows:\n{df.head(10).to_string()}\n\n"
        f"Last 5 rows:\n{df.tail(5).to_string()}\n"
    )


def ask_claude(question: str, df: pd.DataFrame, settings: Settings) -> str:
    """
    Send a natural-language question + data context to Claude and return the answer.

    Parameters
    ----------
    question : str
        The user's question, e.g. "What was the best performing month?"
    df : pd.DataFrame
        The current dataset to analyse.
    settings : Settings
        Injected settings — contains api_key, model name, max_tokens.

    Returns
    -------
    str
        Claude's response text.

    Raises
    ------
    anthropic.AuthenticationError
        Re-raised so the router can map it to HTTP 401.
    Exception
        Any other Anthropic error is re-raised for the router to handle.

    WHY PASS settings AS A PARAMETER?
      Dependency injection. In tests you pass a Settings object with a fake key
      (and mock the Anthropic client). The function itself stays pure and
      testable without network calls.
    """
    data_context = build_data_context(df)

    prompt = (
        "You are a data analytics assistant for a sales & marketing analytics "
        "platform called InsightsAI.\n"
        "You have access to the following dataset:\n\n"
        f"{data_context}\n\n"
        "Answer this question about the data concisely and insightfully. "
        "Include specific numbers when relevant. "
        "If the data doesn't contain enough information to answer, say so.\n\n"
        f"Question: {question}"
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.ai_model,
        max_tokens=settings.ai_max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
