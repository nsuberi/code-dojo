"""Database models for Code Dojo."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.module import LearningModule
from models.goal import LearningGoal
from models.submission import Submission
from models.ai_feedback import AIFeedback
from models.instructor_feedback import InstructorFeedback
from models.anatomy_topic import AnatomyTopic
from models.anatomy_conversation import AnatomyConversation, ConversationMessage, StudentRealization

# New models for agent harness and gems system
from models.core_learning_goal import CoreLearningGoal
from models.goal_progress import GoalProgress
from models.agent_session import AgentSession, AgentMessage
from models.challenge_plan import ChallengePlan
from models.voice_input_metrics import VoiceInputMetrics

# Enhanced feedback and evaluation models (Section 2.1, 12)
from models.challenge_rubric import ChallengeRubric
from models.sensei_evaluation import SenseiEvaluation
from models.architectural_analysis import ArchitecturalAnalysis
from models.scheduled_session import ScheduledSession
