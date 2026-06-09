# 6-Week Phased Feature Roadmap

## Phase 1: The Core MVP (Weeks 1–3)

### Objectives

- Set up a local Flask/FastAPI server capable of parsing raw JSON requests.
- Migrate existing prompt-engineering and evaluation functions out of the Streamlit script into standalone Python endpoints.
- Create a native HTML interface.
- Implement real-time UI logging through JavaScript `fetch()` hooks.

### Deliverables

- Functional API server.
- Browser-based frontend.
- End-to-end question-answer game loop.

---

## Phase 2: Database & Engagement Layer (Weeks 4-5)

### Objectives

- Integrate MongoDB Atlas (free tier).
- Manage user profile objects using JSON documents.
- Implement dynamic score calculation.

### Scoring Formula

Score = (21 - Q_used) * category_difficulty

### Additional Features

- User registration.
- User login/authentication.
- Persistent win/loss tracking.
- High-score leaderboard.
- Win streak and performance metrics.

---

## Phase 3: Final Polish & "Juice" (Week 6)

### Objectives

#### UI Enhancements

- Smooth asynchronous CSS transitions.
- Chat bubbles slide elegantly into place.
- Improved visual responsiveness.

#### AI Presentation

- Typewriter animation for AI reasoning panels.
- Improved readability of responses.

#### Quality Assurance

- Edge-case testing.
- Final guess validation testing.
- Typographical and formatting robustness checks.
- General bug fixing and usability improvements.

---

# Final Deliverable

A university-grade, full-stack web application that:

- Uses a decoupled frontend/backend architecture.
- Employs cryptographic techniques to prevent client-side cheating.
- Persists user data through MongoDB.
- Provides an engaging AI-powered 20 Questions experience.
- Demonstrates significant JavaScript, backend, database, and software architecture competencies.