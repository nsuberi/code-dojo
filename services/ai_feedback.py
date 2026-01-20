"""AI feedback generation using Claude API."""

import os
from anthropic import Anthropic
from config import Config


def generate_ai_feedback(challenge_description, diff_content, challenge_rubric=None, submission_id=None,
                        pr_metadata=None, pr_files=None):
    """
    Generate AI feedback for a code submission using Claude.

    Uses agentic review when a challenge rubric is available for multi-approach
    evaluation with structured feedback. Enhanced with architectural analysis
    via LangGraph orchestration when PR data is available.

    Args:
        challenge_description: The challenge/task description in markdown
        diff_content: The code diff showing student's changes
        challenge_rubric: Optional ChallengeRubric object for agentic review
        submission_id: Optional submission ID for tracing
        pr_metadata: Optional PR metadata dict from GitHub API
        pr_files: Optional list of PR file dicts from GitHub API

    Returns:
        If challenge_rubric provided: dict with content, detected_approach, evaluation, etc.
        Otherwise: String containing the AI feedback
    """
    # Use orchestrated review when rubric is available (Section 4)
    if challenge_rubric:
        from services.review_orchestrator import orchestrate_review
        return orchestrate_review(
            submission_id=submission_id,
            challenge_md=challenge_description,
            diff_content=diff_content,
            rubric=challenge_rubric.get_rubric(),
            pr_metadata=pr_metadata,
            pr_files=pr_files
        )

    # Fallback to simple 4-point feedback for challenges without rubrics
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
