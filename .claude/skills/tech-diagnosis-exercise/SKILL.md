---
name: tech-diagnosis-exercise
description: Generate interactive technical diagnosis exercises from git commits. Use when user wants to create learning materials from code fixes, debug sessions, or technical problem-solving. Takes two git commits (before/after a fix) and a problem description to create structured diagnostic exercises that teach technical anatomy, troubleshooting patterns, and systems thinking. Ideal for creating educational content from real-world debugging experiences.
license: MIT License - see LICENSE.txt
---

# Technical Diagnosis Exercise Generator

This skill generates interactive learning exercises from git commit histories. It transforms debugging sessions into structured diagnostic lessons that teach systems thinking and technical problem-solving.

## Overview

Given two git commits and a problem description, this skill creates:
- Symptom identification and reproduction steps
- Layer-by-layer technical anatomy breakdown
- "What broke vs. what didn't" analysis
- Interactive diagnostic questions
- Practice exercises for skill transfer

## Core Workflow

### Step 1: Gather Input Information

Collect three key pieces:

1. **Before commit** (broken state)
   - Commit hash or identifier
   - Access to the codebase at this commit
   
2. **After commit** (fixed state)
   - Commit hash or identifier
   - Access to the codebase at this commit

3. **Problem description**
   - What symptom did the user observe?
   - What environment/context triggered it?
   - What was the "aha moment" in understanding the issue?

**Example request format:**
```
Create a diagnosis exercise comparing commits abc123 and def456.
The problem: Flask app worked locally but broke in GitHub Codespaces
because URL generation didn't account for the proxy.
```

### Step 2: Analyze the Git Diff

Use git tools to extract the changes:

```bash
git diff <before-commit> <after-commit>
```

For each changed file, identify:
- **Changed lines**: What actually got modified?
- **Unchanged context**: What stayed the same around the changes?
- **File type**: Application code, config, infrastructure, etc.

**Analysis framework:**
- If changes are in application logic → likely a business logic fix
- If changes are in middleware/config → likely a systems integration fix
- If changes are in infrastructure → likely an environment/deployment fix
- If changes span multiple layers → likely a architectural understanding gap

### Step 3: Map the Technical Anatomy

Create a layer-by-layer map of the system involved. For each layer, document:

**For each layer:**
1. **What this layer does** (in 1-2 sentences)
2. **What's in this layer** (components, files, responsibilities)
3. **Whether it changed** (✅ unchanged, ⚠️ modified, 🔴 broken, 🆕 added)
4. **Why it did/didn't need to change**

**Common layer patterns:**

For web applications:
1. Application Logic Layer (routes, controllers, business logic)
2. Data Layer (database, models, queries)
3. Presentation Layer (templates, views, UI)
4. Network Layer (ports, protocols, proxies)
5. Infrastructure Layer (servers, containers, deployment)

For data processing:
1. Input Layer (data sources, parsing)
2. Transformation Layer (processing, computation)
3. Storage Layer (databases, files, caching)
4. Output Layer (formatting, export)

For APIs:
1. Request Layer (routing, authentication)
2. Business Logic Layer (processing, validation)
3. Integration Layer (external services, databases)
4. Response Layer (formatting, serialization)

**The pattern:** Always identify what DIDN'T break to highlight what DID by contrast.

### Step 4: Structure the Exercise

Create the exercise in this exact structure:

#### 1. The Symptom
**Format:**
```markdown
## The Symptom

[Concrete description of what the user experienced]

Locally: [what happened in working environment]
[Output, screenshots, or logs showing it working]

In [broken environment]: [what happened in broken environment]
[Output, screenshots, or logs showing it broken]

**Starting Question: [High-level diagnostic question]**
```

**Guidelines:**
- Make it visceral and concrete
- Include actual command output or error messages if available
- Lead with a open-ended question that frames the investigation

#### 2. Diagnostic Framework: [Name] Anatomy
**Format:**
```markdown
## Diagnostic Framework: [System Name] Anatomy

Let's map the journey of [primary entity: request/data/command] through the system,
identifying what's the same and what's different.

### Layer 1: [Layer Name] [Status Icon]

**What's here:**
- [Component/file 1]
- [Component/file 2]
- [Component/file 3]

**Why it didn't break:** [or "Why it broke:" or "What changed:"]
- [Reason 1]
- [Reason 2]

**Key insight:** [One-sentence takeaway about this layer]

---

[Repeat for each layer...]
```

**Status icons:**
- ✅ `(UNCHANGED)` - worked before and after
- ⚠️ `(CHANGED)` - modified as part of fix
- 🔴 `(BROKEN)` - the problem layer
- 🆕 `(NEW)` - added in the fix

#### 3. The Anatomical Fix
**Format:**
```markdown
## The Anatomical Fix

### What needs to change:

**1. [Change description]:**

```[language]
[Actual code from the after commit]
```

**What this does:**
- [Explanation point 1]
- [Explanation point 2]

**2. [Additional change if applicable]:**

[Repeat pattern...]
```

**Include:**
- The actual code from the fix
- Line-by-line explanation of what changed
- Why each change addresses the root cause
- Any configuration or setup changes

#### 4. Diagnosis Questions (for learners)
**Format:**
```markdown
## Diagnosis Questions (for learners)

### Question 1: Why didn't [unchanged system] break?
**Answer:** [Explain the reasoning]

### Question 2: [Diagnostic question about the failure]
**Answer:** [Explain the root cause]

### Question 3: What would break WITHOUT the fix?
- [Consequence 1]
- [Consequence 2]
- [Consequence 3]

### Question 4: What WOULDN'T break even without the fix?
- [Thing 1 that still works]
- [Thing 2 that still works]
```

**Question patterns:**
- "Why didn't X break?" → teaches understanding of what layer owns what
- "What would break without the fix?" → teaches impact analysis
- "What wouldn't break?" → teaches system boundaries
- "When would you see this symptom?" → teaches pattern recognition

#### 5. The Pattern: What This Teaches
**Format:**
```markdown
## The Pattern: What This Teaches

### Core Concepts:

1. **[Concept name]**
   - [Learning point]
   - [Learning point]

2. **[Concept name]**
   - [Learning point]

### Diagnostic Skill Building:

**When [this symptom pattern], ask:**
1. [Diagnostic question 1]
2. [Diagnostic question 2]
3. [Diagnostic question 3]
```

**Extract:**
- 2-3 transferable concepts from this specific fix
- A decision tree or question pattern for similar issues
- Mental models for systems thinking

#### 6. Practice Exercise
**Format:**
```markdown
## Practice Exercise

**Given this error:** "[New but related error message]"

**Walk through:**
1. Which layer is this happening in? ([Expected answer])
2. What's working? ([Expected answer])
3. What's the gap? ([Expected answer])
4. What information exists but isn't being used? ([Expected answer])
5. What's the minimal fix? ([Expected answer])
```

Create a similar-but-different scenario that tests the same diagnostic pattern.

### Step 5: Add Interactive Elements (Optional)

For enhanced interactivity, add sections like:

**Progressive Reveal Pattern:**
```markdown
<details>
<summary>🤔 Before reading on, try to answer: What layer would you investigate first?</summary>

[Provide the answer and reasoning after they've thought about it]
</details>
```

**Hypothesis Testing:**
```markdown
## Test Your Hypothesis

If you think the problem is in [Layer X], you would expect to see:
- ✅ [Observable thing 1]
- ✅ [Observable thing 2]
- ❌ But we actually see [contradictory evidence]

This rules out [Layer X]. Let's look at [Layer Y]...
```

**Common Misdiagnoses:**
```markdown
## Common Misdiagnoses

❌ **Misdiagnosis 1**: "It's a [wrong layer] problem"
- Why this seems right: [Surface evidence]
- Why this is wrong: [Counterevidence]

✅ **Correct diagnosis**: "It's a [right layer] problem"
- Key evidence: [What proves it]
```

### Step 6: Quality Check

Before finalizing, verify:

- [ ] Symptom is concrete and reproducible
- [ ] All layers of the system are identified
- [ ] Unchanged systems are explicitly called out (the "what didn't break" is as important as what did)
- [ ] The fix is explained mechanistically, not just shown
- [ ] Questions scaffold from observation → analysis → generalization
- [ ] Practice exercise tests the same pattern with different details
- [ ] Code snippets are actual code from the commits, not paraphrased
- [ ] The diagnostic thinking pattern is made explicit

## Key Principles

### Emphasize the Negative Space
The most powerful teaching comes from identifying what DIDN'T need to change:
- "Routes didn't break because they only match on path"
- "Database queries work because they don't care about network layer"
- "Templates render fine until they need to generate URLs"

This teaches layer boundaries and system decomposition.

### Teach Diagnosis, Not Just Solutions
The goal isn't "here's how to fix proxy issues" but "here's how to diagnose proxy issues":
- What evidence points to which layer?
- What can you rule out and why?
- What information exists but isn't being used?
- What's the minimal change that fixes the root cause?

### Make Mental Models Explicit
Pull out the transferable thinking:
- "Environments are layers, each with different knowledge"
- "When something works locally but not deployed, ask: what's the network path?"
- "Local vs. deployed isn't just location—it's network topology"

### Use Actual Code
Don't paraphrase the fix—show the actual diff:
```python
# Before
app = Flask(__name__)

# After  
from werkzeug.middleware.proxy_fix import ProxyFix
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
```

This grounds the learning in reality.

## Example Output Structure

See `references/example-proxy-exercise.md` for a complete example following this format.

## Customization Options

The user may want variations:

**Shorter format**: Skip "Common Misdiagnoses" and "Interactive Elements", focus on core anatomy
**Deeper format**: Add more diagnostic questions, multiple practice exercises
**Specific audience**: Adjust technical depth for beginners vs. experienced developers
**Different medium**: Format for video script, workshop handout, or documentation

Always ask what format would be most useful before generating.

## Anti-Patterns to Avoid

❌ **Don't**: Just show the diff without explaining the reasoning
✅ **Do**: Map the system layers and explain why each did/didn't need to change

❌ **Don't**: Assume the reader knows what a proxy is
✅ **Do**: Build from first principles (but concisely)

❌ **Don't**: Make it a tutorial on the fix itself
✅ **Do**: Make it a lesson in diagnostic thinking using this fix as the example

❌ **Don't**: Use vague descriptions like "the network layer changed"
✅ **Do**: Show the actual code/config that changed and explain mechanistically

❌ **Don't**: Overwhelm with every possible related concept
✅ **Do**: Focus on 2-3 core concepts that emerge from this specific case

## Usage Tips

**Best commit pairs:**
- Real debugging sessions where the fix was non-obvious
- Issues that span multiple system layers
- "Works locally but not in prod" type problems
- Fixes that required understanding system architecture

**Less ideal commit pairs:**
- Typo fixes or simple syntax errors
- Single-line obvious changes
- Changes without clear environmental context
- Refactoring without a clear "broken" state
