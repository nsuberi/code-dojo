"""Planning harness for pre-challenge plan creation."""

import os
import uuid
import json
from datetime import datetime
from langsmith import traceable
from config import Config
from models import db
from models.agent_session import AgentSession, AgentMessage
from models.challenge_plan import ChallengePlan
from models.core_learning_goal import CoreLearningGoal
from services.socratic_harness_base import (
    SocraticHarnessBase,
    format_goal_menu,
    parse_topic_selection,
    evaluate_rubric_item
)
from services.socratic_chat import start_conversation, send_message, end_conversation as end_socratic_conversation

# Set up LangSmith environment variables
os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_API_KEY"] = Config.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = Config.LANGCHAIN_PROJECT


class PlanningHarness(SocraticHarnessBase):
    """Guides student to create an implementation plan (pre-challenge)."""

    def __init__(self, learning_goal_id, user_id, langsmith_project=None):
        super().__init__(learning_goal_id, user_id, submission_id=None, langsmith_project=langsmith_project)
        self.plan = None

    @traceable(name="planning_harness_orchestration", metadata={"harness_type": "planning"})
    def start_session(self):
        """Start a new planning session."""
        # Load learning goals
        goals = self.get_core_learning_goals()

        # Create agent session
        self.session = AgentSession(
            id=str(uuid.uuid4()),
            user_id=self.user_id,
            learning_goal_id=self.learning_goal_id,
            harness_type='planning',
            context='pre_coding',
            status='active',
            total_goals=len(goals),
            created_at=datetime.utcnow()
        )
        db.session.add(self.session)

        # Get or create plan
        self.plan = ChallengePlan.query.filter_by(
            user_id=self.user_id,
            learning_goal_id=self.learning_goal_id
        ).first()

        if not self.plan:
            self.plan = ChallengePlan(
                user_id=self.user_id,
                learning_goal_id=self.learning_goal_id,
                plan_content="",
                created_at=datetime.utcnow()
            )
            db.session.add(self.plan)

        db.session.commit()

        # Create welcome message
        welcome = f"""Hello! I'm your Socratic Sensei. Let's build your implementation plan together.

Before you start coding, let's think through the key concepts you'll need to address:

{format_goal_menu(goals)}

**How would you like to approach this?**
1. Tell me your initial thoughts and I'll help you develop them
2. Let me guide you through each concept
3. Jump to a specific topic you want to plan for"""

        # Store the welcome message
        self.store_message('assistant', welcome)

        return {
            'session_id': self.session.id,
            'opening_message': welcome,
            'goals': goals,
            'plan': self.plan.to_dict() if self.plan else None
        }

    @traceable(name="planning_message_process", metadata={"harness_type": "planning"})
    def process_message(self, user_message):
        """Process a user message in the planning session."""
        if not self.session:
            return {'error': 'No active session'}

        # Ensure session is attached to current db.session
        self.ensure_session_attached()

        # Store user message
        self.store_message('user', user_message, input_mode='text')

        # Update plan iterations
        if self.plan:
            self.plan.increment_iterations()

        # Check for topic selection or mode switch
        goals = self.get_core_learning_goals()

        if "guide me" in user_message.lower() or "all of them" in user_message.lower():
            self.session.guide_me_mode = True
            db.session.commit()
            return self._start_guided_planning(goals)

        # Check for specific topic selection
        selected_index = parse_topic_selection(user_message, goals)
        if selected_index is not None:
            return self._focus_on_goal(goals, selected_index, user_message)

        # General planning response
        return self._generate_planning_response(user_message, goals)

    def _start_guided_planning(self, goals):
        """Start guided planning through all goals."""
        if not goals:
            response = "It looks like there are no specific learning goals defined for this challenge yet. Let's start by discussing your overall approach. What's your initial plan?"
        else:
            first_goal = goals[0]
            response = f"""Great! Let's work through the plan systematically.

Let's start with **{first_goal['title']}**: {first_goal['description']}

What's your initial thought on how you'd approach this in your implementation?"""

            self.session.current_goal_index = 0
            db.session.commit()

        self.store_message('assistant', response)

        return {
            'response': response,
            'coverage': self.evaluate_plan_coverage(),
            'current_goal_index': 0
        }

    def _focus_on_goal(self, goals, goal_index, user_message):
        """Focus the conversation on a specific goal."""
        goal = goals[goal_index]

        response = f"""Let's explore **{goal['title']}**.

{goal['description']}

Based on what you said: "{user_message[:100]}..."

What specific approach are you thinking for handling this in your code?"""

        self.session.current_goal_index = goal_index
        db.session.commit()

        self.store_message('assistant', response)

        # Update coverage for this goal
        self._update_coverage_from_discussion(goal['id'], user_message)

        return {
            'response': response,
            'coverage': self.evaluate_plan_coverage(),
            'current_goal_index': goal_index
        }

    def _generate_planning_response(self, user_message, goals):
        """Generate a planning-focused response."""
        from anthropic import Anthropic

        api_key = Config.ANTHROPIC_API_KEY
        if not api_key:
            return {'error': 'AI not configured'}

        # Ensure session is attached to current db.session for lazy loading
        self.ensure_session_attached()

        # Get conversation history
        messages = []
        for msg in self.session.messages.order_by(AgentMessage.created_at).all():
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Build system prompt for planning
        goals_context = "\n".join([f"- {g['title']}: {g['description']}" for g in goals])

        system_prompt = f"""You are the Socratic Sensei helping a student build an implementation plan before they start coding.

## Your Role
- Help them think through their approach
- Ask questions that reveal gaps in their thinking
- Suggest considerations they might have missed
- Build a structured plan from the conversation

## Learning Goals to Cover
{goals_context}

## Guidelines
- Keep responses concise (2-4 sentences)
- Ask one focused question at a time
- Reference specific concepts from the goals
- When they have a solid idea for a concept, acknowledge it and move on
- Help them build a plan artifact they can use while coding

## Current Plan Building
As the conversation progresses, help structure their thoughts into actionable plan items."""

        try:
            client = Anthropic(api_key=api_key)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=system_prompt,
                messages=messages + [{"role": "user", "content": user_message}]
            )

            assistant_response = response.content[0].text
            self.store_message('assistant', assistant_response)

            # Update plan content based on the conversation
            self._update_plan_from_conversation(user_message, assistant_response)

            # Evaluate coverage
            coverage = self.evaluate_plan_coverage()

            return {
                'response': assistant_response,
                'coverage': coverage,
                'plan': self.plan.to_dict() if self.plan else None
            }

        except Exception as e:
            return {'error': f'Error generating response: {str(e)}'}

    def _update_coverage_from_discussion(self, goal_id, user_message):
        """Update coverage based on what was discussed."""
        if not self.plan:
            return

        # Simple check - if they provided a substantive response about the goal
        if len(user_message) > 30:
            self.plan.update_coverage(goal_id, True)
            db.session.commit()

    def _update_plan_from_conversation(self, user_message, assistant_response):
        """Update the plan content based on the conversation."""
        if not self.plan:
            return

        # Append key insights to plan
        current_content = self.plan.plan_content or ""

        # Extract any plan-worthy content
        if len(user_message) > 50:
            current_content += f"\n- {user_message[:200]}"

        self.plan.plan_content = current_content
        db.session.commit()

    @traceable(name="evaluate_plan_coverage", metadata={"harness_type": "planning"})
    def evaluate_plan_coverage(self):
        """Check which learning goals are addressed in the plan."""
        goals = self.get_core_learning_goals()

        coverage = {}
        for goal in goals:
            progress = self.get_or_create_progress(goal['id'])
            # For planning, check if they've discussed this topic
            coverage[str(goal['id'])] = self.plan.get_coverage().get(str(goal['id']), False) if self.plan else False

        return {
            'goals': coverage,
            'covered_count': sum(1 for v in coverage.values() if v),
            'total_count': len(goals)
        }

    def update_plan(self, new_content):
        """Update the plan content directly."""
        if not self.plan:
            return {'error': 'No plan found'}

        self.plan.plan_content = new_content
        self.plan.updated_at = datetime.utcnow()
        db.session.commit()

        return {'success': True, 'plan': self.plan.to_dict()}

    def export_plan(self, challenge_title=None):
        """Export the plan as markdown."""
        if not self.plan:
            return {'error': 'No plan found'}

        self.plan.mark_exported()
        db.session.commit()

        from models.goal import LearningGoal
        if not challenge_title:
            learning_goal = LearningGoal.query.get(self.learning_goal_id)
            challenge_title = learning_goal.title if learning_goal else "Challenge"

        return {
            'success': True,
            'markdown': self.plan.export_markdown(challenge_title),
            'plan': self.plan.to_dict()
        }

    def generate_plan_from_conversation(self):
        """Extract a structured plan from the dialogue."""
        if not self.session:
            return {'error': 'No active session'}

        from anthropic import Anthropic

        api_key = Config.ANTHROPIC_API_KEY
        if not api_key:
            return {'error': 'AI not configured'}

        # Ensure session is attached to current db.session for lazy loading
        self.ensure_session_attached()

        # Get conversation history
        messages = self.session.messages.order_by(AgentMessage.created_at).all()
        conversation_text = "\n".join([f"{m.role}: {m.content}" for m in messages])

        goals = self.get_core_learning_goals()
        goals_text = "\n".join([f"- {g['title']}: {g['description']}" for g in goals])

        prompt = f"""Based on this planning conversation, create a structured implementation plan.

## Learning Goals
{goals_text}

## Conversation
{conversation_text[:6000]}

Create a markdown plan with:
1. ## Understanding - Key concepts identified
2. ## Approach - Step-by-step implementation plan
3. ## Key Considerations - Technical considerations discussed
4. ## Questions to Explore - Open questions to investigate while coding

Keep it concise and actionable."""

        try:
            client = Anthropic(api_key=api_key)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            plan_content = response.content[0].text

            if self.plan:
                self.plan.plan_content = plan_content
                self.plan.updated_at = datetime.utcnow()
                db.session.commit()

            return {
                'success': True,
                'plan_content': plan_content,
                'plan': self.plan.to_dict() if self.plan else None
            }

        except Exception as e:
            return {'error': f'Error generating plan: {str(e)}'}

    def end_session(self):
        """End the planning session."""
        if not self.session:
            return {'error': 'No active session'}

        self.session.status = 'completed'
        self.session.completed_at = datetime.utcnow()
        db.session.commit()

        return {
            'success': True,
            'plan': self.plan.to_dict() if self.plan else None,
            'coverage': self.evaluate_plan_coverage()
        }
