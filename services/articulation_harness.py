"""Articulation harness for post-challenge verbal explanation."""

import os
import uuid
import json
from datetime import datetime
from langsmith import traceable, trace
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
        self._thread_id = None  # Thread ID for grouping traces in LangSmith
        self._parent_trace_headers = None  # Store trace headers for parent-child linking
        self._topic_thread_id = None  # Thread ID for current topic conversation
        self._topic_trace_headers = None  # Store trace headers for topic-level linking

    def set_diff_content(self, diff_content):
        """Set the code diff content for reference."""
        self.diff_content = diff_content

    def _get_langsmith_extra(self):
        """Get LangSmith extra config with parent headers for proper trace linking.

        This ensures all child traces include parent headers so they
        are properly nested in LangSmith's trace view.
        """
        if not self._thread_id:
            return None

        extra = {
            "metadata": {
                "session_id": self._thread_id,
                "harness_type": "articulation"
            }
        }

        # Include parent headers so child traces link properly
        if self._topic_trace_headers:
            extra["parent"] = self._topic_trace_headers
        elif self._parent_trace_headers:
            extra["parent"] = self._parent_trace_headers

        return extra

    def start_session(self, focus_goal_id=None):
        """Start a new articulation session.

        Args:
            focus_goal_id: If provided, immediately focus on this specific core goal
        """
        # Load learning goals
        goals = self.get_core_learning_goals()

        # Generate thread ID for grouping all traces in this session
        # Use a deterministic UUID based on session creation to ensure consistency
        self._thread_id = str(uuid.uuid4())

        # Create parent trace, capture headers, then IMMEDIATELY close it
        # This prevents the parent from staying "running" forever if user navigates away
        with trace(
            name="articulation_harness_orchestration",
            inputs={
                "submission_id": self.submission_id,
                "user_id": self.user_id,
                "learning_goal_id": self.learning_goal_id,
                "focus_goal_id": focus_goal_id
            },
            metadata={
                "session_id": self._thread_id,  # Required for LangSmith thread grouping
                "harness_type": "articulation",
                "user_id": self.user_id,
                "submission_id": self.submission_id,
                "learning_goal_id": self.learning_goal_id
            },
            run_id=uuid.UUID(self._thread_id)  # Use thread_id as run_id for consistency
        ) as run_tree:
            self._parent_trace_headers = run_tree.to_headers()
        # Parent trace ends here (no longer "running" forever)

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
            langsmith_run_id=self._thread_id,  # Store the thread ID for querying
            langsmith_trace_headers=json.dumps(dict(self._parent_trace_headers)),  # Store headers for reconstruction
            created_at=datetime.utcnow()
        )
        db.session.add(self.session)
        db.session.commit()

        # If focus_goal_id provided, immediately focus on that specific goal
        if focus_goal_id:
            # Convert to int - frontend sends string from dataset attribute
            try:
                focus_goal_id = int(focus_goal_id)
            except (TypeError, ValueError):
                pass  # Keep as-is if conversion fails
            for i, goal in enumerate(goals):
                if goal['id'] == focus_goal_id:
                    result = self._focus_on_goal(goals, i, introduce=True)
                    # Add fields expected by frontend
                    result['session_id'] = self.session.id
                    result['opening_message'] = result.get('response')
                    result['goals'] = goals
                    result['can_request_instructor'] = result['engagement']['can_request_instructor']
                    return result

        # Calculate current engagement
        engagement = self.calculate_engagement_stats()

        # Create welcome message
        welcome = f"""Hello! I'm your Digi Trainer. Let's talk through what you built.

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

    def _close_topic_trace(self, goal=None, status=None):
        """Clear the current topic trace headers.

        Args:
            goal: The goal that was being discussed (optional, for logging)
            status: The outcome status - 'passed', 'engaged', or 'frustrated' (optional, for logging)
        """
        # Clear topic headers (traces are already completed since we use with-blocks)
        self._topic_trace_headers = None
        self._topic_thread_id = None

        # Also clear from session if it exists
        if self.session:
            self.session.current_topic_thread_id = None
            self.session.current_topic_trace_headers = None
            db.session.commit()

    def process_message(self, user_message, input_mode='text', voice_duration=None, original_transcription=None):
        """Process a user message in the articulation session."""
        if not self.session:
            return {'error': 'No active session'}

        # Store user message first
        self.store_message(
            'user',
            user_message,
            input_mode=input_mode,
            voice_duration=voice_duration,
            metadata={'original_transcription': original_transcription} if original_transcription else None
        )

        # Check for frustration before normal processing (only if actively on a topic)
        messages = [m.content for m in self.session.messages.all()]
        is_frustrated = self.session.current_goal_index is not None and self.detect_frustration(messages)

        # Use trace() with parent headers for proper nesting in LangSmith
        with trace(
            name="articulation_message_process",
            inputs={
                "user_message": user_message,
                "input_mode": input_mode,
                "voice_duration": voice_duration
            },
            metadata={
                "topic_thread_id": self._topic_thread_id,  # Link to current topic thread
                "session_id": self._thread_id,  # Required for LangSmith thread grouping
                "harness_type": "articulation",
                "input_mode": input_mode,
                "frustration_detected": is_frustrated  # Track frustration in traces
            },
            parent=self._topic_trace_headers or self._parent_trace_headers  # Link to parent for nesting
        ) as message_run_tree:
            goals = self.get_core_learning_goals()
            result = None

            # Handle frustration immediately - end topic and offer to move on
            if is_frustrated:
                result = self._handle_frustration_and_end_topic(user_message, goals)

            # Check for topic selection or mode switch
            elif "guide me" in user_message.lower() or "all of them" in user_message.lower():
                self.session.guide_me_mode = True
                db.session.commit()
                result = self._start_guided_articulation(goals)

            elif "suggest" in user_message.lower():
                next_index = self.recommend_next_goal()
                if next_index is not None:
                    result = self._focus_on_goal(goals, next_index, introduce=True)
                else:
                    result = self._all_goals_completed()

            # Check for specific topic selection
            elif (selected_index := parse_topic_selection(user_message, goals)) is not None:
                result = self._focus_on_goal(goals, selected_index, introduce=True)

            # If we have a current goal, evaluate the response
            elif self.session.current_goal_index is not None:
                result = self._evaluate_articulation(user_message, goals)

            # General response
            else:
                result = self._generate_articulation_response(user_message, goals)

            # Set outputs for LangSmith visibility
            if result:
                message_run_tree.outputs = {
                    "response": result.get("response"),
                    "engagement": result.get("engagement")
                }
            return result

    def process_voice_input(self, audio_data, input_mode='voice'):
        """Process voice input for articulation."""
        # Use trace() with parent headers for proper nesting in LangSmith
        with trace(
            name="articulation_voice_process",
            inputs={
                "audio_data_size": len(audio_data) if audio_data else 0,
                "session_id": self.session.id if self.session else None
            },
            metadata={
                "topic_thread_id": self._topic_thread_id,  # Link to current topic thread
                "session_id": self._thread_id,  # Required for LangSmith thread grouping
                "harness_type": "articulation",
                "input_mode": "voice"
            },
            parent=self._topic_trace_headers or self._parent_trace_headers  # Link to parent for nesting
        ) as voice_run_tree:
            # Transcribe the audio
            result = transcribe_audio(
                audio_data,
                user_id=self.user_id,
                session_id=self.session.id if self.session else None
            )

            if not result['success']:
                voice_run_tree.outputs = {"success": False, "error": result['error']}
                return {'error': result['error']}

            voice_run_tree.outputs = {"transcription": result.get('transcription'), "success": True}

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

        # Close any existing topic trace before starting a new one
        if self._topic_trace_headers:
            self._close_topic_trace()

        # Create new topic thread ID for this goal conversation
        self._topic_thread_id = str(uuid.uuid4())

        # Create topic trace, capture headers, then immediately close
        with trace(
            name="articulation_topic_conversation",
            inputs={
                "goal_id": goal['id'],
                "goal_title": goal['title'],
                "introduce": introduce
            },
            metadata={
                "topic_thread_id": self._topic_thread_id,
                "session_id": self._thread_id,  # Link to parent session
                "goal_id": goal['id'],
                "goal_title": goal['title'],
                "harness_type": "articulation"
            },
            parent=self._parent_trace_headers  # Link to parent for nesting
        ) as topic_run_tree:
            self._topic_trace_headers = topic_run_tree.to_headers()
        # Topic trace ends here (child traces will link via headers)

        self.session.current_goal_index = goal_index
        self.session.current_rubric_item_index = 0
        self.session.current_attempts = 0
        self.session.current_topic_thread_id = self._topic_thread_id  # Persist for HTTP boundaries
        self.session.current_topic_trace_headers = json.dumps(dict(self._topic_trace_headers))  # Store headers
        # Set core_goal_id if not already set (first topic focused)
        if self.session.core_goal_id is None:
            self.session.core_goal_id = goal['id']
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

    def _handle_frustration_and_end_topic(self, user_message, goals):
        """Handle frustration by ending current topic and marking as needs work.

        When a user expresses frustration:
        1. Acknowledge the difficulty empathetically
        2. IMMEDIATELY end the current topic (no prolonged help attempts)
        3. Mark topic as "engaged" (needs more work, not passed)
        4. Offer to move on to a different topic or end session

        Returns dict with frustration_detected, topic_ended, topic_status flags
        for trace visibility.
        """
        current_goal = None
        if self.session.current_goal_index is not None and self.session.current_goal_index < len(goals):
            current_goal = goals[self.session.current_goal_index]

        if current_goal:
            # Mark topic as "engaged" (needs more work) - NOT passed
            self.update_gem_state(current_goal['id'], 'engaged')
            self.session.goals_engaged = (self.session.goals_engaged or 0) + 1
            db.session.commit()

            response = f"""I can see this topic is challenging right now - that's completely normal.

🔵 I've marked **{current_goal['title']}** as something to revisit later. No pressure.

Let's move on. Would you like to:
1. Try a different concept
2. End this session for now

You can always come back to practice this topic when you're ready."""

        else:
            response = """I can see you're finding this challenging - that's completely normal.

Would you like to:
1. Try a different concept
2. Take a break and come back later"""

        self.store_message('assistant', response)

        # Close topic trace with frustration status
        self._close_topic_trace(current_goal, 'frustrated')

        # Reset current goal state
        self.session.current_goal_index = None
        self.session.current_rubric_item_index = 0
        self.session.current_attempts = 0
        db.session.commit()

        return {
            'response': response,
            'frustration_detected': True,
            'topic_ended': True,
            'topic_status': 'engaged',  # Needs more work
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

        # Evaluate the response with session_id for LangSmith thread grouping
        passed, evaluation = evaluate_rubric_item(
            user_message,
            current_item,
            langsmith_extra=self._get_langsmith_extra()
        )

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

        response = f"""✓ That's a solid explanation!

Now let's explore a related aspect. {hint}"""

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
        # Close topic trace for the completed goal
        self._close_topic_trace(completed_goal, status)

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
            gem_message = "💎 **Mastery demonstrated!** You clearly understand this concept."
        else:
            gem_message = "🔵 **Good engagement!** You've shown effort on this concept."

        # Check if we should offer instructor unlock
        if engagement['can_request_instructor'] and not self.session.guide_me_mode:
            unlock_message = "\n\n✨ **You've unlocked instructor feedback!** You can now request a review when you're ready."
        else:
            unlock_message = ""

        if self.session.guide_me_mode:
            # Move to next goal
            next_index = self.recommend_next_goal()
            if next_index is not None:
                next_goal = all_goals[next_index]

                # Create new topic thread ID for the next goal
                self._topic_thread_id = str(uuid.uuid4())

                # Create topic trace, capture headers, then immediately close
                with trace(
                    name="articulation_topic_conversation",
                    inputs={
                        "goal_id": next_goal['id'],
                        "goal_title": next_goal['title'],
                        "introduce": True
                    },
                    metadata={
                        "topic_thread_id": self._topic_thread_id,
                        "session_id": self._thread_id,
                        "goal_id": next_goal['id'],
                        "goal_title": next_goal['title'],
                        "harness_type": "articulation"
                    },
                    parent=self._parent_trace_headers  # Link to parent for nesting
                ) as topic_run_tree:
                    self._topic_trace_headers = topic_run_tree.to_headers()
                # Topic trace ends here (child traces will link via headers)

                self.session.current_goal_index = next_index
                self.session.current_rubric_item_index = 0
                self.session.current_attempts = 0
                self.session.current_topic_thread_id = self._topic_thread_id
                self.session.current_topic_trace_headers = json.dumps(dict(self._topic_trace_headers))
                db.session.commit()

                # Mark new goal as in progress
                self.update_gem_state(next_goal['id'], 'in_progress')

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

        system_prompt = f"""You are the Digi Trainer helping a student articulate their understanding of code they've written.

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

        # Clear trace headers (no context managers to close - traces complete immediately)
        self._parent_trace_headers = None
        self._topic_trace_headers = None

        return {
            'success': True,
            'engagement': engagement,
            'can_request_instructor': engagement['can_request_instructor']
        }
