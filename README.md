# Code Dojo - Learning Platform

A Flask-based learning platform where students can view modules, watch tutorials, submit GitHub solutions, receive AI feedback, and get instructor reviews.

## Features

- **Learning Modules**: Organized curriculum with video tutorials and coding challenges
- **GitHub Integration**: Students submit solutions via GitHub repository URLs
- **AI Feedback**: Automated code review using Claude AI
- **Instructor Review**: Human feedback and pass/fail grading
- **Role-based Access**: Student, Instructor, and Admin roles

## Quick Start

### 1. Set up virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables (optional)

Create a `.env` file:

```bash
FLASK_SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-api-key  # For AI feedback
```

### 4. Initialize the database

```bash
python seed_data.py
```

This creates:
- Sample learning module and challenges
- Admin, instructor, and student accounts

### 5. Run the server

```bash
python app.py
```

The app will be available at `http://localhost:5002`

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

## Project Structure

```
code-dojo/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── seed_data.py                # Database initialization
├── demo_submissions.py         # Create sample submissions
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
