# Code Templates for Concept Exercises

Quick-start templates for generating concept examples.

## Flask Application Templates

### Minimal Flask App (ProxyFix Example)

**File: app.py (Before - Broken)**
```python
from flask import Flask, render_template_string, url_for, redirect

app = Flask(__name__)

@app.route('/')
def index():
    login_url = url_for('login', _external=True)
    dashboard_url = url_for('dashboard', _external=True)
    return render_template_string('''
        <h1>Welcome</h1>
        <p>Login URL: {{ login_url }}</p>
        <p>Dashboard URL: {{ dashboard_url }}</p>
        <a href="{{ dashboard_url }}">Go to Dashboard</a>
    ''', login_url=login_url, dashboard_url=dashboard_url)

@app.route('/dashboard')
def dashboard():
    return render_template_string('<h1>Dashboard</h1><a href="/">Home</a>')

@app.route('/login')
def login():
    # After login, redirect to dashboard
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**File: app.py (After - Fixed)**
```python
from flask import Flask, render_template_string, url_for, redirect
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
    login_url = url_for('login', _external=True)
    dashboard_url = url_for('dashboard', _external=True)
    return render_template_string('''
        <h1>Welcome</h1>
        <p>Login URL: {{ login_url }}</p>
        <p>Dashboard URL: {{ dashboard_url }}</p>
        <a href="{{ dashboard_url }}">Go to Dashboard</a>
    ''', login_url=login_url, dashboard_url=dashboard_url)

@app.route('/dashboard')
def dashboard():
    return render_template_string('<h1>Dashboard</h1><a href="/">Home</a>')

@app.route('/login')
def login():
    # After login, redirect to dashboard
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**File: requirements.txt**
```
Flask==3.0.0
Werkzeug==3.0.1
```

**File: README.md**
```markdown
# Flask ProxyFix Example

## Running Locally

```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000 - everything works!

## Running in GitHub Codespaces

1. Open in Codespaces
2. Run `python app.py`
3. Visit the forwarded URL

**Before fix:** Links point to localhost:5000 (unreachable)
**After fix:** Links use the external Codespaces URL

## What This Teaches

How Flask's `url_for()` generates URLs and why apps behind reverse proxies
need ProxyFix middleware to read X-Forwarded headers.
```

---

### Flask Application Factory

**File: app.py (Before - Broken)**
```python
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'

from views import main_bp
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)
```

**File: views.py (Before - Broken)**
```python
from flask import Blueprint, render_template_string
from app import app  # Circular import!

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template_string('<h1>Hello World</h1>')

@main_bp.route('/config')
def show_config():
    return f"Secret key: {app.config['SECRET_KEY']}"
```

**File: app.py (After - Fixed)**
```python
from flask import Flask

def create_app(config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config or 'dev'
    
    # Import and register blueprints inside factory
    from views import main_bp
    app.register_blueprint(main_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

**File: views.py (After - Fixed)**
```python
from flask import Blueprint, render_template_string, current_app

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template_string('<h1>Hello World</h1>')

@main_bp.route('/config')
def show_config():
    # Use current_app instead of importing app
    return f"Secret key: {current_app.config['SECRET_KEY']}"
```

---

## pytest Templates

### Fixture Scope Issue

**File: database.py (Both versions)**
```python
class Database:
    def __init__(self):
        self.data = {}
    
    def insert(self, key, value):
        self.data[key] = value
    
    def get(self, key):
        return self.data.get(key)
    
    def clear(self):
        self.data.clear()
```

**File: conftest.py (Before - Broken)**
```python
import pytest
from database import Database

@pytest.fixture(scope='module')  # Wrong! Shared across tests
def db():
    database = Database()
    return database
```

**File: test_users.py (Before - Broken)**
```python
def test_create_user(db):
    db.insert('user1', {'name': 'Alice'})
    assert db.get('user1') == {'name': 'Alice'}

def test_user_not_found(db):
    # This fails if test_create_user ran first!
    # db still has user1 from previous test
    assert db.get('user1') is None
```

**File: conftest.py (After - Fixed)**
```python
import pytest
from database import Database

@pytest.fixture(scope='function')  # Correct! Fresh per test
def db():
    database = Database()
    yield database
    database.clear()  # Cleanup after each test
```

**File: test_users.py (After - Fixed)**
```python
def test_create_user(db):
    db.insert('user1', {'name': 'Alice'})
    assert db.get('user1') == {'name': 'Alice'}

def test_user_not_found(db):
    # Now this works! Fresh db each time
    assert db.get('user1') is None
```

---

### Mock Patching Location

**File: api_client.py (Both versions)**
```python
import requests

def fetch_user(user_id):
    response = requests.get(f'https://api.example.com/users/{user_id}')
    return response.json()
```

**File: test_api.py (Before - Broken)**
```python
from unittest.mock import patch
from api_client import fetch_user

@patch('requests.get')  # Wrong! Patching wrong location
def test_fetch_user(mock_get):
    mock_get.return_value.json.return_value = {'id': 1, 'name': 'Alice'}
    
    result = fetch_user(1)
    
    # This will fail because we patched the wrong location!
    assert result == {'id': 1, 'name': 'Alice'}
```

**File: test_api.py (After - Fixed)**
```python
from unittest.mock import patch
from api_client import fetch_user

@patch('api_client.requests.get')  # Correct! Patch where it's used
def test_fetch_user(mock_get):
    mock_get.return_value.json.return_value = {'id': 1, 'name': 'Alice'}
    
    result = fetch_user(1)
    
    # Now it works!
    assert result == {'id': 1, 'name': 'Alice'}
```

---

## Docker/Infrastructure Templates

### Environment Variables

**File: app.py (Before - Broken)**
```python
from flask import Flask
import psycopg2

app = Flask(__name__)

# Hardcoded connection string!
DATABASE_URL = "postgresql://localhost:5432/mydb"

@app.route('/users')
def get_users():
    conn = psycopg2.connect(DATABASE_URL)
    # ... query users
    return "Users"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**File: app.py (After - Fixed)**
```python
from flask import Flask
import psycopg2
import os

app = Flask(__name__)

# Use environment variable with sensible default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/mydb')

@app.route('/users')
def get_users():
    conn = psycopg2.connect(DATABASE_URL)
    # ... query users
    return "Users"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**File: docker-compose.yml (After only)**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://db:5432/mydb
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_PASSWORD=secret
```

**File: Dockerfile (Both versions)**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

---

## Async/Await Templates

### Async Context Manager

**File: api_client.py (Before - Broken)**
```python
import aiohttp

async def fetch_data(url):
    # Missing async with!
    session = aiohttp.ClientSession()
    response = await session.get(url)
    data = await response.json()
    # Session never closed!
    return data
```

**File: api_client.py (After - Fixed)**
```python
import aiohttp

async def fetch_data(url):
    # Proper async context manager
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data
```

**File: test_api.py (Both versions)**
```python
import pytest
from api_client import fetch_data

@pytest.mark.asyncio
async def test_fetch_data():
    # This would leak resources with the "before" version
    result = await fetch_data('https://api.example.com/data')
    assert 'key' in result
```

---

## README Template

```markdown
# [Concept Name] Example

## What This Demonstrates

[1-2 sentence explanation of the concept]

## The Problem

When you [describe scenario], [symptom occurs].

**Why this happens:**
[Explanation of root cause]

## The Fix

[Brief description of what changes]

## Running the Example

### Before Fix

```bash
git checkout [before-commit-hash]
pip install -r requirements.txt
python app.py  # or pytest
```

**Expected behavior:** [what goes wrong]

### After Fix

```bash
git checkout [after-commit-hash]
python app.py  # or pytest
```

**Expected behavior:** [what works now]

## Key Takeaway

[One sentence: what developers should remember]

## See Also

- Diagnosis Exercise: See EXERCISE.md for full analysis
- [Link to relevant documentation]
```

---

## Commit Message Templates

### Before Commit (Broken State)

```
Initial implementation - [symptom]

Demonstrates [concept] in broken state.

Problem: [what goes wrong]
- [Detail 1]
- [Detail 2]

Environment: [where/when it fails]
Symptom: [observable behavior]
```

### After Commit (Fixed State)

```
Fix: [what was fixed]

Changes:
- [Change 1]
- [Change 2]

Why:
[Explanation of why these changes fix the problem]

Teaches:
- [Concept 1]
- [Concept 2]
```

---

## Quick Reference: Template Selection

| Concept | Template | Files Needed |
|---------|----------|--------------|
| Flask proxy handling | Minimal Flask App | app.py, requirements.txt, README.md |
| Flask app factory | Application Factory | app.py, views.py, requirements.txt |
| pytest fixture scope | Fixture Scope | conftest.py, test_*.py, database.py |
| Mock patching | Mock Patching | api_client.py, test_api.py |
| Environment config | Environment Variables | app.py, docker-compose.yml, Dockerfile |
| Async context mgr | Async Context Manager | api_client.py, test_api.py |

Choose the template closest to the concept being taught, then adapt as needed.
