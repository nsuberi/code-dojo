"""Socratic chat service for anatomy discussions using Claude."""

import os
import re
import uuid
from datetime import datetime
from anthropic import Anthropic
from langsmith import traceable
from config import Config
from models import db
from models.anatomy_topic import AnatomyTopic
from models.anatomy_conversation import AnatomyConversation, ConversationMessage, StudentRealization

# Set up LangSmith environment variables
os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_API_KEY"] = Config.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = Config.LANGCHAIN_PROJECT


def format_pass_indicators(indicators):
    """Format pass indicators as a bulleted list."""
    return "\n".join(f"- {indicator}" for indicator in indicators)


def get_socratic_system_prompt(topic_name, topic_description, analogies, diff_content, challenge_context, rubric_context=None):
    """Build the system prompt for Socratic dialogue.

    Args:
        topic_name: Name of the topic being discussed
        topic_description: Description of the topic
        analogies: Suggested analogies for teaching
        diff_content: The student's code diff
        challenge_context: Context from the challenge
        rubric_context: Optional dict with:
            - criterion: The learning criterion to explore
            - pass_indicators: What demonstrates understanding
            - current_hint_index: Which Socratic hint to emphasize (0-2)
            - hints: List of progressive Socratic questions
    """
    analogy_section = ""
    if analogies:
        analogy_section = f"""
## Suggested Analogies
Use these analogies when helpful:
{analogies}
"""

    # Add rubric section if provided
    rubric_section = ""
    if rubric_context:
        current_hint = rubric_context['hints'][rubric_context['current_hint_index']] if rubric_context.get('hints') else ""
        rubric_section = f"""

## Focused Learning Objective
Your goal in this conversation is to guide the student to understand:
**{rubric_context['criterion']}**

They demonstrate understanding when they can:
{format_pass_indicators(rubric_context['pass_indicators'])}

Start with or build upon this Socratic question:
{current_hint}

If they struggle, build up progressively from simpler concepts.
"""

    return f"""You are the Digi Trainer, a wise and patient coding teacher who guides students to understand their own code through thoughtful questions rather than direct explanations.

## Your Teaching Method
1. **Never give direct answers** - Guide through questions that lead to discovery
2. **Use analogies** - Connect coding concepts to real-world situations
3. **Keep responses concise** - 2-3 sentences typically, make it conversational
4. **Celebrate realizations** - When a student demonstrates understanding, acknowledge it warmly
5. **Build progressively** - Start with what they know and build understanding step by step

## Current Discussion Topic
**{topic_name}**
{topic_description or ''}
{analogy_section}
{rubric_section}

## The Student's Code Context
The student is discussing code they wrote for this challenge:
{challenge_context or 'A coding challenge'}

Here is the relevant code they wrote:
```diff
{diff_content[:4000] if diff_content else 'No code diff available'}
```

## Tracking Understanding
When the student demonstrates a clear understanding or has an "aha moment", append this tag at the end of your response:
[REALIZATION: brief description of what they understood]

For example:
"Yes! That's exactly right - the decorator checks if you're logged in before letting you access the protected page."
[REALIZATION: Student understood that login_required decorator acts as an authentication gatekeeper]

## Conversation Guidelines
- Start by asking what they think this code element does
- If they're confused, zoom out to simpler concepts first
- Reference their actual code when possible
- Don't overwhelm - one concept at a time
- Use encouraging but honest language
- If they ask a direct question, answer with a guiding question back

Begin the conversation by warmly greeting the student and asking an opening question about the topic that invites them to share what they already understand."""


@traceable(name="socratic_chat_start", metadata={"feature": "socratic_sensei"})
def start_conversation(submission, topic_id=None, topic_name=None, topic_description=None, analogies=None, diff_content=None, rubric_context=None):
    """
    Start a new Socratic conversation about an anatomy topic.

    Args:
        submission: The Submission object
        topic_id: ID of admin-configured topic (optional)
        topic_name: Name of the topic (required if no topic_id)
        topic_description: Description of the topic
        analogies: Suggested analogies for teaching
        diff_content: The student's code diff
        rubric_context: Optional rubric context for agent-driven sessions

    Returns:
        Tuple of (conversation, opening_message)
    """
    api_key = Config.ANTHROPIC_API_KEY

    if not api_key:
        return None, "AI chat is not available. Please configure the ANTHROPIC_API_KEY."

    # If topic_id provided, get topic details
    topic = None
    if topic_id:
        topic = AnatomyTopic.query.get(topic_id)
        if topic:
            topic_name = topic.name
            topic_description = topic.description
            analogies = topic.suggested_analogies

    if not topic_name:
        return None, "No topic specified for conversation."

    # Create conversation record
    conversation = AnatomyConversation(
        id=str(uuid.uuid4()),
        submission_id=submission.id,
        topic_id=topic_id,
        topic_name=topic_name,
        status='active',
        created_at=datetime.utcnow()
    )
    db.session.add(conversation)

    # Get challenge context
    challenge_context = submission.goal.challenge_md or submission.goal.title

    # Build system prompt with optional rubric context
    system_prompt = get_socratic_system_prompt(
        topic_name, topic_description, analogies, diff_content, challenge_context, rubric_context
    )

    try:
        client = Anthropic(api_key=api_key)

        # Get opening message from Claude
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": "Hello! I'd like to understand this code better."}
            ]
        )

        assistant_response = message.content[0].text

        # Parse and store any realizations
        cleaned_response, realizations = parse_realizations(assistant_response, topic_name)

        # Store the initial exchange
        user_msg = ConversationMessage(
            conversation_id=conversation.id,
            role='user',
            content="Hello! I'd like to understand this code better.",
            created_at=datetime.utcnow()
        )
        assistant_msg = ConversationMessage(
            conversation_id=conversation.id,
            role='assistant',
            content=cleaned_response,
            created_at=datetime.utcnow()
        )
        db.session.add(user_msg)
        db.session.add(assistant_msg)

        # Store realizations
        for realization in realizations:
            r = StudentRealization(
                conversation_id=conversation.id,
                topic=topic_name,
                description=realization,
                detected_at=datetime.utcnow()
            )
            db.session.add(r)

        db.session.commit()

        return conversation, cleaned_response

    except Exception as e:
        db.session.rollback()
        return None, f"Error starting conversation: {str(e)}"


@traceable(name="socratic_chat_message", metadata={"feature": "socratic_sensei"})
def send_message(conversation_id, user_message, diff_content=None, rubric_context=None):
    """
    Send a message in an existing conversation and get Claude's response.

    Args:
        conversation_id: The conversation UUID
        user_message: The user's message
        diff_content: The student's code diff (for context)
        rubric_context: Optional rubric context for progressive hints

    Returns:
        Tuple of (success, response_text_or_error)
    """
    api_key = Config.ANTHROPIC_API_KEY

    if not api_key:
        return False, "AI chat is not available."

    conversation = AnatomyConversation.query.get(conversation_id)
    if not conversation:
        return False, "Conversation not found."

    if conversation.status != 'active':
        return False, "This conversation has ended."

    # Get topic details
    topic_name = conversation.topic_name
    topic_description = ''
    analogies = ''

    if conversation.topic:
        topic_description = conversation.topic.description or ''
        analogies = conversation.topic.suggested_analogies or ''

    # Get challenge context
    challenge_context = conversation.submission.goal.challenge_md or conversation.submission.goal.title

    # Build system prompt with optional rubric context
    system_prompt = get_socratic_system_prompt(
        topic_name, topic_description, analogies, diff_content, challenge_context, rubric_context
    )

    # Build message history
    messages = []
    for msg in conversation.messages.order_by(ConversationMessage.created_at).all():
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Add new user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    try:
        client = Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )

        assistant_response = response.content[0].text

        # Parse realizations
        cleaned_response, realizations = parse_realizations(assistant_response, topic_name)

        # Store messages
        user_msg = ConversationMessage(
            conversation_id=conversation_id,
            role='user',
            content=user_message,
            created_at=datetime.utcnow()
        )
        assistant_msg = ConversationMessage(
            conversation_id=conversation_id,
            role='assistant',
            content=cleaned_response,
            created_at=datetime.utcnow()
        )
        db.session.add(user_msg)
        db.session.add(assistant_msg)

        # Store realizations
        for realization in realizations:
            r = StudentRealization(
                conversation_id=conversation_id,
                topic=topic_name,
                description=realization,
                detected_at=datetime.utcnow()
            )
            db.session.add(r)

        db.session.commit()

        return True, cleaned_response

    except Exception as e:
        db.session.rollback()
        return False, f"Error sending message: {str(e)}"


@traceable(name="socratic_chat_end", metadata={"feature": "socratic_sensei"})
def end_conversation(conversation_id):
    """
    End a conversation and generate a synthesis of what was learned.

    Args:
        conversation_id: The conversation UUID

    Returns:
        Tuple of (success, synthesis_markdown_or_error)
    """
    api_key = Config.ANTHROPIC_API_KEY

    conversation = AnatomyConversation.query.get(conversation_id)
    if not conversation:
        return False, "Conversation not found."

    if conversation.status == 'ended':
        return True, conversation.synthesis_markdown

    # Get all messages and realizations
    messages = conversation.messages.order_by(ConversationMessage.created_at).all()
    realizations = conversation.realizations.all()

    # Build conversation transcript
    transcript = "\n".join([
        f"**{msg.role.title()}**: {msg.content}"
        for msg in messages
    ])

    # Build realizations list
    realizations_text = "\n".join([
        f"- {r.description}"
        for r in realizations
    ]) if realizations else "No specific realizations detected."

    if not api_key:
        # Generate basic synthesis without AI
        synthesis = f"""## Learning Summary: {conversation.topic_name}

### Conversation Overview
This was a Socratic dialogue exploring **{conversation.topic_name}**.

### Key Realizations
{realizations_text}

### Next Steps
Continue exploring related concepts and applying what you've learned to new code!
"""
        conversation.synthesis_markdown = synthesis
        conversation.status = 'ended'
        conversation.ended_at = datetime.utcnow()
        db.session.commit()
        return True, synthesis

    try:
        client = Anthropic(api_key=api_key)

        prompt = f"""Synthesize this Socratic dialogue into a brief learning summary.

## Topic
{conversation.topic_name}

## Conversation Transcript
{transcript[:6000]}

## Detected Realizations
{realizations_text}

Create a warm, encouraging markdown summary that:
1. Acknowledges what the student explored
2. Highlights key insights and realizations
3. Suggests what to explore next

Keep it concise (150-250 words). Use a friendly, supportive tone.
Format with markdown headers and bullet points."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        synthesis = response.content[0].text

        conversation.synthesis_markdown = synthesis
        conversation.status = 'ended'
        conversation.ended_at = datetime.utcnow()
        db.session.commit()

        return True, synthesis

    except Exception as e:
        db.session.rollback()
        return False, f"Error generating synthesis: {str(e)}"


def parse_realizations(response_text, topic_name):
    """
    Parse [REALIZATION: ...] tags from Claude's response.

    Args:
        response_text: The raw response from Claude
        topic_name: The current topic name

    Returns:
        Tuple of (cleaned_response, list_of_realizations)
    """
    pattern = r'\[REALIZATION:\s*(.+?)\]'
    realizations = re.findall(pattern, response_text, re.IGNORECASE)

    # Remove realization tags from response
    cleaned = re.sub(pattern, '', response_text, flags=re.IGNORECASE).strip()

    return cleaned, realizations


def get_conversation_history(conversation_id):
    """
    Get the full conversation history.

    Args:
        conversation_id: The conversation UUID

    Returns:
        Dict with conversation details, messages, and realizations
    """
    conversation = AnatomyConversation.query.get(conversation_id)
    if not conversation:
        return None

    return conversation.to_dict(include_messages=True, include_realizations=True)
