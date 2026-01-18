# Complete Workflow Examples

End-to-end examples of using the concept-to-exercise skill.

## Example 1: Flask ProxyFix Concept

### User Request

```
Create an exercise teaching how to use Flask's ProxyFix middleware
when deploying behind a reverse proxy like in GitHub Codespaces.
```

### Skill Execution Flow

**Step 1: Parse the concept**
- Domain: Flask web applications
- Concept: ProxyFix middleware for reverse proxy deployment
- Problem pattern: "Works locally but not when deployed"
- Environment: GitHub Codespaces (has reverse proxy)

**Step 2: Design the code**
```
Files to create:
- app.py: Flask app using url_for() 
- requirements.txt: Flask dependency
- README.md: How to run locally vs Codespaces

Before state:
- app.py without ProxyFix
- url_for() generates localhost URLs

After state:
- app.py with ProxyFix middleware
- url_for() generates correct external URLs
```

**Step 3: Create repository and commits**

```bash
# Initialize
mkdir -p /home/claude/demo-repos/flask-proxyfix
cd /home/claude/demo-repos/flask-proxyfix
git init
git config user.name "Diagnosis Exercise Generator"
git config user.email "exercises@example.com"

# Create before state
cat > app.py << 'EOF'
from flask import Flask, url_for, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    dashboard_url = url_for('dashboard', _external=True)
    return render_template_string('''
        <h1>Home</h1>
        <p>Dashboard: <a href="{{ url }}">{{ url }}</a></p>
    ''', url=dashboard_url)

@app.route('/dashboard')
def dashboard():
    return '<h1>Dashboard</h1>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

cat > requirements.txt << 'EOF'
Flask==3.0.0
Werkzeug==3.0.1
EOF

cat > README.md << 'EOF'
# Flask ProxyFix Example

Run locally: python app.py
Run in Codespaces: Forward port, visit external URL

Issue: In Codespaces, url_for() generates localhost:5000 URLs
EOF

git add .
git commit -m "Initial implementation - URL generation breaks in Codespaces

Demonstrates Flask url_for() in broken state.

Problem: url_for(_external=True) generates localhost:5000 URLs
Environment: GitHub Codespaces (behind reverse proxy)
Symptom: Generated links point to localhost (unreachable from browser)"

BEFORE_COMMIT=$(git rev-parse HEAD)

# Create after state
cat > app.py << 'EOF'
from flask import Flask, url_for, render_template_string
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Fix: Trust proxy headers for URL generation
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_prefix=1
)

@app.route('/')
def index():
    dashboard_url = url_for('dashboard', _external=True)
    return render_template_string('''
        <h1>Home</h1>
        <p>Dashboard: <a href="{{ url }}">{{ url }}</a></p>
    ''', url=dashboard_url)

@app.route('/dashboard')
def dashboard():
    return '<h1>Dashboard</h1>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

git add .
git commit -m "Fix: Add ProxyFix middleware for URL generation behind proxy

Changes:
- Import ProxyFix from werkzeug.middleware.proxy_fix
- Wrap app.wsgi_app with ProxyFix
- Configure to trust X-Forwarded headers

Why:
When behind a reverse proxy, Flask doesn't automatically know the
external URL. ProxyFix reads X-Forwarded-* headers added by the proxy
and updates the request context so url_for() generates correct URLs.

Teaches:
- How reverse proxies modify requests
- Role of X-Forwarded headers
- Middleware pattern in Flask"

AFTER_COMMIT=$(git rev-parse HEAD)
```

**Step 4: Prepare diagnosis exercise context**

```
Repository: /home/claude/demo-repos/flask-proxyfix
Before commit: [first 8 chars of BEFORE_COMMIT]
After commit: [first 8 chars of AFTER_COMMIT]

Symptom:
Flask app runs successfully in GitHub Codespaces, but all generated
URLs point to http://localhost:5000 which is unreachable from the
browser. Links don't work, redirects fail, static file URLs 404.

Environment context:
Locally the app works fine. In GitHub Codespaces (or any deployment
behind a reverse proxy), url_for() doesn't know about the external URL
because it only sees the proxied request to localhost.

Key insight:
Flask's url_for() uses request metadata (scheme, host, path) to generate
URLs. Behind a proxy, this metadata reflects the internal connection
(http://localhost:5000), not the external URL. ProxyFix middleware reads
X-Forwarded headers to restore the original request context.
```

**Step 5: Invoke tech-diagnosis-exercise skill**

```
Create a diagnosis exercise from the repository at 
/home/claude/demo-repos/flask-proxyfix:

Before: commit [BEFORE_COMMIT] (broken state)  
After: commit [AFTER_COMMIT] (fixed state)

Problem description:
Flask app works locally but when deployed to GitHub Codespaces,
url_for() generates URLs pointing to localhost:5000 instead of
the external Codespaces URL. Links don't work from the browser.

Environment:
- Local: Flask app runs at http://localhost:5000 (works)
- Codespaces: Flask runs behind reverse proxy (breaks)
- The proxy adds X-Forwarded-* headers but Flask ignores them

Key insight:
URL generation needs to be proxy-aware. The middleware pattern
allows Flask to read proxy headers without changing route code.
```

**Step 6: Output**

Generated files:
- `flask-proxyfix-exercise/EXERCISE.md` - Full diagnosis exercise
- `flask-proxyfix-exercise/demo-code/` - Git repository
- `flask-proxyfix-exercise/TEACHING_GUIDE.md` - Usage instructions

---

## Example 2: Pytest Fixture Scope

### User Request

```
Teach pytest fixture scope - how function vs module scope affects
test isolation and why tests can fail intermittently with wrong scope.
```

### Skill Execution Flow

**Step 1: Parse concept**
- Domain: Python testing with pytest
- Concept: Fixture scope and test isolation
- Problem: Tests pass individually but fail when run together
- Root cause: Shared state between tests

**Step 2: Design code**

```
Files needed:
- database.py: Simple in-memory database
- conftest.py: Fixture definitions
- test_database.py: Tests that demonstrate the problem
- requirements.txt: pytest

Before state:
- Fixture with module scope (shared across tests)
- Tests fail intermittently due to shared state

After state:
- Fixture with function scope (isolated per test)
- Tests reliably pass
```

**Step 3: Create repository**

```bash
mkdir -p /home/claude/demo-repos/pytest-fixture-scope
cd /home/claude/demo-repos/pytest-fixture-scope
git init

# Before state files...
cat > database.py << 'EOF'
class Database:
    def __init__(self):
        self.users = {}
    
    def add_user(self, user_id, name):
        self.users[user_id] = name
    
    def get_user(self, user_id):
        return self.users.get(user_id)
    
    def clear(self):
        self.users.clear()
EOF

cat > conftest.py << 'EOF'
import pytest
from database import Database

@pytest.fixture(scope='module')  # WRONG: shared across all tests
def db():
    return Database()
EOF

cat > test_database.py << 'EOF'
def test_add_user(db):
    db.add_user(1, 'Alice')
    assert db.get_user(1) == 'Alice'

def test_user_not_found(db):
    # BUG: This assumes clean database
    # But if test_add_user ran first, user 1 exists!
    assert db.get_user(1) is None

def test_add_another_user(db):
    db.add_user(2, 'Bob')
    assert db.get_user(2) == 'Bob'
EOF

cat > requirements.txt << 'EOF'
pytest==7.4.3
EOF

cat > README.md << 'EOF'
# Pytest Fixture Scope Example

Run tests: pytest -v

Problem: Tests fail intermittently depending on order
EOF

git add .
git commit -m "Initial tests - intermittent failures due to fixture scope

Demonstrates pytest fixture scope in broken state.

Problem: Module-scoped fixture is shared across all tests
Environment: Running pytest with multiple tests
Symptom: test_user_not_found fails if test_add_user runs first"

# After state...
cat > conftest.py << 'EOF'
import pytest
from database import Database

@pytest.fixture(scope='function')  # CORRECT: fresh per test
def db():
    database = Database()
    yield database
    database.clear()
EOF

git add .
git commit -m "Fix: Change fixture scope to function for test isolation

Changes:
- Changed scope='module' to scope='function'
- Added yield instead of return
- Added cleanup after yield

Why:
Module scope shares the fixture across all tests in the module.
Function scope creates a fresh fixture for each test, ensuring
isolation. The yield pattern allows cleanup after each test.

Teaches:
- Fixture scope levels (function, class, module, session)
- Test isolation principles
- Fixture cleanup patterns"
```

**Step 4: Invoke diagnosis exercise skill**

The output would explain:
- Test Execution Layer (unchanged - pytest still runs tests)
- Fixture Lifecycle Layer (BROKEN - wrong scope)
- State Storage Layer (affected - shared state)
- Test Isolation Layer (FIXED - proper scope)

---

## Example 3: Docker Networking

### User Request

```
Create an exercise about Docker networking - why "localhost" doesn't work
inside containers and how to properly reference other services.
```

### Execution Summary

**Files created:**
- `app.py`: Python app connecting to database
- `Dockerfile`: Container definition
- `docker-compose.yml`: Multi-container setup
- `requirements.txt`: Dependencies

**Before commit:**
```python
# app.py
import psycopg2
DB_HOST = "localhost"  # WRONG in container!
conn = psycopg2.connect(f"postgresql://{DB_HOST}:5432/db")
```

**After commit:**
```python
# app.py  
import os
DB_HOST = os.getenv('DB_HOST', 'localhost')  # Environment-aware
conn = psycopg2.connect(f"postgresql://{DB_HOST}:5432/db")
```

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - DB_HOST=db  # Service name, not localhost
```

**Diagnosis exercise explains:**
- Application Layer (unchanged)
- Network Resolution Layer (BROKEN - localhost resolves wrong)
- Container Networking Layer (NEW - separate namespaces)
- Configuration Layer (FIXED - environment variable)

---

## Example 4: Async Context Manager

### User Request

```
Teach proper async context manager usage with aiohttp - why sessions
need to be properly closed and how to use async with correctly.
```

**Files:**
- `api_client.py`: Async HTTP client
- `test_client.py`: Tests
- `requirements.txt`: aiohttp, pytest-asyncio

**Before:** Missing `async with`, session not closed
**After:** Proper `async with` nesting

**Key teaching points:**
- Resource management in async code
- Context manager protocol
- Why leaking connections is bad

---

## Template for New Examples

```
### User Request
[What the user asks for]

### Concept Analysis
- Domain: [e.g., Flask, pytest, Docker]
- Concept: [What we're teaching]
- Problem pattern: [Type of issue]
- Key insight: [Main takeaway]

### Files Structure
- File 1: [purpose]
- File 2: [purpose]
...

### Before State
[What's broken and why]

### After State
[What changed and why it fixes it]

### Diagnosis Layers
1. Layer 1: [status and explanation]
2. Layer 2: [status and explanation]
...

### Expected Learning Outcomes
- [Outcome 1]
- [Outcome 2]
```

---

## Quick Reference: Concept to Files Mapping

| Concept | Key Files | Lines Changed |
|---------|-----------|---------------|
| Flask ProxyFix | app.py | ~5 lines |
| App Factory | app.py, views.py | ~15 lines |
| Fixture Scope | conftest.py | ~2 lines |
| Mock Patching | test_*.py | ~1 line |
| Docker Networking | app.py, docker-compose.yml | ~5 lines |
| Env Variables | app.py, .env | ~3 lines |
| Async Context | api_client.py | ~3 lines |

Keep examples minimal - focus on the concept, not building full apps.
