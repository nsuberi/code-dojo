---
name: concept-to-exercise
description: Generate diagnosis exercises from concept descriptions. Use when user wants to teach a technical concept (Python testing, Flask apps, deployment, async code, etc.) by creating a broken→fixed code example and turning it into a diagnosis exercise. Takes a concept description, generates two git commits (before/after fix), then creates an interactive learning exercise using the tech-diagnosis-exercise skill.
license: MIT License - see LICENSE.txt
---

# Concept to Exercise Generator

This skill creates complete diagnosis exercises from concept descriptions by:
1. Generating realistic code that demonstrates a problem
2. Creating git commits for broken and fixed states
3. Invoking tech-diagnosis-exercise to create the learning material

## Overview

**Input:** Description of what you want to teach
**Output:** Complete diagnosis exercise with real code examples

**Example request:**
```
Teach the concept of Flask's ProxyFix middleware for handling X-Forwarded headers
when deploying behind a reverse proxy.
```

**What happens:**
1. Creates minimal Flask app that breaks behind a proxy
2. Commits the broken state
3. Fixes it with ProxyFix middleware
4. Commits the fixed state
5. Generates diagnosis exercise explaining the anatomy of the fix

## Core Workflow

### Step 1: Understand the Concept

Parse the user's description to identify:

**1. Domain/Technology:**
- Python testing (pytest, fixtures, mocking, parametrization)
- Flask apps (routing, middleware, extensions, deployment)
- Infrastructure (Docker, environment variables, networking)
- Async code (asyncio, aiohttp, async patterns)
- Database (SQLAlchemy, migrations, transactions)
- API clients (requests, authentication, error handling)

**2. The Core Concept:**
- What specific thing are we teaching?
- What's the "aha moment" we want to create?
- What misunderstanding does this address?

**3. The Problem Pattern:**
- What symptom should the learner observe?
- What's the environmental context?
- What makes it non-obvious?

**4. The Fix:**
- What changes are needed?
- What layers are involved?
- What's the minimal fix that teaches the concept?

**Clarifying questions to ask if unclear:**
- "What environment triggers the problem? (local vs deployed, different OS, etc.)"
- "What symptom should the learner observe?"
- "What's the key insight you want them to learn?"
- "Should this be beginner, intermediate, or advanced level?"

### Step 2: Design the Code Example

Create a **minimal but realistic** code example that:

**Must haves:**
- Actually demonstrates the problem (not just commented code)
- Runs and fails in the expected way
- Fixes with clear, targeted changes
- Stays focused on one concept

**Design principles:**

**Keep it minimal:**
- Only include code necessary to demonstrate the concept
- No extraneous features or complexity
- Typically 3-5 files max

**Make it realistic:**
- Use real libraries and frameworks
- Follow common conventions
- Include realistic error messages

**Make it reproducible:**
- Include requirements.txt or dependencies
- Document how to run it
- Specify the environment that triggers the issue

**Example scope for "ProxyFix concept":**
```
Files needed:
- app.py (Flask app with url_for() usage)
- requirements.txt (Flask dependency)
- README.md (how to run locally vs in Codespaces)

Not needed:
- Full frontend
- Database
- Authentication
- Multiple routes beyond demonstration
```

### Step 3: Create Git Repository with Commits

**3a. Initialize repository:**

```bash
# Create workspace
mkdir -p /home/claude/demo-repos/[concept-name]
cd /home/claude/demo-repos/[concept-name]
git init
git config user.name "Diagnosis Exercise Generator"
git config user.email "exercises@example.com"
```

**3b. Create broken state:**

Write all files for the broken state, then:

```bash
git add .
git commit -m "Initial implementation - [symptom description]

Demonstrates [concept] in broken state.
Problem: [what goes wrong]
Environment: [where it fails]"
```

Capture the commit hash:
```bash
BEFORE_COMMIT=$(git rev-parse HEAD)
```

**3c. Create fixed state:**

Modify files to fix the problem, then:

```bash
git add .
git commit -m "Fix: [what was fixed]

Changes: [list key changes]
Why: [brief explanation of fix]
Teaches: [concept being demonstrated]"
```

Capture the commit hash:
```bash
AFTER_COMMIT=$(git rev-parse HEAD)
```

**3d. Verify the commits:**

```bash
# Show what changed
git diff $BEFORE_COMMIT $AFTER_COMMIT

# Verify we have both commits
git log --oneline
```

### Step 4: Prepare Context for Diagnosis Exercise

Gather all the information needed for the diagnosis exercise:

**Required information:**
1. Repository path
2. Before commit hash
3. After commit hash
4. Problem description (symptom the user experiences)
5. Environment context (what triggers it)
6. The "aha moment" (key insight)

**Format:**
```
Repository: /home/claude/demo-repos/[concept-name]
Before commit: [hash]
After commit: [hash]

Symptom: [concrete description of what breaks]
Environment context: [what's different between working/broken]
Key insight: [what this teaches about system architecture]
```

### Step 5: Invoke Diagnosis Exercise Skill

Now use the tech-diagnosis-exercise skill:

```
Create a diagnosis exercise from the repository at [path]:
- Before: commit [hash] (broken state)
- After: commit [hash] (fixed state)

Problem description:
[Symptom users experience]

Environment:
[Context that triggers the issue]

Key insight:
[What this teaches]
```

The tech-diagnosis-exercise skill will:
- Analyze the git diff
- Map the technical layers
- Create the diagnosis exercise
- Generate practice questions

### Step 6: Package Everything

Create a complete package with:

1. **The diagnosis exercise** (generated by tech-diagnosis-exercise skill)
2. **The demo repository** (the actual code)
3. **A README** explaining how to use both

**Directory structure:**
```
[concept-name]-exercise/
├── EXERCISE.md           # The diagnosis exercise
├── demo-code/           # The git repository
│   ├── .git/           
│   ├── [application files]
│   └── README.md       # How to run the demo
└── TEACHING_GUIDE.md   # How to use this for teaching
```

## Concept Patterns Library

Common patterns for different domains:

### Python Testing Patterns

**Fixture scope issues:**
```python
# Before: fixture with wrong scope causes state leakage
@pytest.fixture
def database():
    db = create_db()
    return db  # Not cleaned up!

# After: proper scope and cleanup
@pytest.fixture(scope="function")
def database():
    db = create_db()
    yield db
    db.cleanup()
```

**Mock patching location:**
```python
# Before: patching wrong import location
@patch('requests.get')  # Wrong!
def test_api_call():
    ...

# After: patch where it's used
@patch('myapp.api_client.requests.get')  # Right!
def test_api_call():
    ...
```

### Flask App Patterns

**Application factory pattern:**
```python
# Before: app created at module level (can't test)
app = Flask(__name__)
app.config['DEBUG'] = True

# After: factory pattern
def create_app(config=None):
    app = Flask(__name__)
    if config:
        app.config.update(config)
    return app
```

**Blueprint registration:**
```python
# Before: circular imports
from app import app
from views import bp
app.register_blueprint(bp)  # Circular!

# After: register in factory
def create_app():
    app = Flask(__name__)
    from views import bp
    app.register_blueprint(bp)
    return app
```

### Infrastructure Patterns

**Environment variables:**
```python
# Before: hardcoded config
DATABASE_URL = "postgresql://localhost:5432/db"

# After: environment-aware
import os
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/db')
```

**Docker networking:**
```yaml
# Before: uses localhost in Docker
services:
  app:
    environment:
      - DB_HOST=localhost  # Won't work!

# After: uses service name
services:
  app:
    environment:
      - DB_HOST=db
```

### Async Patterns

**Event loop in tests:**
```python
# Before: creates new event loop each test (slow)
def test_async_function():
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(my_async_func())

# After: reuses event loop with pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_func()
```

**Async context managers:**
```python
# Before: not awaiting async context manager
async with ClientSession() as session:  # Wrong!
    resp = await session.get(url)

# After: proper async context manager
async with aiohttp.ClientSession() as session:
    async with session.get(url) as resp:
        data = await resp.json()
```

## Code Generation Guidelines

### File Templates

**Flask app template:**
```python
from flask import Flask, render_template_string, url_for

app = Flask(__name__)

@app.route('/')
def index():
    # Demonstrate the concept here
    dashboard_url = url_for('dashboard')
    return render_template_string('''
        <h1>Home</h1>
        <a href="{{ url }}">Dashboard</a>
    ''', url=dashboard_url)

@app.route('/dashboard')
def dashboard():
    return render_template_string('<h1>Dashboard</h1>')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**pytest test template:**
```python
import pytest

def test_example():
    # Demonstrate the concept here
    result = function_under_test()
    assert result == expected_value

@pytest.fixture
def example_fixture():
    # Setup
    resource = create_resource()
    yield resource
    # Teardown
    resource.cleanup()
```

**Docker template:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

### Requirements.txt Templates

**Flask app:**
```
Flask==3.0.0
Werkzeug==3.0.1
```

**Testing:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
```

**Async:**
```
aiohttp==3.9.1
asyncio==3.4.3
```

## Example Workflows

### Example 1: Teaching Flask ProxyFix

**User request:**
```
Teach how to use ProxyFix middleware when deploying Flask behind a reverse proxy
```

**Skill execution:**

1. **Design the example:**
   - Create Flask app that uses url_for()
   - Works locally
   - Breaks in GitHub Codespaces (proxy environment)
   - Fix: Add ProxyFix middleware

2. **Generate files:**
   - `app.py` - Basic Flask app with url_for() usage
   - `requirements.txt` - Flask dependency
   - `README.md` - Instructions for local vs Codespaces

3. **Create commits:**
   - Commit 1: App without ProxyFix
   - Commit 2: App with ProxyFix middleware

4. **Invoke diagnosis exercise:**
   - Pass commits to tech-diagnosis-exercise skill
   - Generate full diagnosis exercise

5. **Package output:**
   - Exercise markdown
   - Demo repository
   - Teaching guide

### Example 2: Teaching Pytest Fixture Scope

**User request:**
```
Teach pytest fixture scope and how function vs module scope affects test isolation
```

**Skill execution:**

1. **Design the example:**
   - Create test file with database fixture
   - First version: module scope (state leakage)
   - Second version: function scope (proper isolation)

2. **Generate files:**
   - `test_database.py` - Tests that fail due to state leakage
   - `database.py` - Simple in-memory database
   - `conftest.py` - Fixture definitions
   - `requirements.txt` - pytest

3. **Create commits:**
   - Commit 1: Module-scoped fixture (tests fail intermittently)
   - Commit 2: Function-scoped fixture (tests isolated)

4. **Invoke diagnosis exercise:**
   - Explain the test execution layer
   - Explain the fixture lifecycle layer
   - Show what changed (scope parameter)

## Quality Checks

Before invoking the diagnosis exercise skill, verify:

- [ ] Code actually demonstrates the problem (run it!)
- [ ] The "before" state has the expected symptom
- [ ] The "after" state fixes it with minimal changes
- [ ] Git commits are clean and well-described
- [ ] README explains how to reproduce
- [ ] Focus is on one clear concept

## Anti-Patterns to Avoid

❌ **Don't:** Create complex examples with many concepts
✅ **Do:** Focus on one concept per exercise

❌ **Don't:** Use fake/placeholder code
✅ **Do:** Write code that actually runs and demonstrates the issue

❌ **Don't:** Make trivial examples (typo fixes)
✅ **Do:** Show realistic problems developers encounter

❌ **Don't:** Skip the verification step
✅ **Do:** Actually run the code before/after to verify the symptom

## Advanced Usage

### Chain Multiple Concepts

Create a series building on each other:

1. Basic Flask app
2. Add database (teaches connection handling)
3. Add testing (teaches test fixtures)
4. Add Docker (teaches environment config)

Each builds on the previous, creating a progression.

### Custom Patterns

User can provide their own code pattern:

```
Create an exercise teaching this pattern:
[paste code snippet]

The problem is: [description]
The fix is: [description]
```

The skill adapts to custom patterns.

## Usage Example

**Simple request:**
```
Create an exercise teaching Flask's application factory pattern
```

**Detailed request:**
```
Create an exercise teaching how to properly structure a Flask app with blueprints
to avoid circular imports.

Target audience: Intermediate developers
Key concepts: Application factory, blueprint registration, import order
Symptom: ImportError when trying to run the app
Environment: Any
```

**With reference code:**
```
I want to teach this concept using a similar structure to this code:
[paste example structure]

Create the broken/fixed commits and generate the exercise.
```

## Output Format

The skill produces three artifacts:

1. **Git repository** at `/home/claude/demo-repos/[concept-name]/`
2. **Diagnosis exercise** markdown file
3. **Teaching guide** explaining how to use both

All packaged together for easy distribution.
