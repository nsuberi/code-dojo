# Breadboard Examples

## Example: Importing a Markdown Sketch

User provides this rough markdown:

```markdown
# Self-serve checkout
- getMemberWaiverStatus()
- "Click to sign" button
- signWaiver()
- getWaiver()
  - waiver content

# POS purchase trigger
- onPOSPurchase()
- sendWaiverEmail()
  - generateSigningToken()
  - email content
- WaiverRequests

# Waiver request email
- email content  
- signing link

# Waiver signing page
- validateSigningToken(token)
- waiver content
- "Click to sign" button
- signWaiver()
  - WaiverSignatures
  - member.waiverUpToDate

# Member profile: Waivers tab
- getMemberWaiverStatus() → signed status
- getMemberWaiverHistory() → history list
- "Re-send waiver" button
  - resendWaiverRequest()

# Overview: Needs Attention panel
- getMembersNeedingWaiver() → unsigned members list
```

### Step 1: Parse and Classify

| Raw Item | Classification | ID | Reasoning |
|----------|---------------|-----|-----------|
| getMemberWaiverStatus() | Code | N12 | Has (), verb "get" |
| "Click to sign" button | UI | U2 | In quotes, "button" |
| signWaiver() | Code | N5 | Has (), verb "sign" |
| getWaiver() | Code | N11 | Has (), verb "get" |
| waiver content | UI | U1 | Display element |
| onPOSPurchase() | Code | N7 | Has (), "on" prefix = handler |
| sendWaiverEmail() | Code | N6 | Has (), verb "send" |
| generateSigningToken() | Code | N13 | Has (), verb "generate" |
| email content | UI | U3 | Display element |
| WaiverRequests | Code | N2 | PascalCase = model/table |
| signing link | UI | U4 | "link" = UI element |
| validateSigningToken() | Code | N14 | Has (), verb "validate" |
| WaiverSignatures | Code | N1 | PascalCase = model/table |
| member.waiverUpToDate | Code | N3 | dot notation = property |
| signed status | UI | U7 | Display element |
| getMemberWaiverHistory() | Code | N9 | Has (), verb "get" |
| history list | UI | U8 | Display element |
| "Re-send waiver" button | UI | U9 | In quotes, "button" |
| resendWaiverRequest() | Code | N10 | Has (), verb "resend" |
| getMembersNeedingWaiver() | Code | N8 | Has (), verb "get" |
| unsigned members list | UI | U10 | Display element |

### Step 2: Infer Wiring from Nesting and Arrows

From the markdown structure:
- `getWaiver()` nested under shows `waiver content` → N11 populates U1
- `signWaiver()` with nested `WaiverSignatures` → N5 writes N1
- `signWaiver()` with nested `member.waiverUpToDate` → N5 updates N3
- `getMemberWaiverStatus() → signed status` (arrow in text) → N12 populates U7
- `getMemberWaiverHistory() → history list` → N9 populates U8
- `getMembersNeedingWaiver() → unsigned members list` → N8 populates U10

### Step 3: Ask Clarifying Questions

Before completing the breadboard:
1. "Is Self-serve checkout existing or new?"
2. "Does the POS purchase trigger only fire for members without current waivers?"
3. "What determines if a waiver is 'current' - version number, date, or both?"
4. "Should the Needs Attention panel link to member profiles?"

### Step 4: Output Complete Breadboard

(See full example below)

---

## Example: Member Waiver System

A gym needs members to sign liability waivers. Waivers can be signed at self-serve checkout or via email link.

### Requirements Table

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| R1 | Members must sign waiver before purchasing | Must | Confirmed |
| R2 | Support signing at checkout kiosk | Must | Confirmed |
| R3 | Support signing via emailed link | Must | Confirmed |
| R4 | Staff can resend waiver requests | Should | Confirmed |
| R5 | Staff can view member waiver history | Should | Confirmed |
| R6 | Dashboard shows members needing waivers | Should | Confirmed |

### Shapes Table

| Shape | Description | Scope |
|-------|-------------|-------|
| Checkout signing | Sign waiver during self-serve checkout | Small |
| POS email flow | Trigger waiver email after POS purchase | Small |
| Email signing | Dedicated page for signing via email link | Medium |
| Member waivers tab | View/resend waivers from member profile | Small |
| Needs attention panel | Dashboard of unsigned members | Small |

### Affordances Table

| ID | Type | Name | Shape | Place |
|----|------|------|-------|-------|
| U1 | UI | waiver content | Checkout signing | Self-serve checkout |
| U2 | UI | "Click to sign" button | Checkout signing | Self-serve checkout |
| U3 | UI | email content | POS email flow | Waiver request email |
| U4 | UI | signing link | POS email flow | Waiver request email |
| U5 | UI | waiver content | Email signing | Waiver signing page |
| U6 | UI | "Click to sign" button | Email signing | Waiver signing page |
| U7 | UI | signed status | Member waivers tab | Member profile |
| U8 | UI | history list | Member waivers tab | Member profile |
| U9 | UI | "Re-send waiver" button | Member waivers tab | Member profile |
| U10 | UI | unsigned members list | Needs attention | Overview |
| N1 | Code | WaiverSignatures | - | - |
| N2 | Code | WaiverRequests | - | - |
| N3 | Code | member.waiverUpToDate | - | - |
| N5 | Code | signWaiver() | - | - |
| N6 | Code | sendWaiverEmail() | - | - |
| N7 | Code | onPOSPurchase() | - | - |
| N8 | Code | getMembersNeedingWaiver() | - | - |
| N9 | Code | getMemberWaiverHistory() | - | - |
| N10 | Code | resendWaiverRequest() | - | - |
| N11 | Code | getWaiver() | - | - |
| N12 | Code | getMemberWaiverStatus() | - | - |
| N13 | Code | generateSigningToken() | - | - |
| N14 | Code | validateSigningToken() | - | - |

### Wiring Diagram

```
┌─ PLACE: Self-serve checkout (existing) ────────────────────────────┐
│                                                                     │
│  N12 getMemberWaiverStatus()                                        │
│      └─→ U2 "Click to sign" button ─→ N5 signWaiver()              │
│                                        └─→ N1 WaiverSignatures     │
│  N11 getWaiver()                       └─→ N3 member.waiverUpToDate│
│      └─→ U1 waiver content                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─ TRIGGER: POS purchase ────────────────────────────────────────────┐
│                                                                     │
│  N7 onPOSPurchase()                                                 │
│      └─→ N6 sendWaiverEmail()                                       │
│          └─→ N13 generateSigningToken()                             │
│          └─→ U3 email content                                       │
│      └─→ N2 WaiverRequests                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─ PLACE: Waiver request email (new) ────────────────────────────────┐
│                                                                     │
│  U3 email content                                                   │
│                                                                     │
│  U4 signing link ──────────────────────────────────────────────────┼──┐
│                                                                     │  │
└─────────────────────────────────────────────────────────────────────┘  │
                                                                         │
                                    ┌────────────────────────────────────┘
                                    ▼
┌─ PLACE: Waiver signing page (new) ─────────────────────────────────┐
│                                                                     │
│  N14 validateSigningToken(token)                                    │
│      └─→ U5 waiver content ←── N11 getWaiver()                     │
│      └─→ U6 "Click to sign" button ─→ N5 signWaiver()              │
│                                       └─→ N1 WaiverSignatures      │
│                                       └─→ N3 member.waiverUpToDate │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─ PLACE: Member profile: Waivers tab (new tab, existing page) ──────┐
│                                                                     │
│  N12 getMemberWaiverStatus() ─→ U7 signed status                   │
│                                                                     │
│  N9 getMemberWaiverHistory() ─→ U8 history list                    │
│                                                                     │
│  ~U9 "Re-send waiver" button                                        │
│      └─→ ~N10 resendWaiverRequest()                                 │
│          └─→ N6 sendWaiverEmail() ─→ U3 (email)                    │
│          └─→ N2 WaiverRequests                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─ PLACE: Overview: Needs Attention (new panel, replaces latest sales)┐
│                                                                      │
│  N8 getMembersNeedingWaiver() ─→ U10 unsigned members list          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

Note: `~` prefix indicates conditional/optional elements.

### Wiring Table

| From | To | Wire Type | Description |
|------|-----|-----------|-------------|
| N12 getMemberWaiverStatus() | U2 "Click to sign" button | shows | Show if waiver needed |
| N11 getWaiver() | U1 waiver content | populates | Load waiver text |
| U2 "Click to sign" button | N5 signWaiver() | calls | Trigger signing |
| N5 signWaiver() | N1 WaiverSignatures | writes | Record signature |
| N5 signWaiver() | N3 member.waiverUpToDate | updates | Mark current |
| N7 onPOSPurchase() | N6 sendWaiverEmail() | calls | Start email flow |
| N6 sendWaiverEmail() | N13 generateSigningToken() | calls | Create secure token |
| N6 sendWaiverEmail() | U3 email content | sends | Deliver email |
| N7 onPOSPurchase() | N2 WaiverRequests | writes | Log request |
| U4 signing link | N14 validateSigningToken() | calls | Validate on click |
| N14 validateSigningToken() | U5 waiver content | shows | Show page if valid |
| N11 getWaiver() | U5 waiver content | populates | Load waiver text |
| U6 "Click to sign" button | N5 signWaiver() | calls | Trigger signing |
| N12 getMemberWaiverStatus() | U7 signed status | populates | Show status |
| N9 getMemberWaiverHistory() | U8 history list | populates | Show history |
| U9 "Re-send waiver" button | N10 resendWaiverRequest() | calls | Trigger resend |
| N10 resendWaiverRequest() | N6 sendWaiverEmail() | calls | Send email |
| N10 resendWaiverRequest() | N2 WaiverRequests | writes | Log request |
| N8 getMembersNeedingWaiver() | U10 unsigned members list | populates | Show list |

---

## Example: Simple Login Shape

Minimal example showing a single shape.

### Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| R1 | Users can log in with email/password | Must | Confirmed |
| R2 | Show error on invalid credentials | Must | Confirmed |

### Affordances

| ID | Type | Name | Description |
|----|------|------|-------------|
| U1 | UI | email field | Input for email address |
| U2 | UI | password field | Input for password |
| U3 | UI | "Log in" button | Submits credentials |
| U4 | UI | error message | Shows validation errors |
| N1 | Code | authenticateUser() | Validates credentials |
| N2 | Code | createSession() | Creates auth session |
| N3 | Code | Sessions | Session storage |

### Wiring Diagram

```
┌─ PLACE: Login page (new) ──────────────────────────────────────────┐
│                                                                     │
│  U1 email field ─────┐                                              │
│                      ├─→ U3 "Log in" button ─→ N1 authenticateUser()│
│  U2 password field ──┘                        │                     │
│                                               ├─→ N2 createSession()│
│                                               │   └─→ N3 Sessions   │
│                                               │                     │
│  U4 error message ←───────────────────────────┘                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Example: Implementation Plan Output

Taking the Checkout Signing shape from the waiver system, here's the implementation plan for Claude Code:

```markdown
# Implementation Plan: Checkout Signing

## Overview

Allow members to sign liability waivers during self-serve checkout. Members who haven't signed the current waiver version will see the waiver text and a sign button before completing checkout.

## Prerequisites

- [ ] Existing Checkout page component at `src/pages/Checkout.tsx`
- [ ] Existing Member model with member authentication
- [ ] Database supporting Prisma migrations

## Files

### Create
| File | Purpose |
|------|---------|
| `prisma/migrations/xxx_add_waivers/migration.sql` | Add waiver tables |
| `src/models/waiver.ts` | Waiver and WaiverSignature types |
| `src/api/waivers/getWaiver.ts` | N11 - Fetch waiver content |
| `src/api/waivers/getMemberWaiverStatus.ts` | N12 - Check if signing needed |
| `src/api/waivers/signWaiver.ts` | N5 - Record signature |
| `src/components/checkout/WaiverStep.tsx` | Container for waiver UI |
| `src/components/checkout/WaiverContent.tsx` | U1 - Display waiver text |
| `src/components/checkout/SignWaiverButton.tsx` | U2 - Sign button |

### Modify
| File | Changes |
|------|---------|
| `prisma/schema.prisma` | Add Waiver, WaiverSignature models; add fields to Member |
| `src/pages/Checkout.tsx` | Add WaiverStep before payment |

## Data Models

### N1 WaiverSignatures

Add to prisma/schema.prisma:

model WaiverSignature {
  id        String   @id @default(cuid())
  memberId  String
  member    Member   @relation(fields: [memberId], references: [id])
  waiverId  String
  waiver    Waiver   @relation(fields: [waiverId], references: [id])
  signedAt  DateTime @default(now())
  ipAddress String?
  
  @@index([memberId])
  @@index([waiverId])
}

model Waiver {
  id         String   @id @default(cuid())
  title      String
  content    String   @db.Text
  version    String
  isActive   Boolean  @default(true)
  createdAt  DateTime @default(now())
  signatures WaiverSignature[]
  
  @@unique([version])
}

### N3 member.waiverUpToDate

Add to existing Member model:

model Member {
  // ... existing fields
  waiverUpToDate    Boolean  @default(false)
  waiverSignedAt    DateTime?
  waiverSignatures  WaiverSignature[]
}

## Functions

### N11 getWaiver()

// src/api/waivers/getWaiver.ts
export async function getWaiver(waiverId?: string) {
  // If no waiverId, get current active waiver
  // Return { id, title, content, version }
}

### N12 getMemberWaiverStatus()

// src/api/waivers/getMemberWaiverStatus.ts  
export async function getMemberWaiverStatus(memberId: string) {
  // Get current active waiver
  // Check if member has signed this version
  // Return { needsSignature, currentWaiverId, lastSignedAt?, lastSignedVersion? }
}

### N5 signWaiver()

// src/api/waivers/signWaiver.ts
export async function signWaiver(input: {
  memberId: string;
  waiverId: string;
  ipAddress?: string;
}) {
  // In transaction:
  // 1. Create WaiverSignature record
  // 2. Update member.waiverUpToDate = true
  // 3. Update member.waiverSignedAt = now()
  // Return { success, signature }
}

## UI Components

### U1 WaiverContent

// src/components/checkout/WaiverContent.tsx
// Props: { waiver: { title, content, version }, isLoading }
// Renders: Scrollable container with title and HTML/markdown content
// States: Loading skeleton, Loaded, Error

### U2 SignWaiverButton  

// src/components/checkout/SignWaiverButton.tsx
// Props: { onSign: () => Promise<void>, isLoading, disabled }
// Renders: Primary button "I Agree and Sign"
// States: Default, Hover, Loading (spinner), Disabled, Success (checkmark)

## Wiring

### Checkout.tsx integration

// Add to checkout flow, before payment step:
const { data: waiverStatus, isLoading: statusLoading } = 
  useWaiverStatus(member.id);

// Only fetch waiver if needed
const { data: waiver, isLoading: waiverLoading } = 
  useWaiver(waiverStatus?.currentWaiverId, {
    enabled: waiverStatus?.needsSignature
  });

const signMutation = useSignWaiver();

// In render, before payment:
{waiverStatus?.needsSignature && (
  <WaiverStep
    waiver={waiver}
    isLoading={waiverLoading}
    onSign={() => signMutation.mutateAsync({
      memberId: member.id,
      waiverId: waiver.id
    })}
    isSigning={signMutation.isLoading}
  />
)}

## Acceptance Criteria

- [ ] New member at checkout sees waiver content
- [ ] Waiver displays title, full content, version number
- [ ] Sign button is visible below waiver content
- [ ] Clicking sign shows loading state
- [ ] After signing: WaiverSignature record created with correct data
- [ ] After signing: member.waiverUpToDate = true
- [ ] After signing: checkout proceeds to payment
- [ ] Returning member with current signature skips waiver step
- [ ] Error message shown if signing fails
- [ ] Waiver step not shown if no active waiver exists

## Implementation Order

1. Schema changes + migration
2. getWaiver() + test
3. getMemberWaiverStatus() + test
4. signWaiver() + test
5. WaiverContent component + Storybook
6. SignWaiverButton component + Storybook
7. WaiverStep container component
8. Integrate into Checkout.tsx
9. E2E test
```
