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
