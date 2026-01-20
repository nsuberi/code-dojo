# Code Dojo - Learning Platform

A Flask-based learning platform where students can view modules, watch tutorials, submit GitHub solutions, receive AI feedback, and get instructor reviews.

## Features

- **Learning Modules**: Organized curriculum with video tutorials and coding challenges
- **GitHub Integration**: Students submit solutions via GitHub repository URLs
- **AI Feedback**: Automated code review using Claude AI
- **Instructor Review**: Human feedback and pass/fail grading
- **Role-based Access**: Student, Instructor, and Admin roles

## Quick Start

### One-Command Startup (Recommended)

```bash
git clone <repository-url>
cd code-dojo
./start.sh
```

The startup script will automatically:
- Check for virtual environment and dependencies
- Create and seed the database if needed
- Start Flask on http://localhost:5002

**First run:** The script will prompt you to create a virtual environment and install dependencies.

### Manual Setup (Alternative)

If you prefer manual control:

1. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database**
   ```bash
   python seed_data.py --all
   ```

4. **Run the server**
   ```bash
   python app.py
   ```

The app will be available at `http://localhost:5002`

## Managing the Application

### Starting the App

```bash
./start.sh              # Smart startup (checks DB, seeds if needed)
./start.sh --fresh      # Reset database and start fresh (DESTRUCTIVE)
./start.sh --no-seed    # Quick restart without DB checks
./start.sh --seed-only  # Only seed database, don't start app
```

### Stopping the App

Press `Ctrl+C` in the terminal, or:

```bash
kill $(lsof -ti:5002)
```

### Checking Database Status

```bash
python seed_data.py --check
```

### Resetting the Database

```bash
./start.sh --fresh
# or manually:
python seed_data.py --reset
python seed_data.py --rubrics
python seed_data.py --challenge-rubric
```

## Demo Accounts

After running `seed_data.py`:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@codedojo.com | admin123 |
| Instructor | instructor@codedojo.com | instructor123 |
| Student | alice@example.com | student123 |
| Student | bob@example.com | student123 |

## Creating Demo Submissions

To populate the platform with sample submissions:

```bash
python demo_submissions.py
```

This creates:
- Alice's submission using the API Key authentication solution
- Bob's submission using the HTTP Basic Auth solution
- AI feedback for both submissions
- Instructor review for Bob's submission (marked as passed)

## Troubleshooting

### CoreLearningGoals (Gems) show 0 in the UI

**Symptom:** Console shows "no core learning goals defined for this challenge yet"

**Cause:** Database was seeded without the `--rubrics` flag

**Fix:**
```bash
python seed_data.py --rubrics
python seed_data.py --challenge-rubric
# or reset everything:
./start.sh --fresh
```

### Port 5002 already in use

**Cause:** Flask is already running or another process is using the port

**Fix:**
```bash
# Kill the process using port 5002
kill $(lsof -ti:5002)
# Then restart
./start.sh
```

### "No module named 'flask'" error

**Cause:** Virtual environment not activated or dependencies not installed

**Fix:**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
./start.sh
```

### Database file permission errors

**Cause:** Incorrect permissions on instance/ directory

**Fix:**
```bash
mkdir -p instance
chmod 755 instance/
# If database exists:
chmod 644 instance/code_dojo.db
```

### Demo submissions don't appear

**Cause:** Demo data not created (separate from seed data)

**Fix:**
```bash
python demo_submissions.py
```

## Claude Code Plugin

This repository includes a local plugin for Claude Code that enhances PR analysis and architectural review capabilities.

### Installing the arch-pr-analyzer Plugin

If you're using Claude Code CLI, you can install the local plugin:

```bash
# Add the local marketplace
/plugin marketplace add ./local-marketplace

# Install the plugin
/plugin install arch-pr-analyzer@code-dojo-plugins

# Restart Claude Code to load the plugin
```

Or from your terminal:

```bash
claude plugin marketplace add ./local-marketplace
claude plugin install arch-pr-analyzer@code-dojo-plugins
```

### Using the Plugin

Once installed, you can:
- Run `/arch-pr-analyzer:arch-analyze` to analyze PR architectural changes
- Access architectural analysis skills for codebase insights
- Use multi-granularity reports and diagrams for code reviews

See `local-marketplace/README.md` for more details.

## Project Structure

```
code-dojo/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── seed_data.py                # Database initialization
├── demo_submissions.py         # Create sample submissions
├── local-marketplace/          # Claude Code plugin marketplace
│   └── plugins/
│       └── arch-pr-analyzer/   # PR architecture analysis plugin
├── models/
│   ├── user.py                 # User model
│   ├── module.py               # LearningModule model
│   ├── goal.py                 # LearningGoal model
│   ├── submission.py           # Submission model
│   ├── ai_feedback.py          # AIFeedback model
│   └── instructor_feedback.py  # InstructorFeedback model
├── routes/
│   ├── auth.py                 # Authentication routes
│   ├── modules.py              # Curriculum routes
│   ├── submissions.py          # Submission routes
│   └── admin.py                # Admin/instructor routes
├── services/
│   ├── github.py               # GitHub API integration
│   └── ai_feedback.py          # Claude API integration
├── middleware/
│   └── auth.py                 # Authentication decorators
├── templates/                  # Jinja2 templates
└── static/                     # CSS and JavaScript
```

## The Learning Challenge

The default curriculum teaches **API Authentication** using the Snippet Manager starter repo:

- **Starter Repository**: https://github.com/nsuberi/snippet-manager-starter
- **Challenge**: Add authentication to protect write operations
- **Two Solutions Available**:
  - `with-api-auth` branch: API Key authentication
  - `with-basic-auth` branch: HTTP Basic Auth

## User Workflows

### Student Flow
1. Sign up / Log in
2. Browse learning modules
3. Watch tutorial video
4. Read challenge description
5. Fork starter repo and implement solution
6. Submit GitHub repo URL and branch
7. Receive AI feedback
8. Request instructor review
9. Get pass/fail result with comments

### Instructor Flow
1. Log in as instructor
2. View submissions awaiting review
3. See code diff and AI feedback
4. Add comments and pass/fail decision
5. Submit review

### Admin Flow
1. Log in as admin
2. View all students and submissions
3. Access instructor review functionality
4. Monitor platform activity

## Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: SQLite
- **Auth**: Flask-Login, Werkzeug password hashing
- **AI**: Anthropic Claude API
- **Frontend**: Jinja2 templates, vanilla CSS/JS

## License

MIT License - feel free to use this for learning and experimentation.
