"""AI feedback generation using Claude API."""

import os
from anthropic import Anthropic
from config import Config


def generate_ai_feedback(challenge_description, diff_content):
    """
    Generate AI feedback for a code submission using Claude.

    Args:
        challenge_description: The challenge/task description in markdown
        diff_content: The code diff showing student's changes

    Returns:
        String containing the AI feedback
    """
    api_key = Config.ANTHROPIC_API_KEY

    if not api_key:
        return """**AI Feedback (Demo Mode)**

No Anthropic API key configured. In production, this would provide:
1. **Correctness Analysis** - Does the code solve the challenge?
2. **Code Quality Review** - Is it well-structured and maintainable?
3. **Security Assessment** - Any vulnerabilities introduced?

To enable AI feedback, set the ANTHROPIC_API_KEY environment variable."""

    try:
        client = Anthropic(api_key=api_key)

        prompt = f"""Review this code submission for the following challenge:

## Challenge Description
{challenge_description}

## Student's Code Changes
{diff_content}

Please provide constructive feedback on:

1. **Correctness** - Does the code solve the challenge requirements?
2. **Code Quality** - Is it well-structured, readable, and maintainable?
3. **Security** - Are there any security concerns with the implementation?
4. **Suggestions** - What could be improved?

Be encouraging but honest. Point out both strengths and areas for improvement."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        return f"""**AI Feedback Error**

Could not generate AI feedback: {str(e)}

Please check your API key configuration and try again."""
