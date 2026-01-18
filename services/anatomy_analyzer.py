"""Anatomy analyzer service for combining admin topics with AI-detected patterns."""

import json
from anthropic import Anthropic
from config import Config
from models.anatomy_topic import AnatomyTopic


def get_anatomy_menu(goal, submission_diff):
    """
    Build the anatomy menu by combining admin-configured topics
    with AI-detected patterns from the student's code diff.

    Args:
        goal: The LearningGoal object
        submission_diff: The git diff showing student's code changes

    Returns:
        List of anatomy elements (dicts with id, name, description, source)
    """
    # Get admin-configured topics
    admin_topics = AnatomyTopic.query.filter_by(goal_id=goal.id).order_by(AnatomyTopic.order).all()

    menu_items = []

    # Add admin topics first
    for topic in admin_topics:
        menu_items.append({
            'id': f'topic_{topic.id}',
            'topic_id': topic.id,
            'name': topic.name,
            'description': topic.description or '',
            'analogies': topic.suggested_analogies or '',
            'source': 'admin',
        })

    # Use AI to detect additional patterns from the diff
    ai_detected = detect_code_patterns(goal, submission_diff, [t.name for t in admin_topics])

    for pattern in ai_detected:
        menu_items.append({
            'id': f'detected_{pattern["name"].lower().replace(" ", "_")}',
            'topic_id': None,
            'name': pattern['name'],
            'description': pattern['description'],
            'analogies': pattern.get('suggested_analogy', ''),
            'source': 'ai_detected',
        })

    return menu_items


def detect_code_patterns(goal, diff_content, existing_topics):
    """
    Use Claude to analyze the code diff and identify discussable patterns
    that aren't already covered by admin topics.

    Args:
        goal: The LearningGoal object
        diff_content: The git diff
        existing_topics: List of already-configured topic names to avoid duplicates

    Returns:
        List of detected patterns (dicts with name, description, suggested_analogy)
    """
    api_key = Config.ANTHROPIC_API_KEY

    if not api_key or not diff_content:
        return []

    try:
        client = Anthropic(api_key=api_key)

        existing_list = ', '.join(existing_topics) if existing_topics else 'none'

        prompt = f"""Analyze this code submission and identify 2-4 interesting code patterns or concepts
that would be valuable for a student to discuss and understand deeply.

## Challenge Context
{goal.challenge_md or goal.title}

## Student's Code Changes
```diff
{diff_content[:8000]}
```

## Already Configured Topics (avoid these)
{existing_list}

Identify patterns NOT in the already configured list. Focus on:
- Specific coding patterns used (decorators, context managers, error handling)
- Architectural decisions (routing, data flow, separation of concerns)
- Security or performance considerations visible in the code
- Interesting language features or library usage

Return JSON array with 2-4 patterns. Each pattern should have:
- name: Short descriptive name (2-4 words)
- description: One sentence explaining what this pattern does in their code
- suggested_analogy: A real-world analogy to help explain this concept

Example response format:
[
  {{
    "name": "Error Handling Pattern",
    "description": "The code uses try-except blocks to gracefully handle database connection failures",
    "suggested_analogy": "Like a safety net catching trapeze artists - the program doesn't crash when something goes wrong"
  }}
]

Return ONLY the JSON array, no other text."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON from response
        # Handle potential markdown code blocks
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])

        patterns = json.loads(response_text)

        # Validate and filter
        valid_patterns = []
        for p in patterns:
            if isinstance(p, dict) and 'name' in p and 'description' in p:
                # Skip if too similar to existing topics
                name_lower = p['name'].lower()
                if not any(existing.lower() in name_lower or name_lower in existing.lower()
                          for existing in existing_topics):
                    valid_patterns.append({
                        'name': p['name'],
                        'description': p['description'],
                        'suggested_analogy': p.get('suggested_analogy', ''),
                    })

        return valid_patterns[:4]  # Limit to 4 max

    except Exception as e:
        print(f"Error detecting code patterns: {e}")
        return []
