# Example: Flask Proxy URL Generation Fix

This is a complete example of a diagnosis exercise following the tech-diagnosis-exercise skill format.

**Commits analyzed:**
- Before: Flask app with basic routing
- After: Added ProxyFix middleware for URL generation

**Problem:** App worked locally but broke when deployed to GitHub Codespaces because URL generation didn't account for proxy headers.

---

# Diagnosis Exercise: "It Works on My Machine" - The Flask Proxy Mystery

## The Symptom

Your Flask app runs perfectly when you start it locally:
```bash
$ python app.py
 * Running on http://127.0.0.1:5000
```

You click around - everything works. Links go where they should. Forms submit. Images load.

You push to GitHub Codespaces. The app starts. The logs look identical. But when you visit the URL... things break. Links point to wrong places. Redirects fail. Static files 404.

**Starting Question: What changed between working and broken?**

---

## Diagnostic Framework: The Network Anatomy

Let's map the journey of a request through the system, identifying what's the same and what's different.

### Layer 1: Your Application Code ✅ (UNCHANGED)

**What's here:**
- Your Flask routes (`@app.route('/dashboard')`)
- Your business logic
- Your templates with `{{ url_for('dashboard') }}`
- Your Python imports and dependencies

**Why it didn't break:**
- The *code* is identical
- Python doesn't care where it runs
- The logic (`if user.is_admin: ...`) works the same

**Key insight:** The application layer doesn't know or care about the network. It just responds to requests and generates responses.

---

### Layer 2: The Port Binding ✅ (MOSTLY UNCHANGED)

**What's here:**
- Flask binds to a port: `app.run(port=5000)`
- The operating system listens on that port
- Requests arriving at that port get handed to Flask

**Why it didn't break:**
- Flask *still* binds to port 5000 in Codespaces
- The binding mechanism is identical
- The port number didn't change

**What DID change:**
- *Who* sends requests to that port
- Locally: your browser directly
- Codespaces: a proxy forwards requests

**Key insight:** Your app is still listening on the same port. The problem isn't "can requests reach the port?" but "does the app understand where those requests came from?"

---

### Layer 3: The Proxy Layer ⚠️ (NEW - THIS IS THE PROBLEM ZONE)

**What's here (in Codespaces only):**

```
[Your Browser] → [GitHub's Proxy] → [Your Flask App]
    ↓                    ↓                ↓
URL you see      URL transformation    URL Flask sees
```

**The anatomy of the proxy:**

**Incoming request you make:**
```
https://username-12345.app.github.dev/dashboard
```

**What the proxy does:**
```
1. Receives the request at the public URL
2. Adds headers:
   X-Forwarded-Proto: https
   X-Forwarded-Host: username-12345.app.github.dev
   X-Forwarded-Prefix: /  (or some prefix)
3. Forwards to: http://localhost:5000/dashboard
```

**What Flask sees (by default):**
```
Host: localhost:5000
Path: /dashboard
Protocol: http
```

**What Flask needs to know but doesn't:**
- The *original* URL was https://username-12345.app.github.dev/dashboard
- When it generates links, they should use that external URL
- When it generates redirects, they should use that external URL

---

### Layer 4: URL Generation 🔴 (BROKEN - THE CORE ISSUE)

**What Flask does when generating URLs:**

```python
# In your template:
{{ url_for('dashboard') }}
```

**Locally, Flask generates:**
```
http://localhost:5000/dashboard  ✅ Correct!
```

**In Codespaces (without fix), Flask generates:**
```
http://localhost:5000/dashboard  ❌ Wrong! Browser can't reach this.
```

**In Codespaces (with fix), Flask generates:**
```
https://username-12345.app.github.dev/dashboard  ✅ Correct!
```

**Why it breaks:**
- Flask doesn't automatically read the `X-Forwarded-*` headers
- It uses the *direct* request information (Host: localhost)
- Generated URLs work locally but fail when the app is behind a proxy

---

## The Anatomical Fix

### What needs to change:

**1. Tell Flask to trust proxy headers:**

```python
from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,      # Trust X-Forwarded-For
    x_proto=1,    # Trust X-Forwarded-Proto (http→https)
    x_host=1,     # Trust X-Forwarded-Host (localhost→external domain)
    x_prefix=1    # Trust X-Forwarded-Prefix (if paths are rewritten)
)
```

**What this does:**
- Wraps Flask's request handler in middleware
- Reads the `X-Forwarded-*` headers the proxy adds
- Tells Flask "pretend the request came from the external URL"
- Now `url_for()` generates correct external URLs

**2. (Sometimes) Update the application root:**

```python
# If the proxy adds a prefix like /app-name/
app.config['APPLICATION_ROOT'] = '/app-name'
```

---

## Diagnosis Questions (for learners)

### Question 1: Why didn't the Flask routes break?
**Answer:** Routes match on the *path* (`/dashboard`), which the proxy doesn't change. The proxy forwards the path as-is.

### Question 2: Why didn't form submissions break?
**Answer:** If forms use relative paths (`action="/submit"`) or path-only `url_for()`, they might *partially* work - until they redirect.

### Question 3: What would break WITHOUT the proxy fix?
- `url_for('dashboard')` generates `http://localhost:5000/dashboard` (browser can't reach)
- `redirect(url_for('login'))` sends browser to unreachable URL
- Static files referenced with `url_for('static', filename='app.css')` fail
- Any OAuth redirects that need to return to your app

### Question 4: What WOULDN'T break even without the fix?
- Template rendering (templates don't care about URLs until they generate links)
- Database queries (database doesn't care about network)
- Hard-coded links (`<a href="/dashboard">`) might work if you're already on the site
- API endpoints called directly with full URLs

---

## The Pattern: What This Teaches

### Core Concepts:

1. **Environments are layers**
   - Application layer (your code)
   - Network layer (ports, proxies)
   - Each layer has different knowledge

2. **Context awareness**
   - Your code needs to know *where it's running*
   - Not just "does it work?" but "does it work in context?"

3. **Request metadata**
   - Headers carry context
   - Middleware transforms requests
   - Apps must choose to trust that context

4. **Local vs. deployed isn't just location**
   - Network topology changes
   - What works direct doesn't work through proxy
   - Reverse proxy = requests come from an intermediary

### Diagnostic Skill Building:

**When something works locally but not deployed, ask:**
1. What's the network path in each environment?
2. Are there intermediaries (proxy, load balancer, CDN)?
3. Does my app know about those intermediaries?
4. What information gets lost or added in translation?

---

## Practice Exercise

**Given this error:** "Redirects go to `http://localhost:5000/login` instead of my external URL"

**Walk through:**
1. Which layer is this happening in? (URL generation layer)
2. What's working? (Flask is running, route exists, logic executes)
3. What's the gap? (Flask doesn't know external URL)
4. What information exists but isn't being used? (X-Forwarded headers)
5. What's the minimal fix? (ProxyFix middleware)

---

## What Makes This Exercise Work

**Notice the structure:**

1. ✅ **Concrete symptom** - Not abstract "URLs don't work" but specific "links point to localhost:5000"
2. ✅ **Layer-by-layer breakdown** - Four distinct layers, each analyzed separately
3. ✅ **Emphasis on negative space** - Three layers that DIDN'T break help understand the one that did
4. ✅ **Actual code** - The real ProxyFix implementation, not pseudocode
5. ✅ **Diagnostic questions** - Scaffold from observation to understanding
6. ✅ **Transferable pattern** - Explicit "when X, ask Y" decision tree
7. ✅ **Practice exercise** - Similar scenario testing the same diagnostic skill

This teaches **how to think about the problem**, not just **what the solution is**.
