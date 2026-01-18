"""
Code Dojo - Learning Platform

A Flask-based learning platform where students can view modules,
watch tutorials, submit GitHub solutions, receive AI feedback,
and get instructor reviews.
"""

import re
import markdown
from markupsafe import Markup
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db
from models.user import User
from models.module import LearningModule

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)


# Custom Jinja2 filters
@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown to HTML with code highlighting."""
    if not text:
        return ''
    # Use markdown with fenced code blocks and code highlighting
    md = markdown.Markdown(extensions=[
        'fenced_code',
        'codehilite',
        'tables',
        'nl2br'
    ], extension_configs={
        'codehilite': {
            'css_class': 'highlight',
            'guess_lang': True,
        }
    })
    return Markup(md.convert(text))


@app.template_filter('format_diff')
def format_diff_filter(diff_text):
    """
    Format a code diff with syntax highlighting, line numbers, and file stats.

    Parses unified diff format and generates GitHub-style HTML output with:
    - File headers with stats (additions/deletions)
    - Line numbers (old and new)
    - Color-coded additions (green) and deletions (red)
    - Hunk headers showing line ranges
    """
    if not diff_text:
        return ''

    lines = diff_text.split('\n')
    formatted_lines = []
    current_file = None
    old_line_num = 0
    new_line_num = 0
    file_additions = 0
    file_deletions = 0
    in_diff_content = False

    def close_current_file():
        """Close the current file's diff-content div if open."""
        nonlocal in_diff_content
        if in_diff_content:
            formatted_lines.append('</div></div>')  # Close diff-content and diff-file
            in_diff_content = False

    def get_file_icon(filename):
        """Get an appropriate icon for the file type."""
        if filename.endswith('.py'):
            return '<span class="file-icon" title="Python">&#128013;</span>'  # Snake emoji
        elif filename.endswith(('.js', '.ts')):
            return '<span class="file-icon" title="JavaScript">&#128312;</span>'  # Yellow circle
        elif filename.endswith(('.html', '.htm')):
            return '<span class="file-icon" title="HTML">&#128196;</span>'  # Page
        elif filename.endswith('.css'):
            return '<span class="file-icon" title="CSS">&#127912;</span>'  # Palette
        else:
            return '<span class="file-icon">&#128196;</span>'  # Default page icon

    i = 0
    while i < len(lines):
        line = lines[i]

        # Git diff header - start of a new file
        if line.startswith('diff --git'):
            close_current_file()

            # Extract filename from "diff --git a/file b/file"
            match = re.match(r'diff --git a/(.+) b/(.+)', line)
            if match:
                current_file = match.group(2)
            else:
                current_file = line

            # Look ahead to count stats for this file
            file_additions = 0
            file_deletions = 0
            is_new_file = False
            is_deleted_file = False

            j = i + 1
            while j < len(lines) and not lines[j].startswith('diff --git'):
                peek_line = lines[j]
                if peek_line.startswith('new file'):
                    is_new_file = True
                elif peek_line.startswith('deleted file'):
                    is_deleted_file = True
                elif peek_line.startswith('+') and not peek_line.startswith('+++'):
                    file_additions += 1
                elif peek_line.startswith('-') and not peek_line.startswith('---'):
                    file_deletions += 1
                j += 1

            # Build file header with stats
            file_status = ''
            if is_new_file:
                file_status = '<span class="file-status new">NEW</span>'
            elif is_deleted_file:
                file_status = '<span class="file-status deleted">DELETED</span>'

            icon = get_file_icon(current_file)
            stats_html = ''
            if file_additions > 0 or file_deletions > 0:
                stats_html = f'<span class="file-stats"><span class="additions">+{file_additions}</span><span class="deletions">-{file_deletions}</span></span>'

            formatted_lines.append(f'<div class="diff-file">')
            formatted_lines.append(f'<div class="diff-file-header">{icon}<span class="file-name">{escape_html(current_file)}</span>{file_status}{stats_html}</div>')
            formatted_lines.append('<div class="diff-content">')
            in_diff_content = True

        # New/deleted file mode indicator
        elif line.startswith('new file') or line.startswith('deleted file'):
            # Skip - already handled in lookahead
            pass

        # Index line (skip)
        elif line.startswith('index '):
            pass

        # File markers (--- and +++)
        elif line.startswith('---') or line.startswith('+++'):
            # Skip file markers - we show the filename in the header
            pass

        # Hunk header - parse line numbers
        elif line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            match = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)', line)
            if match:
                old_line_num = int(match.group(1))
                new_line_num = int(match.group(2))
                context = match.group(3).strip()

                # Format hunk header
                hunk_text = f'@@ -{match.group(1)} +{match.group(2)} @@'
                if context:
                    hunk_text += f' {escape_html(context)}'
                formatted_lines.append(f'<div class="diff-hunk">{hunk_text}</div>')
            else:
                formatted_lines.append(f'<div class="diff-hunk">{escape_html(line)}</div>')

        # Added line
        elif line.startswith('+') and not line.startswith('+++'):
            content = line[1:] if len(line) > 1 else ''
            formatted_lines.append(
                f'<div class="diff-line diff-added">'
                f'<span class="line-num old"></span>'
                f'<span class="line-num new">{new_line_num}</span>'
                f'<span class="diff-marker">+</span>'
                f'<span class="diff-text">{escape_html(content)}</span>'
                f'</div>'
            )
            new_line_num += 1

        # Removed line
        elif line.startswith('-') and not line.startswith('---'):
            content = line[1:] if len(line) > 1 else ''
            formatted_lines.append(
                f'<div class="diff-line diff-removed">'
                f'<span class="line-num old">{old_line_num}</span>'
                f'<span class="line-num new"></span>'
                f'<span class="diff-marker">-</span>'
                f'<span class="diff-text">{escape_html(content)}</span>'
                f'</div>'
            )
            old_line_num += 1

        # Context line (or empty line in diff)
        elif in_diff_content and (line.startswith(' ') or line == ''):
            content = line[1:] if line.startswith(' ') and len(line) > 1 else ('' if line == '' else line)
            formatted_lines.append(
                f'<div class="diff-line diff-context">'
                f'<span class="line-num old">{old_line_num}</span>'
                f'<span class="line-num new">{new_line_num}</span>'
                f'<span class="diff-marker"> </span>'
                f'<span class="diff-text">{escape_html(content)}</span>'
                f'</div>'
            )
            old_line_num += 1
            new_line_num += 1

        # Binary file indicator
        elif line.startswith('Binary file'):
            formatted_lines.append(f'<div class="diff-binary">{escape_html(line)}</div>')

        i += 1

    close_current_file()

    return Markup('\n'.join(formatted_lines))


def escape_html(text):
    """Escape HTML special characters."""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


# Register blueprints
from routes.auth import auth_bp
from routes.modules import modules_bp
from routes.submissions import submissions_bp
from routes.admin import admin_bp
from routes.anatomy import anatomy_bp
from routes.scheduling import scheduling_bp

app.register_blueprint(auth_bp)
app.register_blueprint(modules_bp)
app.register_blueprint(submissions_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(anatomy_bp)
app.register_blueprint(scheduling_bp)


# Home route
@app.route('/')
def home():
    """Home page showing available learning modules."""
    modules = LearningModule.query.order_by(LearningModule.order).all()
    return render_template('home.html', modules=modules)


# Health check
@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'healthy'}


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('base.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=Config.DEBUG, port=5002)
