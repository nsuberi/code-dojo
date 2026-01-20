## Impact Assessment Methodology

Comprehensive framework for assessing the scope, risk, and complexity of architectural changes in pull requests.

## Assessment Dimensions

### 1. Scope (Components Affected)

**Definition:** How many distinct architectural components are touched by the changes

**Scoring:**

| Level | Components | Description |
|-------|-----------|-------------|
| **Low** | 1-2 | Changes isolated to one or two components |
| **Medium** | 3-5 | Changes span several components |
| **High** | 6+ | Changes affect many components or cross-cutting concerns |

**How to count components:**
- **High granularity:** System-level components (Auth System, API, Data Layer)
- **Medium granularity:** Modules/services (auth.users, api.orders)
- **Low granularity:** Major code areas affected (authentication logic, user endpoints)

**Examples:**

**Low Scope:**
```
Changes: Update logging in UserService
Components affected: 1 (UserService)
Scope: Low
```

**Medium Scope:**
```
Changes: Add OAuth support
Components affected: 4 (Auth, API Gateway, User Service, Database)
Scope: Medium
```

**High Scope:**
```
Changes: Migrate from REST to GraphQL
Components affected: 12 (All API endpoints, Frontend, Mobile app, etc.)
Scope: High
```

### 2. Risk (Breaking Change Potential)

**Definition:** Likelihood and severity of breaking changes or incompatible modifications

**Scoring:**

| Level | Characteristics | Examples |
|-------|----------------|----------|
| **Low** | - Internal refactoring only<br>- No public API changes<br>- Backward compatible<br>- Safe rollback | - Code reorganization<br>- Performance optimization<br>- Bug fixes<br>- Internal helper functions |
| **Medium** | - API changes with backward compatibility<br>- New optional fields<br>- Deprecated (not removed) endpoints<br>- Requires coordination | - Add optional API parameter<br>- Add new endpoint<br>- Deprecation warnings<br>- Database column addition (nullable) |
| **High** | - Breaking API changes<br>- Removed endpoints/functions<br>- Incompatible schema changes<br>- Changed behavior | - Remove API endpoint<br>- Required field added<br>- Drop database column<br>- Changed authentication flow |

**Risk indicators:**

**Breaking changes:**
- ❌ API endpoint removed
- ❌ Required parameter added to existing endpoint
- ❌ Response schema incompatibly changed
- ❌ Database column dropped
- ❌ Database column type changed incompatibly
- ❌ Function signature changed (different parameters)
- ❌ Removed public class/method

**Non-breaking but requires coordination:**
- ⚠️ New required environment variable
- ⚠️ Database migration (even if additive)
- ⚠️ New external service dependency
- ⚠️ Changed authentication mechanism
- ⚠️ Modified data validation rules

**Safe changes:**
- ✅ New API endpoint (additive)
- ✅ New optional parameters
- ✅ Internal refactoring
- ✅ Performance improvements
- ✅ Bug fixes that don't change behavior
- ✅ Additional response fields (additive)

### 3. Complexity (Code Volume)

**Definition:** Amount of code changed, measuring implementation size

**Scoring:**

| Level | Lines Changed | Files Changed | Description |
|-------|--------------|---------------|-------------|
| **Low** | <100 | <5 | Small, focused change |
| **Medium** | 100-500 | 5-15 | Moderate-sized change |
| **High** | >500 | >15 | Large, extensive change |

**Adjustments:**

**Reduce complexity score if:**
- Generated code (protobuf, GraphQL schemas)
- Test files (count at 50% weight)
- Documentation files (don't count toward complexity)
- Configuration files (simple changes)

**Increase complexity score if:**
- Core business logic changes
- Security-sensitive code
- Performance-critical paths
- Complex algorithms

**Examples:**

**Low Complexity:**
```
Files: 3
Lines: 45 added, 20 deleted (65 total)
Complexity: Low
```

**Medium Complexity:**
```
Files: 10 (8 source, 2 test)
Lines: 234 added, 89 deleted (323 total)
Complexity: Medium
```

**High Complexity:**
```
Files: 24 (18 source, 6 test)
Lines: 678 added, 234 deleted (912 total)
Complexity: High
```

## Overall Impact Matrix

Combine scope, risk, and complexity into overall assessment:

### Impact Calculation

**Critical factors:**
1. **Risk is primary:** High risk always elevates overall impact
2. **Scope amplifies risk:** High risk + High scope = Maximum concern
3. **Complexity is secondary:** Indicates review effort needed

### Impact Levels

**🔴 Critical Impact (Highest concern)**
- High risk + (High scope OR High complexity)
- Breaking changes affecting many components
- Large code changes in critical paths

**Examples:**
- Remove authentication endpoint used by mobile app
- Migrate all API endpoints to new framework
- Change core business logic across system

**Action required:**
- Thorough review by senior engineers
- Comprehensive testing strategy
- Phased rollout plan
- Rollback strategy documented
- Stakeholder coordination

---

**🟠 High Impact (Significant concern)**
- High risk + (Medium scope OR Medium complexity)
- Medium risk + High scope + High complexity
- Breaking changes in contained area

**Examples:**
- Add required field to API used by 3 services
- Database schema breaking change for one module
- Refactor authentication with behavior changes

**Action required:**
- Detailed review
- Integration testing
- Deployment coordination
- Communication with affected teams

---

**🟡 Medium Impact (Moderate concern)**
- Medium risk + Medium scope/complexity
- High risk + Low scope + Low complexity
- Low risk + High scope/complexity

**Examples:**
- Add new optional API parameter used by several services
- Large refactoring with backward compatibility
- Performance optimization affecting multiple modules

**Action required:**
- Standard review process
- Testing of affected areas
- Monitor after deployment

---

**🟢 Low Impact (Minimal concern)**
- Low risk + Low scope + Low complexity
- Internal changes only
- Well-isolated modifications

**Examples:**
- Fix bug in single function
- Update internal helper method
- Refactor code without behavior change

**Action required:**
- Normal code review
- Standard testing

## Decision Tree

```
START
 ├─ Contains breaking changes? (removed APIs, incompatible schemas)
 │   ├─ YES → High Risk
 │   └─ NO
 │       ├─ API changes with backward compatibility?
 │       │   ├─ YES → Medium Risk
 │       │   └─ NO → Low Risk
 │
 ├─ High Risk?
 │   ├─ YES
 │   │   ├─ Affects 6+ components OR 500+ lines?
 │   │   │   ├─ YES → 🔴 CRITICAL IMPACT
 │   │   │   └─ NO → 🟠 HIGH IMPACT
 │   └─ NO
 │       ├─ Medium Risk?
 │       │   ├─ YES
 │       │   │   ├─ Affects 3-5 components OR 100-500 lines?
 │       │   │   │   ├─ YES → 🟠 HIGH IMPACT
 │       │   │   │   └─ NO → 🟡 MEDIUM IMPACT
 │       │   └─ NO
 │       │       └─ 🟢 LOW IMPACT
```

## Detailed Analysis Guidelines

### Assessing API Changes

**For each changed endpoint, check:**

1. **Method changed?** (GET → POST) → Breaking
2. **Path changed?** (/v1/users → /v2/users) → Breaking if old removed
3. **Request schema:**
   - New required field → Breaking
   - New optional field → Non-breaking
   - Removed field → Potentially breaking (clients may send)
   - Field type changed → Breaking

4. **Response schema:**
   - Field removed → Breaking
   - Field type changed → Breaking
   - New field added → Non-breaking (clients ignore unknown)
   - Field made optional → Non-breaking

5. **Status codes:**
   - New error codes → Non-breaking
   - Changed error codes → Potentially breaking
   - New success codes → Review client handling

6. **Authentication:**
   - Added auth requirement → Breaking
   - Changed auth method → Breaking
   - Removed auth requirement → Non-breaking (but security concern)

### Assessing Database Changes

**For each schema change, check:**

1. **Table added** → Non-breaking
2. **Table removed** → Breaking (data loss)
3. **Table renamed** → Breaking (unless migration handled)

4. **Column added:**
   - Nullable → Non-breaking
   - NOT NULL with default → Non-breaking
   - NOT NULL without default → Breaking (existing rows fail)

5. **Column removed** → Breaking (data loss, code may reference)

6. **Column renamed** → Breaking (unless migration preserves)

7. **Column type changed:**
   - Compatible (VARCHAR(50) → VARCHAR(100)) → Non-breaking
   - Incompatible (VARCHAR → INT) → Breaking

8. **Constraint added:**
   - NOT NULL → Breaking if existing nulls
   - UNIQUE → Breaking if existing duplicates
   - FOREIGN KEY → Breaking if orphaned records
   - CHECK → Breaking if existing data violates

9. **Index added** → Non-breaking (performance improvement)

10. **Index removed** → Non-breaking (potential performance regression)

### Assessing Dependency Changes

**For each dependency change:**

1. **New dependency added:**
   - Risk: Low (unless untrusted or security issues)
   - Action: Review dependency licenses, security

2. **Dependency removed:**
   - Risk: Low if properly removed
   - Action: Verify no lingering references

3. **Dependency version changed:**
   - Patch update (1.2.3 → 1.2.4) → Low risk
   - Minor update (1.2.3 → 1.3.0) → Medium risk (check changelog)
   - Major update (1.2.3 → 2.0.0) → High risk (breaking changes expected)

4. **Dependency scope changed:**
   - Production → Dev → Risk reduction
   - Dev → Production → Check if needed
   - Added to global scope → Potential conflicts

## Special Considerations

### Security-Sensitive Changes

**Automatically elevate risk for changes to:**
- Authentication/authorization logic
- Cryptography implementations
- Input validation/sanitization
- Access control checks
- Session management
- Password handling
- Token generation/validation

**Even small changes (low complexity) in security areas should be:**
- Reviewed by security-aware engineers
- Tested thoroughly
- Monitored closely post-deployment

### Performance-Critical Changes

**Changes affecting:**
- Database queries in hot paths
- Caching logic
- API endpoints with high traffic
- Background job processing

**Assessment additions:**
- Performance impact (better/worse/neutral)
- Load testing requirements
- Monitoring strategy

### Data Integrity Changes

**Changes affecting:**
- Data validation rules
- Business logic constraints
- Data transformation pipelines
- Migration scripts

**Assessment additions:**
- Data correctness verification
- Rollback data strategy
- Data backup requirements

## Output Format

### Impact Assessment Summary

```markdown
## Impact Assessment

**Scope:** {Low|Medium|High} ({X} components affected)
**Risk:** {Low|Medium|High} ({Breaking|Non-breaking} changes)
**Complexity:** {Low|Medium|High} ({X} lines across {Y} files)

**Overall Impact:** {🟢 Low | 🟡 Medium | 🟠 High | 🔴 Critical}

### Risk Factors
{If High/Critical impact, list specific risk factors:}
- Breaking change: Removed endpoint `GET /api/legacy/users`
- Database schema change requires migration
- Affects mobile app authentication flow

### Recommended Actions
{Based on impact level, suggest:}
- [ ] Thorough code review by {team/person}
- [ ] Integration testing with {dependent services}
- [ ] Phased rollout strategy
- [ ] Monitor {specific metrics} post-deployment
- [ ] Coordinate with {teams} before merge
```

### Detailed Breakdown

```markdown
### Breaking Changes Detected

1. **API Endpoint Removed:** `GET /auth/legacy/user`
   - **Impact:** Mobile app (v1.2.x) uses this endpoint
   - **Risk:** High - app will break for users on old version
   - **Mitigation:** Deprecate first, remove in later version

2. **Database Column Dropped:** `users.legacy_login_method`
   - **Impact:** Data permanently lost
   - **Risk:** Medium - column not used in current code
   - **Mitigation:** Backup data before migration

### Coordination Required

- **Teams:** Mobile team, Frontend team
- **Reason:** Authentication flow changes affect all clients
- **Timeline:** Deploy backend first, then clients
- **Fallback:** Keep old auth endpoint for 2 weeks
```

## Assessment Workflow

1. **Analyze changed files:**
   - Count files, lines
   - Identify affected components
   - Calculate complexity score

2. **Check for breaking changes:**
   - Review API endpoint changes
   - Analyze database schema changes
   - Check dependency updates
   - Examine function signature changes

3. **Determine risk level:**
   - Apply breaking change detection
   - Consider backward compatibility
   - Assess rollback difficulty

4. **Calculate scope:**
   - Map changes to components
   - Count distinct components affected
   - Consider ripple effects

5. **Combine into overall impact:**
   - Use decision tree
   - Apply special considerations
   - Document reasoning

6. **Generate recommendations:**
   - Required actions for impact level
   - Specific mitigations for risks
   - Testing strategy
   - Deployment approach

## Calibration Examples

### Example 1: Simple Bug Fix

```
Files changed: 1
Lines: +5, -3
Components: 1 (UserService)
Breaking changes: None
Risk: Low
Scope: Low
Complexity: Low
Overall Impact: 🟢 Low
```

### Example 2: New Feature with API

```
Files changed: 8
Lines: +234, -45
Components: 3 (API, Auth, Database)
Breaking changes: None (all additive)
Risk: Medium (new API, requires testing)
Scope: Medium
Complexity: Medium
Overall Impact: 🟡 Medium
```

### Example 3: Breaking Change

```
Files changed: 15
Lines: +456, -234
Components: 6 (API, Auth, Frontend, Mobile, Database, Cache)
Breaking changes: Yes (removed endpoint, schema change)
Risk: High
Scope: High
Complexity: High
Overall Impact: 🔴 Critical
```

## Best Practices

✅ **DO:**
- Be objective in scoring
- Document reasoning for high/critical impacts
- Consider downstream effects
- Check for hidden breaking changes
- Provide specific mitigation strategies

❌ **DON'T:**
- Underestimate risk to avoid concern
- Ignore complexity in tests/docs
- Overlook transitive dependencies
- Skip coordination recommendations
- Use impact assessment as gate without context

## Integration with Analysis

The impact assessment should:
1. Be calculated after architectural analysis complete
2. Inform the executive summary prominence
3. Determine recommended follow-up actions
4. Guide deployment strategy recommendations
5. Help prioritize review focus areas

Use consistently across all analyses to build calibrated intuition for impact levels.
