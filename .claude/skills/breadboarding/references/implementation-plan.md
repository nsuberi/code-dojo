# Implementation Plan Reference

Templates and patterns for producing Claude Code-ready implementation plans from breadboards.

## Complete Implementation Plan Template

```markdown
# Implementation Plan: [Shape Name]

## Overview

[2-3 sentences: What user problem this solves, the key flow, and scope]

## Prerequisites

- [ ] [Existing code/infrastructure this depends on]
- [ ] [Environment or config requirements]

## Files

### Create
| File | Purpose |
|------|---------|
| `src/models/WaiverSignature.ts` | Data model for signed waivers |
| `src/api/signWaiver.ts` | Signing endpoint |
| `src/components/WaiverContent.tsx` | Display waiver text |

### Modify
| File | Changes |
|------|---------|
| `src/pages/Checkout.tsx` | Add waiver signing step |
| `src/models/Member.ts` | Add waiverUpToDate field |

## Data Models

### N1 WaiverSignatures

```typescript
// Database table / Prisma model
model WaiverSignature {
  id        String   @id @default(cuid())
  memberId  String
  member    Member   @relation(fields: [memberId], references: [id])
  waiverId  String
  signedAt  DateTime @default(now())
  ipAddress String?
  
  @@index([memberId])
}
```

### N3 member.waiverUpToDate

```typescript
// Add to existing Member model
model Member {
  // ... existing fields
  waiverUpToDate  Boolean @default(false)
  waiverSignedAt  DateTime?
}
```

## Functions

### N5 signWaiver()

```typescript
/**
 * Records a waiver signature and updates member status
 * 
 * Triggered by: U2 "Click to sign" button (calls)
 * Writes to: N1 WaiverSignatures
 * Updates: N3 member.waiverUpToDate
 */
async function signWaiver(input: {
  memberId: string;
  waiverId: string;
  ipAddress?: string;
}): Promise<{ success: boolean; signature: WaiverSignature }> {
  // 1. Create signature record
  // 2. Update member.waiverUpToDate = true
  // 3. Update member.waiverSignedAt = now
  // 4. Return result
}
```

### N11 getWaiver()

```typescript
/**
 * Retrieves current waiver text for display
 * 
 * Populates: U1 waiver content
 */
async function getWaiver(waiverId?: string): Promise<{
  id: string;
  title: string;
  content: string;
  version: string;
}> {
  // Return current active waiver, or specific version if waiverId provided
}
```

### N12 getMemberWaiverStatus()

```typescript
/**
 * Checks if member needs to sign waiver
 * 
 * Shows: U2 "Click to sign" button (if waiver needed)
 */
async function getMemberWaiverStatus(memberId: string): Promise<{
  needsSignature: boolean;
  currentWaiverId: string;
  lastSignedAt?: Date;
  lastSignedVersion?: string;
}> {
  // Compare member's last signature to current waiver version
}
```

## UI Components

### U1 waiver content

```typescript
/**
 * Displays waiver text for user to read before signing
 * 
 * Populated by: N11 getWaiver()
 */
interface WaiverContentProps {
  waiver: {
    title: string;
    content: string;  // May contain HTML/markdown
    version: string;
  };
  isLoading?: boolean;
}

// Render: Scrollable container with waiver text
// States: Loading, Loaded, Error
// Accessibility: Ensure readable, proper heading structure
```

### U2 "Click to sign" button

```typescript
/**
 * Button to submit waiver signature
 * 
 * Shown by: N12 getMemberWaiverStatus() (when needsSignature = true)
 * Calls: N5 signWaiver() on click
 */
interface SignButtonProps {
  onSign: () => Promise<void>;
  isLoading?: boolean;
  disabled?: boolean;  // Disable until waiver scrolled/read
}

// Render: Primary action button
// States: Default, Loading, Disabled, Success
// UX: Consider requiring scroll-to-bottom before enabling
```

## Wiring Implementation

### Wire: Page Load → Waiver Display

```typescript
// In Checkout page component
const { data: status } = useQuery(['waiverStatus', memberId], 
  () => getMemberWaiverStatus(memberId)
);

const { data: waiver } = useQuery(['waiver', status?.currentWaiverId],
  () => getWaiver(status?.currentWaiverId),
  { enabled: status?.needsSignature }
);

// Render U1 with waiver data
// Conditionally render U2 based on status.needsSignature
```

### Wire: Sign Button → signWaiver → Updates

```typescript
const signMutation = useMutation(signWaiver, {
  onSuccess: () => {
    // Invalidate queries to refresh status
    queryClient.invalidateQueries(['waiverStatus', memberId]);
    // Proceed to next checkout step
  }
});

// In U2 button:
<SignButton 
  onSign={() => signMutation.mutate({ 
    memberId, 
    waiverId: waiver.id 
  })}
  isLoading={signMutation.isLoading}
/>
```

## Acceptance Criteria

- [ ] Member without signed waiver sees waiver content on checkout
- [ ] Member can click "Sign" button after viewing waiver
- [ ] Clicking sign creates WaiverSignature record with correct memberId, waiverId
- [ ] After signing, member.waiverUpToDate is true
- [ ] After signing, sign button no longer appears
- [ ] Member with current signature skips waiver step
- [ ] Error state shown if signing fails
- [ ] Loading state shown while signing in progress

## Implementation Order

1. Add waiverUpToDate field to Member model, run migration
2. Create WaiverSignature model, run migration
3. Implement getWaiver() - can test independently
4. Implement getMemberWaiverStatus() - can test independently  
5. Implement signWaiver() - test with direct calls
6. Create WaiverContent component - test with mock data
7. Create SignButton component - test with mock handler
8. Integrate into Checkout page
9. End-to-end test full flow

## Notes for Claude Code

- Use existing auth context to get memberId
- Follow project patterns for API routes (check existing files)
- Use existing UI component library for button styling
- Check if there's an existing Waiver model to extend vs. create new
```

## Mapping Breadboard to Plan

### From Wiring Table to Implementation

| Wire Type | Implementation Pattern |
|-----------|----------------------|
| calls | Event handler: `onClick={() => functionName()}` |
| populates | Data fetch: `useQuery` or `useEffect` + state |
| shows | Conditional render: `{condition && <Component />}` |
| writes | Database insert in function body |
| updates | Database update or state mutation |
| reads | Database query in function body |
| triggers | Event listener or webhook handler |
| sends | API call or email service invocation |

### Complexity Estimation

Use affordance count to estimate implementation time:

| Affordances | Complexity | Est. Time |
|-------------|------------|-----------|
| 1-5 | Simple | 1-2 hours |
| 6-15 | Medium | 2-8 hours |
| 16-30 | Complex | 1-2 days |
| 30+ | Large | Break into sub-shapes |

### Dependency Graph

Order implementation by dependencies:

```
Models (N affordances that are tables/types)
    ↓
Pure functions (N affordances with no side effects)
    ↓
Functions with side effects (N affordances that write/update)
    ↓
UI components (U affordances)
    ↓
Page integration (wiring everything together)
```

## Chunking for Claude Code Sessions

For larger shapes, break into chunks that can be completed in one session:

**Chunk 1: Data Layer**
- All model definitions
- Database migrations
- Type definitions

**Chunk 2: API Layer**  
- All N affordance functions
- API route handlers
- Unit tests for functions

**Chunk 3: UI Layer**
- All U affordance components
- Component stories/tests
- Mock data for development

**Chunk 4: Integration**
- Wire components to API
- Page-level integration
- End-to-end tests

Each chunk should be independently testable and committable.
