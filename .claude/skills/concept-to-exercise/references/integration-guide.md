# Integration with tech-diagnosis-exercise Skill

This reference explains how to invoke the tech-diagnosis-exercise skill after creating commits.

## Overview

The concept-to-exercise skill creates git commits, then hands them off to
tech-diagnosis-exercise skill to generate the actual learning exercise.

## Integration Flow

```
concept-to-exercise skill:
1. Parse concept description
2. Generate code (before/after states)
3. Create git repository and commits
   → Produces: commit hashes, repo path
   
tech-diagnosis-exercise skill:
4. Analyze git diff
5. Map technical layers
6. Generate diagnosis exercise
   → Produces: complete exercise markdown
```

## Handoff Format

After creating the commits, format the request like this:

```
Create a diagnosis exercise from the repository at [repo-path]:

Before: commit [before-hash] (broken state)
After: commit [after-hash] (fixed state)

Problem description:
[Describe the symptom users experience]

Environment context:
[Explain what's different between working/broken environments]

Key insight:
[What this teaches about system architecture/patterns]
```

## Example Handoff

```
Create a diagnosis exercise from the repository at 
/home/claude/demo-repos/flask-proxyfix:

Before: commit abc12345 (broken state)
After: commit def67890 (fixed state)

Problem description:
Flask application works perfectly when run locally with `python app.py`,
responding at http://localhost:5000 with working links and redirects.
When deployed to GitHub Codespaces, the app runs but all generated URLs
point to http://localhost:5000, which is unreachable from the browser.
Links don't work, redirects fail, and static files return 404 errors.

Environment context:
Local environment: Flask app binds to port 5000, browser connects directly
Codespaces environment: Flask behind reverse proxy, browser connects to
external URL like https://username-abc123.app.github.dev, but Flask
doesn't know about this external URL when generating links.

Key insight:
Flask's url_for() function uses request metadata (scheme, host, port) to
generate URLs. Behind a reverse proxy, Flask only sees the proxied request
(http://localhost:5000), not the original external request. The proxy adds
X-Forwarded-* headers with the original request info, but Flask doesn't
read these by default. The ProxyFix middleware teaches Flask to trust and
use these headers, restoring proper URL generation.
```

## What to Include

### 1. Repository Path
- Must be an absolute path
- Should be in `/home/claude/demo-repos/` or similar
- Must be a valid git repository

### 2. Commit Hashes
- Full hash or first 8 characters
- Before commit must come chronologically before after commit
- Both must exist in the repository

### 3. Problem Description (Symptom)
**Good example:**
```
When you visit the homepage, all links show http://localhost:5000/dashboard
instead of the external URL. Clicking them gives "connection refused" errors.
```

**Bad example:**
```
URLs don't work properly.
```

**Tips:**
- Be concrete about what the user experiences
- Include specific error messages if applicable
- Describe the observable behavior, not the root cause

### 4. Environment Context
**Good example:**
```
Locally: Direct browser → Flask on port 5000 (works)
Codespaces: Browser → GitHub proxy → Flask on port 5000 (breaks)

The proxy adds these headers:
  X-Forwarded-Proto: https
  X-Forwarded-Host: username-abc123.app.github.dev
  X-Forwarded-Port: 443

Flask sees:
  Proto: http
  Host: localhost
  Port: 5000
```

**Bad example:**
```
It works in one place but not another.
```

**Tips:**
- Explain what's different between environments
- Include network topology if relevant
- Mention intermediaries (proxies, load balancers, etc.)

### 5. Key Insight
**Good example:**
```
URL generation requires context awareness. Applications behind proxies
need to understand their external context, not just their internal
binding. Middleware provides this awareness without changing route code.
```

**Bad example:**
```
You need to add ProxyFix.
```

**Tips:**
- Extract the transferable principle
- Explain why the fix works at a conceptual level
- Frame it as a general pattern, not just this specific fix

## Automatic Handoff

When both skills are available, you can create a seamless workflow:

```python
# After creating commits...
repo_path = "/home/claude/demo-repos/flask-proxyfix"
before = "abc12345"
after = "def67890"

# Prepare handoff message
handoff = f"""
Create a diagnosis exercise from the repository at {repo_path}:

Before: commit {before} (broken state)
After: commit {after} (fixed state)

Problem description:
{symptom_description}

Environment context:
{environment_details}

Key insight:
{conceptual_takeaway}
"""

# The message invokes tech-diagnosis-exercise skill automatically
```

## Verifying Prerequisites

Before handing off, verify:

```bash
# 1. Repository exists and is valid
cd $REPO_PATH
git status

# 2. Both commits exist
git log --oneline | grep $BEFORE_COMMIT
git log --oneline | grep $AFTER_COMMIT

# 3. There are actual changes between them
git diff $BEFORE_COMMIT $AFTER_COMMIT --stat

# 4. The diff makes sense for the concept
git diff $BEFORE_COMMIT $AFTER_COMMIT
```

## Error Handling

If tech-diagnosis-exercise skill can't process the commits:

**Common issues:**
1. **Commits too far apart**: Too many unrelated changes
   - Fix: Focus the concept, reduce scope
   
2. **No meaningful diff**: Changes are whitespace only
   - Fix: Ensure actual code changes exist
   
3. **Too many files changed**: Diff is overwhelming
   - Fix: Keep example minimal (3-5 files max)
   
4. **Unclear symptom**: Can't identify what broke
   - Fix: Provide more specific problem description

## Output Location

After tech-diagnosis-exercise skill runs, files are created at:

```
/mnt/user-data/outputs/
└── [concept-name]-exercise.md
```

The concept-to-exercise skill should then:
1. Take this exercise markdown
2. Combine with the demo repository
3. Create a complete teaching package

## Complete Integration Example

```python
# Step 1: concept-to-exercise creates commits
create_git_repo("flask-proxyfix")
write_broken_state()
before = commit("Initial implementation - broken")
write_fixed_state()
after = commit("Fix: Add ProxyFix middleware")

# Step 2: Prepare handoff
handoff_message = format_handoff(
    repo_path="/home/claude/demo-repos/flask-proxyfix",
    before=before,
    after=after,
    symptom="Links point to unreachable localhost URLs",
    environment="Works locally, breaks in GitHub Codespaces",
    insight="URL generation needs proxy awareness"
)

# Step 3: Invoke tech-diagnosis-exercise (automatic)
# User sees: "Creating diagnosis exercise..."

# Step 4: Package results
combine_exercise_and_demo_code()
create_teaching_guide()

# Step 5: Present to user
present_complete_package()
```

## Best Practices

1. **Keep concepts focused**: One concept = one before/after pair
2. **Make symptoms concrete**: Actual errors, not vague descriptions
3. **Explain environment**: What triggers the problem?
4. **Extract principles**: What's the transferable lesson?
5. **Verify first**: Test the code before handing off

## Troubleshooting

**Symptom: Exercise doesn't explain the layers well**
- Cause: Problem description was too vague
- Fix: Provide more environmental context in handoff

**Symptom: Exercise focuses on wrong layer**
- Cause: Key insight wasn't clear
- Fix: Explicitly state what layer contains the core concept

**Symptom: Practice exercise isn't helpful**
- Cause: Transferable pattern wasn't identified
- Fix: Include the decision tree in "key insight"

## Reference

See `workflow-examples.md` for complete end-to-end examples of:
- Flask ProxyFix integration
- Pytest fixture scope integration
- Docker networking integration
- Async context manager integration
