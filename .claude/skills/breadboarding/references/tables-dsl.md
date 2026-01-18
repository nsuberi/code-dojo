# Tables DSL Reference

All shaping artifacts are stored as markdown tables for machine parseability and human readability.

## Requirements Table

Capture requirements as they emerge during discussion.

```markdown
| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| R1 | Users must sign waiver before first purchase | Must | Confirmed | Legal requirement |
| R2 | Waiver can be signed at checkout or via email | Must | Confirmed | Two paths needed |
| R3 | Staff can resend waiver requests | Should | Open | From member profile? |
| R4 | Track waiver signing history | Should | Confirmed | For compliance |
```

**Priority values**: Must, Should, Could, Won't
**Status values**: Open, Confirmed, Deferred, Removed

## Shapes Table

Break project into discrete shapes with scope assessment.

```markdown
| Shape | Description | Scope | Dependencies |
|-------|-------------|-------|--------------|
| Checkout signing | Sign waiver during self-serve checkout | Small | Existing checkout |
| Email signing | Send waiver via email, sign on dedicated page | Medium | Email system |
| Member waivers tab | View/manage waivers from member profile | Small | Member profile |
| Needs attention panel | Dashboard showing unsigned members | Small | Overview page |
```

**Scope values**: Small (1-2 days), Medium (3-5 days), Large (1-2 weeks)

## Fit Analysis Table

Analyze how each shape fits existing system.

```markdown
| Shape | Existing Components | New Components | Integration Points |
|-------|---------------------|----------------|-------------------|
| Checkout signing | Checkout page, Member model | WaiverSignatures table, signWaiver() | Checkout flow after payment |
| Email signing | Email service, Member model | WaiverRequests table, signing page, token system | Triggered by POS purchase |
```

## Affordances Table (Bill of Materials)

Complete inventory of UI and code affordances per shape.

```markdown
### Shape: Checkout signing

| ID | Type | Name | Description | Place |
|----|------|------|-------------|-------|
| U1 | UI | waiver content | Displays waiver text | Checkout |
| U2 | UI | "Click to sign" button | Triggers signing action | Checkout |
| N1 | Code | WaiverSignatures | Table storing signed waivers | - |
| N3 | Code | member.waiverUpToDate | Boolean property on member | - |
| N5 | Code | signWaiver() | Records signature, updates member | - |
| N11 | Code | getWaiver() | Retrieves current waiver text | - |
| N12 | Code | getMemberWaiverStatus() | Checks if member needs to sign | - |
```

**Type values**: UI, Code
**Place**: Which PLACE this affordance appears in, or `-` for code-only

## Wiring Table

Document all connections between affordances.

```markdown
| From | To | Wire Type | Description |
|------|-----|-----------|-------------|
| N12 getMemberWaiverStatus() | U2 "Click to sign" button | shows | Show button if waiver needed |
| N11 getWaiver() | U1 waiver content | populates | Load waiver text into display |
| U2 "Click to sign" button | N5 signWaiver() | calls | User action triggers signing |
| N5 signWaiver() | N1 WaiverSignatures | writes | Record the signature |
| N5 signWaiver() | N3 member.waiverUpToDate | updates | Mark member as current |
```

**Wire Type values**:
- `calls` - UI triggers code action
- `populates` - Code provides data to UI
- `shows` - Code controls UI visibility
- `writes` - Code persists data
- `updates` - Code modifies state
- `reads` - Code retrieves data
- `triggers` - Event starts process
- `sends` - Delivers to external system

## Places Table

Inventory of all locations in the system.

```markdown
| Place | Status | Parent | Description |
|-------|--------|--------|-------------|
| Self-serve checkout | existing | - | Main checkout flow |
| Waiver request email | new | - | Email sent after POS purchase |
| Waiver signing page | new | - | Standalone page for email signing |
| Member profile: Waivers tab | new | Member profile | Tab showing waiver history |
| Overview: Needs Attention | new | Overview | Panel replacing latest sales |
```

**Status values**: existing, new, modified

## Triggers Table

Events that initiate flows (not places).

```markdown
| Trigger | Handler | Initiates | Conditions |
|---------|---------|-----------|------------|
| POS purchase | N7 onPOSPurchase() | Email signing flow | Member waiver not current |
| Daily cron | N15 checkExpiredWaivers() | Reminder emails | Waiver request > 7 days old |
```

## Combined Shape Document

For each shape, create a complete document:

```markdown
# Shape: [Name]

## Requirements
[Requirements table filtered to this shape]

## Fit Analysis
[Single row from fit table]

## Affordances
[Affordances table for this shape]

## Wiring Diagram
[ASCII breadboard]

## Wiring Table
[Wiring table for this shape]
```
