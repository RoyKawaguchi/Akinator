# 🎯 PROJECT OVERVIEW: AI 20-QUESTIONS FULL-STACK GAME

**Target Deadline:** 6 weeks

**Architectural Goal:** Transition the working Streamlit Python prototype into a robust, decoupled, university-grade web application.

## Tech Stack

- Native HTML5/CSS3
- Client-side JavaScript
- Stateless Python Backend (Flask)
- MongoDB Database

---

# 1. Game Premise & Core Mechanics

The application is an interactive, full-stack implementation of **20 Questions**.

### Gameplay Flow

1. The player selects a target category (e.g., Food, Everyday Objects).
2. A secret word/topic is chosen for the match.
3. The user has exactly **20 opportunities** to ask yes/no questions.

Examples:

- "Is it eaten hot?"
- "Does it contain wheat?"

4. An LLM analyzes the user's question against a hidden context block for the secret word, generating:
   - A definitive **YES** or **NO** response.
   - Internal Chain-of-Thought (CoT) reasoning logs. 
   (Reduces hallucination, and helps with debugging)
5. The player wins by typing the correct absolute guess before running out of turns.
6. If they exhaust all 20 questions without guessing the exact word, they lose.

---

# 2. Decoupled Architecture & Responsibilities


**Frontend (Client)** (HTML5, CSS3, Native JavaScript)
- Tracks total active game state (turn counters, raw Q&A chat arrays, UI displays).
- Executes asynchronous network `fetch()` calls to the API.
- Manipulates the DOM dynamically to inject chat logs and trigger animations. 

**Backend (Calculator)** (Python (Flask)) 
- Acts as a purely stateless calculation engine.
- Maps cryptographic hashes back to true words during runtime execution lifecycles.
- Formats and safely injects user questions into the LLM API.
- Validates final player guesses.

**Database (Persistence)** (MongoDB)
- Stores long-term document records (user accounts, login credentials).
- Tracks permanent user profiles, win/loss history records, and top high scores.

---

# 3. Cryptographic State & Anti-Cheat System

Because frontend state management leaves traditional variables exposed to client-side browser inspection tools, a custom data-hiding pipeline prevents cheating.

## Initialization

When a game starts:

1. JS sends the category title (e.g., `"food"`) and requests Python for a secret word.
2. Python picks the secret word (e.g., `"donut"`).
3. Python generates an irreversible cryptographic hash of that string using SHA-256.
4. JS receives the hash (e.g., `b1946ac92492...`). 

The plain-text word never touches browser client memory, preventing players from discovering it through browser developer tools.

## The Question Loop

When asking a question:

1. JavaScript sends to Python:
   - The natural-language question.
   - The hash token.

2. Python:
   - Maps the hash back to the true word using an internal lookup dictionary (very fast).
   - Runs the LLM evaluation logic.
   - Returns a simple Yes/No/Error response to JS.

## The Resolution

For the final guess:

1. The user's guess string is securely sent to Python.
2. Python hashes the guess.
3. The hash is validated against the initialization token.
4. The server issues an authoritative win/loss result.