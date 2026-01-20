"""Architectural analysis model for storing PR architecture insights."""

import json
from datetime import datetime
from models import db


class ArchitecturalAnalysis(db.Model):
    """Architectural analysis data for a submission."""

    __tablename__ = 'architectural_analyses'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Structured architectural data (JSON)
    components_json = db.Column(db.Text)  # Component boundaries and mappings
    dependencies_diff_json = db.Column(db.Text)  # Added/removed dependencies
    api_changes_json = db.Column(db.Text)  # API endpoints added/modified/removed
    schema_changes_json = db.Column(db.Text)  # Database schema changes

    # Impact scores (low/medium/high)
    scope_score = db.Column(db.String(20))  # Number of components affected
    risk_score = db.Column(db.String(20))  # Breaking changes, backward compat
    complexity_score = db.Column(db.String(20))  # Lines changed, files touched

    # Mermaid diagrams
    component_diagram = db.Column(db.Text)  # Component dependency graph
    dataflow_diagram = db.Column(db.Text)  # Data flow sequence diagram
    dependency_diagram = db.Column(db.Text)  # Package dependency graph

    # Summary metadata
    files_changed = db.Column(db.Integer, default=0)
    lines_added = db.Column(db.Integer, default=0)
    lines_removed = db.Column(db.Integer, default=0)

    def get_components(self):
        """Parse and return components JSON."""
        return json.loads(self.components_json) if self.components_json else {}

    def set_components(self, components_dict):
        """Set components from a dictionary."""
        self.components_json = json.dumps(components_dict)

    def get_dependencies_diff(self):
        """Parse and return dependencies diff JSON."""
        return json.loads(self.dependencies_diff_json) if self.dependencies_diff_json else {}

    def set_dependencies_diff(self, deps_dict):
        """Set dependencies diff from a dictionary."""
        self.dependencies_diff_json = json.dumps(deps_dict)

    def get_api_changes(self):
        """Parse and return API changes JSON."""
        return json.loads(self.api_changes_json) if self.api_changes_json else {}

    def set_api_changes(self, api_dict):
        """Set API changes from a dictionary."""
        self.api_changes_json = json.dumps(api_dict)

    def get_schema_changes(self):
        """Parse and return schema changes JSON."""
        return json.loads(self.schema_changes_json) if self.schema_changes_json else {}

    def set_schema_changes(self, schema_dict):
        """Set schema changes from a dictionary."""
        self.schema_changes_json = json.dumps(schema_dict)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'components': self.get_components(),
            'dependencies_diff': self.get_dependencies_diff(),
            'api_changes': self.get_api_changes(),
            'schema_changes': self.get_schema_changes(),
            'scope_score': self.scope_score,
            'risk_score': self.risk_score,
            'complexity_score': self.complexity_score,
            'component_diagram': self.component_diagram,
            'dataflow_diagram': self.dataflow_diagram,
            'dependency_diagram': self.dependency_diagram,
            'files_changed': self.files_changed,
            'lines_added': self.lines_added,
            'lines_removed': self.lines_removed,
        }

    def __repr__(self):
        return f'<ArchitecturalAnalysis for Submission {self.submission_id}>'
