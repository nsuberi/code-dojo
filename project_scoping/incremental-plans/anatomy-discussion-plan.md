# Anatomy Discussion Feature - Implementation Plan

## Overview
Add a Socratic dialogue feature where students can explore the "anatomy" of their code submission through AI-guided conversation. The agent presents a menu of code elements, uses analogies to teach concepts, and synthesizes realizations into a summary popup.

**Key Design Decisions:**
- **Admin-configured topics**: Instructors define anatomy topics per challenge (e.g., "Flask routes", "Authentication", "Database queries")
- **AI-augmented analysis**: The "Socratic Sensei" also analyzes what the student actually built and infers additional discussion points
- **Fully persisted**: Conversations and realizations saved to database for instructor review

## Architecture

```
Learning Goal (admin-configured anatomy topics)
        ↓
Student Submission Page
        ↓
[Anatomy Analyzer] → Combines: 1) Admin topics, 2) Student code patterns
        ↓
[Anatomy Menu UI] → Student selects topic to discuss
        ↓
[Socratic Sensei API] → Claude conversation with Socratic prompting
        ↓                    ↓
        ↓              Tracks realizations via [REALIZATION:] tags
        ↓
[End Conversation] → Synthesis service
        ↓
[Modal Popup] → Markdown summary of topics & realizations
        ↓
[Persisted to DB] → Instructors can review student learning
```

## Files to Create/Modify

### Backend - New Files
| File | Purpose |
|------|---------|
| `services/anatomy_analyzer.py` | Combine admin topics + analyze student code patterns |
| `services/socratic_chat.py` | Manage Claude conversations with Socratic prompting |
| `routes/anatomy.py` | Blueprint with chat API endpoints |
| `models/anatomy_conversation.py` | Persist conversations, messages, realizations |
| `models/anatomy_topic.py` | Admin-configured anatomy topics per LearningGoal |

### Backend - Modify
| File | Purpose |
|------|---------|
| `models/__init__.py` | Import new models |
| `app.py` | Register anatomy blueprint |
| `routes/admin.py` | Add admin UI for configuring anatomy topics |

### Frontend - New Files
| File | Purpose |
|------|---------|
| `static/js/anatomy-chat.js` | Vanilla JS for chat UI, menu, modal |
| `static/assets/socratic-sensei.png` | Avatar icon for the AI tutor in chat |
| `templates/admin/anatomy_topics.html` | Admin page to configure topics per goal |

### Frontend - Modify
| File | Purpose |
|------|---------|
| `static/css/styles.css` | Add chat interface & modal styles |
| `templates/submissions/student_view.html` | Add anatomy discussion section |
| `templates/admin/dashboard.html` | Link to anatomy topic configuration |

### Configuration
| File | Purpose |
|------|---------|
| `.env.example` | Document required env vars including `ANTHROPIC_API_KEY` |

## API Endpoints

```
GET  /submissions/<id>/anatomy          → List anatomy elements
POST /submissions/<id>/anatomy/chat     → Send message / start conversation
POST /submissions/<id>/anatomy/end      → End conversation, get synthesis
```

## Implementation Steps

### Phase 1: Database Models & Config
1. Create `.env.example` with `ANTHROPIC_API_KEY=your_key_here`
2. Create `models/anatomy_topic.py`:
   - `AnatomyTopic` - admin-configured topics per LearningGoal
   - Fields: `goal_id`, `name`, `description`, `suggested_analogies`, `order`
3. Create `models/anatomy_conversation.py`:
   - `AnatomyConversation` - conversation metadata, synthesis
   - `ConversationMessage` - individual messages
   - `StudentRealization` - tracked realizations
4. Update `models/__init__.py` to import new models, run migrations

### Phase 2: Admin Configuration
5. Add admin routes to `routes/admin.py`:
   - `GET /admin/goals/<id>/anatomy-topics` - list/edit topics for a goal
   - `POST /admin/goals/<id>/anatomy-topics` - create/update topics
6. Create `templates/admin/anatomy_topics.html` - form to manage topics

### Phase 3: Anatomy Analyzer Service
7. Create `services/anatomy_analyzer.py`:
   - `get_anatomy_menu(goal, submission_diff)` → combines:
     - Admin-configured topics from database
     - AI-detected patterns from student's code diff
   - Uses Claude to analyze diff and match to topics + find additional patterns

### Phase 4: Socratic Chat Service
8. Create `services/socratic_chat.py`:
   - `start_conversation(submission_id, topic)` → new conversation
   - `send_message(conversation_id, message)` → Claude response + realization detection
   - `end_conversation(conversation_id)` → synthesize and return markdown
   - System prompt with Socratic method, analogies from admin config
   - Parse `[REALIZATION: ...]` tags from Claude responses

### Phase 5: Routes & API
9. Create `routes/anatomy.py` blueprint:
   - `GET /submissions/<id>/anatomy` - fetch menu (admin topics + detected patterns)
   - `POST /submissions/<id>/anatomy/chat` - send message, receive response
   - `POST /submissions/<id>/anatomy/end` - end conversation, return synthesis
10. Register blueprint in `app.py`

### Phase 6: Frontend
11. Add CSS to `static/css/styles.css`:
    - `.anatomy-layout` - sidebar + chat grid
    - `.anatomy-sidebar`, `.anatomy-element` - menu styling
    - `.chat-container`, `.message` - chat interface
    - `.modal-overlay`, `.synthesis-modal` - popup modal
    - `.sensei-avatar` - avatar styling for AI messages (circular, sized appropriately)
12. Create `static/assets/` folder and move `socratic-sensei.png` from project root
13. Create `static/js/anatomy-chat.js`:
    - `loadAnatomyElements()` - fetch and render menu
    - `selectElement(id)` - start/switch discussion
    - `sendMessage()` - POST to chat endpoint
    - `endConversation()` - show synthesis modal
    - Display sensei avatar next to AI messages
14. Modify `templates/submissions/student_view.html`:
    - Add "Explore Your Code" section after AI Feedback
    - Include anatomy sidebar and chat container
    - Include sensei avatar in chat header

**Note**: Future enhancement - add basic animation to the sensei avatar (e.g., subtle idle animation, thinking animation while waiting for response). For now, use static image.

## Socratic Prompt Design

The system prompt instructs Claude to:
1. **Never give direct answers** - guide through questions
2. **Use analogies** - e.g., "decorators are like security guards checking credentials"
3. **Track realizations** - append `[REALIZATION: description]` when student shows understanding
4. **Keep responses concise** - 2-3 sentences typically

Example exchange:
```
Student: "What does @login_required do?"
Claude: "Imagine a VIP room at a club. What would you need before entering?"
Student: "Someone checking if you're on the list?"
Claude: "Exactly! So what do you think @login_required checks?"
[REALIZATION: Student connected authentication to access control]
```

## Database Schema

```python
# Admin-configured topics per learning goal
class AnatomyTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('learning_goals.id'))
    name = db.Column(db.String(100))  # e.g., "Flask Routes", "Authentication"
    description = db.Column(db.Text)   # What students should understand
    suggested_analogies = db.Column(db.Text)  # Analogies for Socratic teaching
    order = db.Column(db.Integer)

    goal = db.relationship('LearningGoal', backref='anatomy_topics')

# Conversation tracking
class AnatomyConversation(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('anatomy_topics.id'), nullable=True)
    topic_name = db.Column(db.String(200))  # For AI-detected topics (no topic_id)
    status = db.Column(db.String(20), default='active')  # active, ended
    synthesis_markdown = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)

    submission = db.relationship('Submission', backref='anatomy_conversations')
    topic = db.relationship('AnatomyTopic')

class ConversationMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('anatomy_conversations.id'))
    role = db.Column(db.String(20))  # user, assistant
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime)

class StudentRealization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('anatomy_conversations.id'))
    topic = db.Column(db.String(200))
    description = db.Column(db.Text)
    detected_at = db.Column(db.DateTime)
```

## Verification

1. **Setup**: Create `.env` with `ANTHROPIC_API_KEY`, run `flask run`
2. **Admin config**: As admin, configure anatomy topics for a learning goal
3. **Test anatomy menu**: Submit code, verify menu shows admin topics + AI-detected patterns
4. **Test Socratic chat**: Select topic, ask questions, verify analogy-based responses
5. **Test realizations**: Express understanding, verify `[REALIZATION]` tags parsed
6. **Test synthesis modal**: End conversation, verify markdown popup with topics & realizations
7. **Instructor review**: As instructor, view student submission and see their conversation history

## Key Files to Modify

- `app.py` - register anatomy blueprint
- `models/__init__.py` - import new models
- `routes/admin.py` - add anatomy topic management routes
- `templates/submissions/student_view.html` - add anatomy section
- `templates/admin/dashboard.html` - link to topic configuration
- `static/css/styles.css` - add chat/modal styles
