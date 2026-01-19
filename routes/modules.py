"""Learning module routes."""

from flask import Blueprint, render_template, abort
from flask_login import current_user
from models.module import LearningModule
from models.goal import LearningGoal
from models.submission import Submission
from models.goal_progress import GoalProgress
from models.core_learning_goal import CoreLearningGoal
from models.challenge_rubric import ChallengeRubric

modules_bp = Blueprint('modules', __name__, url_prefix='/modules')


@modules_bp.route('/<int:module_id>')
def module_detail(module_id):
    """Display a learning module with its goals."""
    module = LearningModule.query.get_or_404(module_id)
    goals = module.goals.order_by(LearningGoal.order).all()
    return render_template('modules/detail.html', module=module, goals=goals)


@modules_bp.route('/<int:module_id>/goals/<int:goal_id>')
def goal_detail(module_id, goal_id):
    """Display a specific learning goal with submission data for Review tab (Section 5)."""
    module = LearningModule.query.get_or_404(module_id)
    goal = LearningGoal.query.filter_by(id=goal_id, module_id=module_id).first_or_404()

    # Get latest submission for current user (if logged in)
    latest_submission = None
    goal_progress = []
    core_learning_goals = []

    if current_user.is_authenticated:
        latest_submission = Submission.query.filter_by(
            user_id=current_user.id,
            goal_id=goal_id
        ).order_by(Submission.created_at.desc()).first()

        # Get goal progress for gems display (by user, not by submission)
        # GoalProgress tracks user progress on CoreLearningGoals
        core_goal_ids = [cg.id for cg in CoreLearningGoal.query.filter_by(learning_goal_id=goal_id).all()]
        if core_goal_ids:
            goal_progress = GoalProgress.query.filter(
                GoalProgress.user_id == current_user.id,
                GoalProgress.core_goal_id.in_(core_goal_ids)
            ).all()

        # Get core learning goals for the Digi-Trainer
        core_learning_goals = CoreLearningGoal.query.filter_by(
            learning_goal_id=goal_id
        ).order_by(CoreLearningGoal.order_index).all()

    # Get challenge rubric if available
    challenge_rubric = ChallengeRubric.query.filter_by(learning_goal_id=goal_id).first()

    return render_template(
        'modules/goal.html',
        module=module,
        goal=goal,
        latest_submission=latest_submission,
        goal_progress=goal_progress,
        core_learning_goals=core_learning_goals,
        challenge_rubric=challenge_rubric
    )
