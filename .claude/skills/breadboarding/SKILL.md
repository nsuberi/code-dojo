---
name: breadboarding
description: "Technical shaping and breadboarding for software projects using Ryan Singer's methodology. Use when users need to: (1) Shape a feature or project before implementation, (2) Create breadboards showing places, affordances, and wiring, (3) Map UI affordances to code affordances, (4) Document requirements and fit analysis, (5) Generate wiring diagrams showing data flow between components. Triggers include phrases like 'breadboard this', 'shape this feature', 'what are the affordances', 'wire up', 'technical shaping', or any request to plan/design a feature before building it."
---

# Breadboarding Skill

Technical shaping methodology that mirrors hardware design: rough concept → component selection → bill of materials → wiring.

## Importing from Markdown Sketches

Users may provide rough markdown sketches as input. Parse them as follows:

**Headers (`#`, `##`, `###`)** → Places or Triggers
- `# Place Name` or `## Place Name` → `PLACE: Place Name`
- Headers containing "trigger", "event", "when", "on" → `TRIGGER: ...`

**List items (`-`, `*`, `1.`)** → Raw affordances to classify
- Items with verbs (get, set, create, validate, send) → likely Code Affordance (N)
- Items in quotes or describing visible elements → likely UI Affordance (U)
- Items describing data/models → Code Affordance (N)

**Nested lists** → Suggest wiring relationships (parent triggers/populates child)

### Import Workflow

1. **Parse the markdown** into places and raw affordances
2. **Classify each affordance** as U (user-facing) or N (code/system)
3. **Assign IDs** (U1, U2... N1, N2...)
4. **Infer wiring** from nesting, naming patterns, and logical flow
5. **Ask clarifying questions** about ambiguous items
6. **Output full breadboard** with tables and diagrams

### Example Import

Input markdown:
```markdown
## Checkout Page
- waiver content display
- "Click to sign" button
- getMemberWaiverStatus()
- getWaiver()
- signWaiver()
  - WaiverSignatures table
  - member.waiverUpToDate
```

Parsed output:
- PLACE: Checkout Page (infer: existing or new?)
- U1: waiver content display (UI - it's a "display")
- U2: "Click to sign" button (UI - in quotes, is a button)
- N1: getMemberWaiverStatus() (Code - has parentheses, verb)
- N2: getWaiver() (Code - function)
- N3: signWaiver() (Code - function)
- N4: WaiverSignatures (Code - nested under signWaiver, is a table/model)
- N5: member.waiverUpToDate (Code - property, nested = updated by signWaiver)

Inferred wiring from nesting:
- N3 signWaiver() → N4 WaiverSignatures (writes)
- N3 signWaiver() → N5 member.waiverUpToDate (updates)

## Core Concepts

**Breadboard**: A schematic showing places, affordances, and connections—without visual design. Tests if the concept works before building.

**Place**: A location in the UI (page, screen, modal, email, panel). Named descriptively with status: `PLACE: Checkout page (existing)` or `PLACE: Waiver email (new)`.

**Affordance**: Something a user or system can interact with.
- **UI Affordance (U)**: Button, field, link, display element. What users see/click.
- **Code Affordance (N)**: Function, API endpoint, model, property. What the system does.

**Wire**: A connection showing data flow between affordances. Uses `→` for direction.

**Trigger**: An event that starts a flow (not a place). Example: `TRIGGER: POS purchase`.

## Shaping Workflow

### 1. Gather Requirements
Start with iterative requirements discussion:
- "What problem are we solving?"
- "Do we need to...?"
- "What about...?"
- "What's the happy path?"
- "What are the edge cases?"

Store requirements in a table as they emerge.

### 2. Identify Shapes (Features/Flows)
Break the project into discrete shapes—each a coherent piece of functionality. Give each shape a name and one-sentence description.

### 3. Analyze Fit
For each shape, analyze:
- Does it fit the existing system?
- What existing components can we reuse?
- What's new vs. modified?

### 4. List Affordances (Bill of Materials)
For each shape, enumerate:
- **UI affordances**: Every button, field, display, link
- **Code affordances**: Every function, endpoint, model, property

Use the naming convention:
- `U1`, `U2`, etc. for UI affordances
- `N1`, `N2`, etc. for code affordances

### 5. Wire the Breadboard
Connect affordances with wires showing:
- What calls what
- What data flows where
- What updates what

### 6. Document in Tables
Store everything in markdown tables. See [references/tables-dsl.md](references/tables-dsl.md) for table formats.

## Breadboard DSL Format

```
┌─ PLACE: [Name] ([status]) ─────────────────────────┐
│                                                     │
│  N[#] functionName()                                │
│      └─→ U[#] element name ←─ N[#] otherFunc()     │
│      └─→ U[#] "button text" ─→ N[#] handler()      │
│                                 └─→ N[#] Model     │
│                                 └─→ N[#] property  │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─ TRIGGER: [Event name] ────────────────────────────┐
│                                                     │
│  N[#] onEventHandler()                              │
│      └─→ N[#] doSomething()                         │
│          └─→ ...                                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Generating Breadboards

When asked to breadboard a feature:

1. **Clarify scope** with 2-3 targeted questions about requirements
2. **Create requirements table** capturing what emerged
3. **Identify shapes** and their relationships
4. **Create affordances table** with both U and N items
5. **Draw wiring diagram** showing connections
6. **Create wiring table** documenting all connections

Always output both human-readable diagrams AND machine-parseable tables.

## Quick Reference

| Element | Prefix | Examples |
|---------|--------|----------|
| UI Affordance | U | U1 "Submit" button, U2 email field, U3 status display |
| Code Affordance | N | N1 submitForm(), N2 validateEmail(), N3 UserModel |
| Place | PLACE: | PLACE: Login page (new) |
| Trigger | TRIGGER: | TRIGGER: Form submission |
| Wire | → | U1 → N1 → N2 |

## References

- **[tables-dsl.md](references/tables-dsl.md)**: Complete table formats for requirements, shapes, affordances, fit analysis, and wiring
- **[examples.md](references/examples.md)**: Full worked examples of breadboards
- **[implementation-plan.md](references/implementation-plan.md)**: Format for Claude Code-ready implementation plans

## Producing Implementation Plans for Claude Code

The final output of shaping should be a plan that Claude Code can execute independently. This requires translating breadboards into actionable implementation artifacts.

### Implementation Plan Structure

For each shape, produce:

1. **File manifest** - What files to create/modify
2. **Data models** - Schema for any N affordances that are models/tables
3. **Function signatures** - Interface for each N affordance that's a function
4. **Component specs** - For each U affordance, what it renders and its props
5. **Wiring as code** - How components connect (event handlers, data fetching)
6. **Acceptance criteria** - How to verify each wire works

### From Breadboard to Code Plan

| Breadboard Element | Implementation Artifact |
|-------------------|------------------------|
| PLACE (new) | New file/component to create |
| PLACE (existing) | File to modify, locate by name |
| U affordance | React component, HTML element, or UI state |
| N affordance (function) | Function signature with inputs/outputs |
| N affordance (model) | Database table or type definition |
| N affordance (property) | Field on a model, derived or stored |
| Wire (calls) | Event handler or function invocation |
| Wire (populates) | Data fetch + state/props |
| Wire (writes) | Database insert/update |
| Wire (updates) | State mutation or model update |

### Output Format for Claude Code

```markdown
# Implementation Plan: [Shape Name]

## Overview
[One paragraph describing what this shape accomplishes]

## Files to Create
- `path/to/new/file.ts` - [purpose]

## Files to Modify  
- `path/to/existing/file.ts` - [what changes]

## Data Models

### [ModelName]
```typescript
interface ModelName {
  id: string;
  field1: type;
  field2: type;
  // ... from N affordances that are models
}
```

## Functions to Implement

### N[#] functionName()
- **Purpose**: [from wiring - what triggers it, what it does]
- **Inputs**: [inferred from wires in]
- **Outputs**: [inferred from wires out]
- **Side effects**: [writes, updates from wiring table]

## UI Components

### U[#] componentName
- **Renders**: [what the user sees]
- **Props/State**: [data from N affordances that populate it]
- **Events**: [wires out to N affordances]

## Wiring Implementation

### [Wire description]
```typescript
// Pseudocode showing how the wire is implemented
// e.g., onClick handler calling function, useEffect fetching data
```

## Acceptance Criteria
- [ ] [Testable criterion derived from each wire]
```

### Execution Guidance for Claude Code

When Claude Code receives this plan:

1. **Start with models** - Create data structures first
2. **Implement N affordances** - Functions that don't depend on UI
3. **Create U affordances** - Components that render data
4. **Wire them together** - Event handlers and data flow
5. **Verify each wire** - Test against acceptance criteria

Include in the plan:
- Specific file paths (suggest based on project conventions)
- Import statements needed
- Error handling patterns
- Loading/empty states for U affordances
