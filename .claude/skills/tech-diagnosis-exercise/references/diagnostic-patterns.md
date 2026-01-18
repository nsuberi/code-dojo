# Common Diagnostic Patterns

This reference provides reusable patterns for different types of technical issues. When creating a diagnosis exercise, identify which pattern(s) apply and adapt the structure accordingly.

## Pattern 1: Environment Difference ("Works Locally But Not in Prod")

**Symptom signature:**
- Code is identical
- Different behavior in different environments
- Often involves deployment, hosting, or infrastructure

**Layer structure:**
1. Application Code Layer ✅ (unchanged)
2. Runtime Environment Layer ⚠️ (changed)
3. Network Layer ⚠️ (changed)
4. Infrastructure Layer ⚠️ (changed)

**Key diagnostic questions:**
- What's different about the environment?
- What assumptions does the code make about its environment?
- What information is available in one environment but not the other?
- What intermediaries exist in one environment but not the other?

**Examples:**
- Proxy header handling (Flask ProxyFix)
- File path differences (absolute vs relative paths)
- Environment variable availability
- Port binding and firewalls
- SSL/TLS certificate validation

---

## Pattern 2: Configuration Mismatch

**Symptom signature:**
- Same code works in some contexts but not others
- Error messages reference missing or incorrect configuration
- Often involves third-party services or libraries

**Layer structure:**
1. Application Code Layer ✅ (unchanged)
2. Configuration Layer 🔴 (broken)
3. Integration Layer ⚠️ (affected)
4. External Service Layer ✅ (unchanged)

**Key diagnostic questions:**
- What configuration values does the code expect?
- Where do those values come from?
- Are they hardcoded, in files, or from environment?
- What happens if they're missing or wrong?

**Examples:**
- API keys and credentials
- Database connection strings
- Feature flags
- Region-specific settings

---

## Pattern 3: Data Format Mismatch

**Symptom signature:**
- Works with some data but fails with other data
- Parsing or validation errors
- Often involves external data sources or APIs

**Layer structure:**
1. Data Source Layer ⚠️ (changed)
2. Parsing Layer 🔴 (broken)
3. Validation Layer ⚠️ (may catch it)
4. Processing Layer ✅ (unchanged, if data reaches it)

**Key diagnostic questions:**
- What format does the code expect?
- What format is actually being provided?
- Where does the assumption about format come from?
- What edge cases wasn't the code handling?

**Examples:**
- Date format differences (MM/DD vs DD/MM)
- Character encoding (UTF-8 vs Latin-1)
- JSON vs XML
- Null vs empty string vs missing field

---

## Pattern 4: Dependency Version Conflict

**Symptom signature:**
- Code breaks after updating dependencies
- Works with old version, fails with new version
- Breaking API changes or deprecated features

**Layer structure:**
1. Application Code Layer 🔴 (using old API)
2. Dependency Interface Layer ⚠️ (changed)
3. Dependency Implementation Layer ⚠️ (changed)

**Key diagnostic questions:**
- What changed in the dependency?
- What API is the code using?
- Is there a deprecation warning or migration guide?
- What's the new way to do the same thing?

**Examples:**
- Library function renamed or signature changed
- Deprecated parameter removed
- Return type changed
- Default behavior changed

---

## Pattern 5: Race Condition / Timing Issue

**Symptom signature:**
- Works sometimes, fails other times
- Often related to concurrent operations
- Hard to reproduce consistently

**Layer structure:**
1. Initiation Layer ✅ (starts operations)
2. Coordination Layer 🔴 (missing or broken)
3. Concurrent Operations Layer ⚠️ (racing)
4. Completion Layer ⚠️ (sees inconsistent state)

**Key diagnostic questions:**
- What operations are happening concurrently?
- What assumptions does the code make about ordering?
- What synchronization mechanisms exist (or don't)?
- What state is being shared?

**Examples:**
- File access conflicts
- Database transaction isolation
- Async/await misuse
- Cache invalidation

---

## Pattern 6: Resource Exhaustion

**Symptom signature:**
- Works initially, degrades or fails over time
- Memory leaks, connection pool exhaustion
- Performance degrades before failure

**Layer structure:**
1. Request Layer ✅ (unchanged)
2. Resource Allocation Layer 🔴 (leaking)
3. Resource Pool Layer ⚠️ (depleted)
4. Resource Cleanup Layer 🔴 (missing or broken)

**Key diagnostic questions:**
- What resources are being allocated?
- Are they being properly released?
- Is there a limit on available resources?
- What happens when the limit is reached?

**Examples:**
- Database connections not closed
- File handles not released
- Memory not freed
- Thread pool exhaustion

---

## Pattern 7: Authentication/Authorization Boundary

**Symptom signature:**
- Works for some users, fails for others
- Permission or access errors
- Often involves role-based or attribute-based access

**Layer structure:**
1. Request Layer ✅ (arrives)
2. Authentication Layer ⚠️ (who are you?)
3. Authorization Layer 🔴 (what can you do?)
4. Resource Access Layer ⚠️ (protected resource)

**Key diagnostic questions:**
- Who is making the request?
- What permissions do they have?
- What permissions does the operation require?
- Where is the permission check happening (or not happening)?

**Examples:**
- Missing authentication token
- Token expired
- Insufficient privileges
- Resource ownership check

---

## Pattern 8: State Management Issue

**Symptom signature:**
- Works on first try, fails on subsequent tries
- State persists when it shouldn't (or doesn't when it should)
- Often involves caching or sessions

**Layer structure:**
1. Request Layer ✅ (unchanged)
2. State Lookup Layer 🔴 (returning stale/wrong state)
3. State Storage Layer ⚠️ (cache/session/database)
4. Business Logic Layer ⚠️ (makes wrong decisions based on state)

**Key diagnostic questions:**
- What state is being stored?
- Where is it stored?
- When is it updated?
- When should it be invalidated?

**Examples:**
- Cache not invalidated after update
- Session state shared incorrectly
- Global variable pollution
- Browser cache serving stale content

---

## How to Use These Patterns

### Step 1: Identify the Pattern
Read the symptom description and match it to one or more patterns above.

### Step 2: Adapt the Layer Structure
Use the suggested layers as a starting point, but customize based on the actual system:
- Add layers specific to your technology stack
- Merge layers if they're tightly coupled
- Split layers if there are important distinctions

### Step 3: Apply the Diagnostic Questions
Use the pattern's questions as a template, but make them specific to the actual problem:
- Replace generic terms with specific technologies
- Add questions specific to the domain
- Order questions from observation to root cause

### Step 4: Emphasize the Negative Space
For each layer that DIDN'T break, explicitly explain why:
- What would have broken if the problem was in this layer?
- What evidence rules out this layer?
- What does this tell us about where the problem actually is?

### Step 5: Extract the Transferable Pattern
Once you've diagnosed this specific instance, generalize:
- What class of problems does this represent?
- What's the decision tree for diagnosing similar issues?
- What mental model should learners take away?

---

## Combining Patterns

Many real-world issues involve multiple patterns:

**Example: "OAuth callback fails in production"**
- Pattern 1 (Environment Difference): Redirect URL differs between local and prod
- Pattern 2 (Configuration Mismatch): OAuth app configured with wrong callback URL
- Pattern 5 (Race Condition): Token validation sometimes fails due to clock skew

When multiple patterns apply, structure the exercise to reveal them progressively:
1. Start with the most obvious pattern
2. Show why that's not the complete answer
3. Reveal the additional pattern
4. Show how they interact

This teaches that real debugging often involves multiple layers of understanding.
