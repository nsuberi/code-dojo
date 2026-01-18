"""Learning module routes."""

from flask import Blueprint, render_template, abort
from models.module import LearningModule
from models.goal import LearningGoal

modules_bp = Blueprint('modules', __name__, url_prefix='/modules')


@modules_bp.route('/<int:module_id>')
def module_detail(module_id):
    """Display a learning module with its goals."""
    module = LearningModule.query.get_or_404(module_id)
    goals = module.goals.order_by(LearningGoal.order).all()
    return render_template('modules/detail.html', module=module, goals=goals)


@modules_bp.route('/<int:module_id>/goals/<int:goal_id>')
def goal_detail(module_id, goal_id):
    """Display a specific learning goal."""
    module = LearningModule.query.get_or_404(module_id)
    goal = LearningGoal.query.filter_by(id=goal_id, module_id=module_id).first_or_404()
    return render_template('modules/goal.html', module=module, goal=goal)
