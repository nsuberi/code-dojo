# Exercise Templates and Quick Start

Quick reference templates for creating diagnosis exercises.

## Quick Start Checklist

Before creating the exercise:
- [ ] Have two commit hashes (before and after)
- [ ] Know the symptom that was observed
- [ ] Know what environment/context triggered it
- [ ] Have access to the repository
- [ ] (Optional) Run `scripts/analyze_diff.py` for automated analysis

Creating the exercise:
- [ ] Write "The Symptom" section with concrete details
- [ ] Identify 3-5 system layers
- [ ] For each layer, document: what's there, why it did/didn't break, key insight
- [ ] Extract the actual code changes from the diff
- [ ] Create 4-5 diagnostic questions
- [ ] Extract 2-3 transferable concepts
- [ ] Create a practice exercise with similar pattern

## Template: The Symptom

```markdown
## The Symptom

[Describe what the user experienced in concrete terms]

[Environment 1 (working)]:
```bash
[command or action taken]
[output showing it works]
```

[Environment 2 (broken)]:
```bash
[same command or action]
[output showing it's broken]
```

**Starting Question: [Open-ended question that frames the investigation]**
```

**Examples of good starting questions:**
- "What changed between working and broken?"
- "Where would you look first to diagnose this?"
- "What layer of the system could cause this symptom?"
- "What information is the app missing?"

## Template: Layer Analysis

```markdown
### Layer [N]: [Layer Name] [Status Icon]

**What's here:**
- [Component 1: brief description]
- [Component 2: brief description]
- [Component 3: brief description]

**Why it [didn't break / broke / changed]:**
- [Reason 1: mechanical explanation]
- [Reason 2: mechanical explanation]

**Key insight:** [One sentence takeaway about this layer's role]
```

**Status Icons:**
- ✅ `(UNCHANGED)` - worked before and after
- ⚠️ `(CHANGED)` - modified as part of fix  
- 🔴 `(BROKEN)` - the problem layer
- 🆕 `(NEW)` - added in the fix

**Good "Key insights" examples:**
- "The application layer doesn't know or care about the network"
- "Routes match on path, which the proxy doesn't modify"
- "Configuration changes don't require code changes"
- "The database layer is isolated from HTTP concerns"

## Template: The Fix

```markdown
## The Anatomical Fix

### What needs to change:

**1. [Description of change]:**

```[language]
[actual code from after commit]
```

**What this does:**
- [Mechanical explanation of line/block 1]
- [Mechanical explanation of line/block 2]
- [Mechanical explanation of line/block 3]

[Optional sections 2, 3, etc. for additional changes]
```

**Tips:**
- Use the ACTUAL code from the commit, not paraphrased
- Explain what each significant line does
- Connect the change to the root cause
- Avoid just describing syntax; explain semantics

## Template: Diagnostic Questions

```markdown
## Diagnosis Questions (for learners)

### Question 1: Why didn't [unchanged component] break?
**Answer:** [Explain the boundary/responsibility that kept it working]

### Question 2: [Question about the failure mechanism]
**Answer:** [Explain the root cause]

### Question 3: What would break WITHOUT the fix?
- [Consequence 1]
- [Consequence 2]
- [Consequence 3]

### Question 4: What WOULDN'T break even without the fix?
- [Thing 1 with brief explanation]
- [Thing 2 with brief explanation]
```

**Question patterns:**

**Understanding boundaries:**
- "Why didn't the [X layer] break?"
- "What would happen if the problem was in [Y layer] instead?"
- "Why does [Z] still work even though [W] is broken?"

**Root cause analysis:**
- "What information does [component] need but not have?"
- "What assumption does [code] make that's violated?"
- "What changed in the environment but not the code?"

**Impact analysis:**
- "What would break WITHOUT the fix?"
- "What WOULDN'T break even without the fix?"
- "When would you see this symptom vs. a different symptom?"

## Template: Transferable Pattern

```markdown
## The Pattern: What This Teaches

### Core Concepts:

1. **[Concept name]**
   - [Specific learning point from this case]
   - [Generalized principle]

2. **[Concept name]**
   - [Specific learning point]
   - [Generalized principle]

### Diagnostic Skill Building:

**When [symptom pattern], ask:**
1. [Diagnostic question 1]
2. [Diagnostic question 2]
3. [Diagnostic question 3]
4. [Diagnostic question 4]
```

**Good concept extractions:**
- Start specific: "Flask's url_for() uses request metadata"
- Generalize: "URL generators need to know the external context"
- Make it transferable: "Context awareness - apps need to know where they're running"

**Good decision tree questions:**
- Observable: "What's different between the environments?"
- Testable: "Are there intermediaries in the request path?"
- Actionable: "Does the app know about those intermediaries?"
- Root cause: "What information exists but isn't being used?"

## Template: Practice Exercise

```markdown
## Practice Exercise

**Given this error:** "[Different but related error message]"

**Walk through:**
1. Which layer is this happening in? ([Expected answer])
2. What's working? ([Expected answer])
3. What's the gap? ([Expected answer])
4. What information exists but isn't being used? ([Expected answer])
5. What's the minimal fix? ([Expected answer])
```

**Creating good practice exercises:**
1. **Same pattern, different details:**
   - Original: Flask URL generation with proxy
   - Practice: Django redirect with load balancer
   
2. **Same root cause, different symptom:**
   - Original: Links point to localhost
   - Practice: Webhooks fail with 404
   
3. **Same layer, different fix:**
   - Original: Missing ProxyFix middleware
   - Practice: Missing ALLOWED_HOSTS setting

## Common Section Titles

Use consistent heading structure:

```markdown
# [Title]: [Specific Problem Name]

## The Symptom
## Diagnostic Framework: [System] Anatomy
### Layer 1: [Name] [Icon]
### Layer 2: [Name] [Icon]
### Layer N: [Name] [Icon]
## The Anatomical Fix
## Diagnosis Questions (for learners)
## The Pattern: What This Teaches
## Practice Exercise
```

## Example: Complete Mini Exercise

```markdown
# Diagnosis Exercise: Docker Environment Variable Mystery

## The Symptom

Your app works perfectly locally but crashes immediately in Docker.

Locally:
```bash
$ python app.py
Connecting to database at postgresql://localhost:5432/mydb
✓ Connected successfully
```

In Docker:
```bash
$ docker run myapp
Connecting to database at postgresql://localhost:5432/mydb
✗ Error: Connection refused
```

**Starting Question: The code is identical - what's different?**

## Diagnostic Framework: Container Networking Anatomy

### Layer 1: Application Code ✅ (UNCHANGED)

**What's here:**
- Database connection logic
- Connection string: `postgresql://localhost:5432/mydb`
- Error handling

**Why it didn't break:**
- The code is identical
- The logic works fine
- Python doesn't care about the network

**Key insight:** Application code doesn't know where "localhost" points.

### Layer 2: Network Resolution 🔴 (BROKEN)

**What's here:**
- DNS resolution of "localhost"
- Network namespace

**Why it broke:**
- Locally: localhost → 127.0.0.1 → database on your machine
- Docker: localhost → 127.0.0.1 → inside container (no database there!)

**Key insight:** "localhost" means different things in different network namespaces.

## The Anatomical Fix

**1. Use environment variable for database host:**

```python
import os

DB_HOST = os.getenv('DB_HOST', 'localhost')
connection_string = f"postgresql://{DB_HOST}:5432/mydb"
```

**What this does:**
- Reads DB_HOST from environment
- Falls back to 'localhost' for local development
- Allows Docker to inject 'host.docker.internal' or service name

**2. Set environment variable in docker-compose.yml:**

```yaml
services:
  app:
    environment:
      - DB_HOST=host.docker.internal
```

## Diagnosis Questions

### Question 1: Why did the database queries work locally?
**Answer:** Locally, "localhost" correctly resolves to the machine running the database.

### Question 2: What would break WITHOUT the fix?
- Any database operation
- But NOT code that doesn't use the database

### Question 3: What WOULDN'T break?
- Code that only uses in-memory data
- File operations (if files are mounted correctly)

## The Pattern: What This Teaches

**Core Concept: Network context**
- "localhost" is relative to network namespace
- Containers have isolated network namespaces
- Configuration must be environment-aware

**When something works locally but not in Docker, ask:**
1. What network resources does the code access?
2. How are those resources identified (hardcoded vs configurable)?
3. What do those identifiers resolve to in each environment?

## Practice Exercise

**Given:** "API calls to localhost:8000 work locally but fail in Docker"

**Walk through:**
1. Which layer? (Network resolution layer)
2. What's working? (Application code, HTTP client)
3. What's the gap? (localhost resolves to wrong place in container)
4. What's the fix? (Use environment variable for API host)
```

---

This template demonstrates all the key elements in a concise example.
