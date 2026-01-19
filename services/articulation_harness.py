"""Articulation harness for post-challenge verbal explanation."""

import os
import uuid
import json
from datetime import datetime
from langsmith import traceable
from config import Config
from models import db
from models.agent_session import AgentSession, AgentMessage
from models.submission import Submission
from models.core_learning_goal import CoreLearningGoal
from models.goal_progress import GoalProgress
from services.socratic_harness_base import (
    SocraticHarnessBase,
    format_goal_menu,
    parse_topic_selection,
    evaluate_rubric_item,
    get_remaining_goals
)
from services.socratic_chat import start_conversation, send_message, end_conversation as end_socratic_conversation
from services.whisper_transcription import transcribe_audio

# Set up LangSmith environment variables
os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_API_KEY"] = Config.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = Config.LANGCHAIN_PROJECT


class ArticulationHarness(SocraticHarnessBase):
    """Evaluates student's verbal articulation of concepts (post-challenge)."""

    def __init__(self, submission_id, user_id, langsmith_project=None):
        self.submission = Submission.query.get(submission_id)
        if not self.submission:
            raise ValueError(f"Submission {submission_id} not found")

        super().__init__(
            self.submission.goal_id,
            user_id,
            submission_id=submission_id,
            langsmith_project=langsmith_project
        )
        self.diff_content = None

    def set_diff_content(self, diff_content):
        """Set the code diff content for reference."""
        self.diff_content = diff_content

    @traceable(name="articulation_harness_orchestration", metadata={"harness_type": "articulation"})
    def start_session(self):
        """Start a new articulation session."""
        # Load learning goals
        goals = self.get_core_learning_goals()

        # Create agent session
        self.session = AgentSession(
            id=str(uuid.uuid4()),
            user_id=self.user_id,
            learning_goal_id=self.learning_goal_id,
            submission_id=self.submission_id,
            harness_type='articulation',
            context='post_submission',
            status='active',
            total_goals=len(goals),
            created_at=datetime.utcnow()
        )
        db.session.add(self.session)
        db.session.commit()

        # Calculate current engagement
        engagement = self.calculate_engagement_stats()

        # Create welcome message
        welcome = f"""Hello! I'm your Socratic Sensei. Let's talk through what you built.

Explaining your code verbally is essential for code reviews and technical interviews. This is practice for those moments.

**Concepts to explain** (💎 = {engagement['passed']} mastered, need {max(0, (len(goals) // 2) - engagement['valid_count'])} more for instructor feedback):

{self._format_goals_with_gems(goals)}

**How would you like to proceed?**
1. Choose a concept to explain
2. Let me suggest where to start
3. Guide me through all of them

🎤 *Voice input is recommended for practice, but you can also type.*"""

        # Store the welcome message
        self.store_message('assistant', welcome)

        return {
            'session_id': self.session.id,
            'opening_message': welcome,
            'goals': goals,
            'engagement': engagement,
            'can_request_instructor': engagement['can_request_instructor']
        }

    def _format_goals_with_gems(self, goals):
        """Format goals with gem status indicators."""
        lines = []
        for i, goal in enumerate(goals, 1):
            progress = GoalProgress.query.filter_by(
                user_id=self.user_id,
                core_goal_id=goal['id']
            ).first()

            if progress:
                if progress.is_expired():
                    gem = "⟳"  # Expired - needs renewal
                elif progress.status == 'passed':
                    gem = "💎"
                elif progress.status == 'engaged':
                    gem = "🔵"
                elif progress.status == 'in_progress':
                    gem = "⚪"
                else:
                    gem = "○"
            else:
                gem = "○"

            lines.append(f"{i}. {gem} **{goal['title']}**")

        return "\n".join(lines)

    @traceable(name="articulation_message_process", metadata={"harness_type": "articulation"})
    def process_message(self, user_message, input_mode='text', voice_duration=None, original_transcription=None):
        """Process a user message in the articulation session."""
        if not self.session:
            return {'error': 'No active session'}

        # Store user message
        self.store_message(
            'user',
            user_message,
            input_mode=input_mode,
            voice_duration=voice_duration,
            metadata={'original_transcription': original_transcription} if original_transcription else None
        )

        goals = self.get_core_learning_goals()

        # Check for topic selection or mode switch
        if "guide me" in user_message.lower() or "all of them" in user_message.lower():
            self.session.guide_me_mode = True
            db.session.commit()
            return self._start_guided_articulation(goals)

        if "suggest" in user_message.lower():
            next_index = self.recommend_next_goal()
            if next_index is not None:
                return self._focus_on_goal(goals, next_index, introduce=True)
            else:
                return self._all_goals_completed()

        # Check for specific topic selection
        selected_index = parse_topic_selection(user_message, goals)
        if selected_index is not None:
            return self._focus_on_goal(goals, selected_index, introduce=True)

        # If we have a current goal, evaluate the response
        if self.session.current_goal_index is not None:
            return self._evaluate_articulation(user_message, goals)

        # General response
        return self._generate_articulation_response(user_message, goals)

    @traceable(name="articulation_voice_process", metadata={"harness_type": "articulation", "input_mode": "voice"})
    def process_voice_input(self, audio_data, input_mode='voice'):
        """Process voice input for articulation."""
        # Transcribe the audio
        result = transcribe_audio(
            audio_data,
            user_id=self.user_id,
            session_id=self.session.id if self.session else None
        )

        if not result['success']:
            return {'error': result['error']}

        # Process the transcription as a message
        return self.process_message(
            result['transcription'],
            input_mode='voice',
            voice_duration=result.get('duration_seconds'),
            original_transcription=result['transcription']
        )

    def _start_guided_articulation(self, goals):
        """Start guided articulation through all goals."""
        next_index = self.recommend_next_goal()

        if next_index is None:
            return self._all_goals_completed()

        return self._focus_on_goal(goals, next_index, introduce=True)

    def _focus_on_goal(self, goals, goal_index, introduce=False):
        """Focus the conversation on explaining a specific goal."""
        goal = goals[goal_index]

        self.session.current_goal_index = goal_index
        self.session.current_rubric_item_index = 0
        self.session.current_attempts = 0
        db.session.commit()

        # Mark as in progress
        self.update_gem_state(goal['id'], 'in_progress')

        # Get the first rubric item
        rubric_items = goal.get('rubric', {}).get('items', [])
        if rubric_items:
            first_item = rubric_items[0]
            first_hint = first_item['socratic_hints'][0] if first_item.get('socratic_hints') else ""

            response = f"""Let's explore **{goal['title']}**.

Walk me through how you approached this in your code. {first_hint}

*Take your time to explain - this is practice for real technical discussions.*"""
        else:
            response = f"""Let's explore **{goal['title']}**.

Walk me through how you implemented this in your code. How would you explain it to a colleague?"""

        self.store_message('assistant', response)

        return {
            'response': response,
            'current_goal': goal,
            'engagement': self.calculate_engagement_stats()
        }

    def _evaluate_articulation(self, user_message, goals):
        """Evaluate the student's articulation against rubric."""
        current_goal = goals[self.session.current_goal_index]
        rubric_items = current_goal.get('rubric', {}).get('items', [])

        if not rubric_items:
            # No rubric items - just acknowledge and move on
            return self._goal_completed(current_goal, goals, 'engaged')

        current_item_index = self.session.current_rubric_item_index
        if current_item_index >= len(rubric_items):
            return self._goal_completed(current_goal, goals, 'passed')

        current_item = rubric_items[current_item_index]

        # Increment attempts
        self.session.current_attempts += 1
        db.session.commit()

        # Evaluate the response
        passed, evaluation = evaluate_rubric_item(user_message, current_item)

        # Update progress
        progress = self.get_or_create_progress(current_goal['id'])
        if passed:
            progress.mark_item_passed(current_item['id'], user_message, evaluation)
        else:
            progress.increment_attempts()

        db.session.commit()

        if passed:
            # Move to next rubric item
            self.session.current_rubric_item_index += 1
            self.session.current_attempts = 0
            db.session.commit()

            if self.session.current_rubric_item_index >= len(rubric_items):
                return self._goal_completed(current_goal, goals, 'passed')
            else:
                next_item = rubric_items[self.session.current_rubric_item_index]
                return self._probe_next_item(current_goal, next_item)

        elif self.session.current_attempts >= 3:
            # Max attempts reached - mark as engaged and move on
            progress.mark_item_engaged(current_item['id'], user_message, evaluation)
            db.session.commit()

            self.session.current_rubric_item_index += 1
            self.session.current_attempts = 0
            db.session.commit()

            if self.session.current_rubric_item_index >= len(rubric_items):
                return self._goal_completed(current_goal, goals, 'engaged')
            else:
                next_item = rubric_items[self.session.current_rubric_item_index]
                return self._acknowledge_and_continue(current_goal, next_item)

        else:
            # Give another hint
            hint_index = min(self.session.current_attempts, len(current_item.get('socratic_hints', [])) - 1)
            return self._provide_hint(current_goal, current_item, hint_index)

    def _probe_next_item(self, goal, rubric_item):
        """Probe the student on the next rubric item."""
        hints = rubric_item.get('socratic_hints', [])
        hint = hints[0] if hints else ""

        response = f"""That's a great explanation!

Now let's dig a bit deeper. {hint}"""

        self.store_message('assistant', response)

        return {
            'response': response,
            'current_goal': goal,
            'rubric_item': rubric_item,
            'engagement': self.calculate_engagement_stats()
        }

    def _provide_hint(self, goal, rubric_item, hint_index):
        """Provide a progressive hint for the current rubric item."""
        hints = rubric_item.get('socratic_hints', [])
        hint = hints[hint_index] if hint_index < len(hints) else hints[-1] if hints else ""

        response = f"""Let me help you think through this a bit more.

{hint}

Try to connect this to what you actually implemented in your code."""

        self.store_message('assistant', response)

        return {
            'response': response,
            'current_goal': goal,
            'rubric_item': rubric_item,
            'attempts_remaining': 3 - self.session.current_attempts,
            'engagement': self.calculate_engagement_stats()
        }

    def _acknowledge_and_continue(self, goal, next_item):
        """Acknowledge effort and continue to next item."""
        hints = next_item.get('socratic_hints', [])
        hint = hints[0] if hints else ""

        response = f"""Good thinking on that! Let's explore another aspect.

{hint}"""

        self.store_message('assistant', response)

        return {
            'response': response,
            'current_goal': goal,
            'rubric_item': next_item,
            'engagement': self.calculate_engagement_stats()
        }

    def _goal_completed(self, completed_goal, all_goals, status):
        """Handle completion of a goal."""
        # Update gem state
        self.update_gem_state(completed_goal['id'], status)

        # Update session stats
        if status == 'passed':
            self.session.goals_passed = (self.session.goals_passed or 0) + 1
        else:
            self.session.goals_engaged = (self.session.goals_engaged or 0) + 1
        db.session.commit()

        engagement = self.calculate_engagement_stats()

        if status == 'passed':
            gem_message = "💎 You've demonstrated mastery of this concept!"
        else:
            gem_message = "🔵 Great engagement with this concept!"

        # Check if we should offer instructor unlock
        if engagement['can_request_instructor'] and not self.session.guide_me_mode:
            unlock_message = "\n\n✨ **You've unlocked instructor feedback!** You can now request a review when you're ready."
        else:
            unlock_message = ""

        if self.session.guide_me_mode:
            # Move to next goal
            next_index = self.recommend_next_goal()
            if next_index is not None:
                self.session.current_goal_index = next_index
                self.session.current_rubric_item_index = 0
                self.session.current_attempts = 0
                db.session.commit()

                next_goal = all_goals[next_index]
                rubric_items = next_goal.get('rubric', {}).get('items', [])
                first_hint = ""
                if rubric_items:
                    first_hint = rubric_items[0].get('socratic_hints', [''])[0]

                response = f"""{gem_message}{unlock_message}

Excellent work on **{completed_goal['title']}**!

Let's move on to **{next_goal['title']}**. {first_hint}"""

                self.store_message('assistant', response)

                return {
                    'response': response,
                    'current_goal': next_goal,
                    'engagement': engagement,
                    'gem_unlocked': True,
                    'gem_status': status
                }
            else:
                return self._all_goals_completed()

        else:
            # Offer choice
            remaining = [g for i, g in enumerate(all_goals) if i != self.session.current_goal_index]

            response = f"""{gem_message}{unlock_message}

Excellent work on **{completed_goal['title']}**!

Would you like to:
1. Explore another concept: {self._format_goals_with_gems(remaining)[:200]}
2. Request instructor feedback (if unlocked)
3. End this session"""

            self.store_message('assistant', response)

            self.session.current_goal_index = None
            db.session.commit()

            return {
                'response': response,
                'engagement': engagement,
                'gem_unlocked': True,
                'gem_status': status
            }

    def _all_goals_completed(self):
        """Handle when all goals have been completed."""
        engagement = self.calculate_engagement_stats()

        response = f"""🎉 **Amazing work!**

You've explored all the key concepts for this challenge:
- 💎 {engagement['passed']} concepts mastered
- 🔵 {engagement['engaged']} concepts engaged with

This is exactly the kind of practice that makes technical interviews and code reviews feel natural.

{"✨ **Instructor feedback is now available!** Click below to request a review." if engagement['can_request_instructor'] else ""}

What would you like to do next?"""

        self.store_message('assistant', response)

        return {
            'response': response,
            'engagement': engagement,
            'all_complete': True
        }

    def _generate_articulation_response(self, user_message, goals):
        """Generate a general articulation response."""
        from anthropic import Anthropic

        api_key = Config.ANTHROPIC_API_KEY
        if not api_key:
            return {'error': 'AI not configured'}

        # Get conversation history
        messages = []
        for msg in self.session.messages.order_by(AgentMessage.created_at).all():
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Build system prompt
        goals_context = "\n".join([f"- {g['title']}: {g['description']}" for g in goals])

        system_prompt = f"""You are the Socratic Sensei helping a student articulate their understanding of code they've written.

## Your Role
- Guide them to explain their implementation clearly
- Ask questions that help them articulate their reasoning
- Prepare them for code reviews and technical interviews

## Learning Goals
{goals_context}

## Guidelines
- Keep responses concise (2-4 sentences)
- Encourage verbal explanation practice
- Reference their actual code when possible
- Help them build confidence in technical communication"""

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

            return {
                'response': assistant_response,
                'engagement': self.calculate_engagement_stats()
            }

        except Exception as e:
            return {'error': f'Error generating response: {str(e)}'}

    def end_session(self):
        """End the articulation session."""
        if not self.session:
            return {'error': 'No active session'}

        self.session.status = 'completed'
        self.session.completed_at = datetime.utcnow()
        db.session.commit()

        engagement = self.calculate_engagement_stats()

        return {
            'success': True,
            'engagement': engagement,
            'can_request_instructor': engagement['can_request_instructor']
        }
