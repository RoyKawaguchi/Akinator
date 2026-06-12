// Base URL pointing directly to your local Flask backend instance
const API_BASE_URL = "http://127.0.0.1:5000/api";

// Client-side transient game state storage
let currentGameId = null;
let gameAnalysisHistory = [];
let currentTurnIndex = 0;

// DOM Element Registry
const setupContainer = document.getElementById("setup-container");
const gameContainer = document.getElementById("game-container");
const gameOverContainer = document.getElementById("game-over-container");

const chatDisplay = document.getElementById("chat-display");
const categoryBadge = document.getElementById("category-badge");
const turnCounter = document.getElementById("turn-counter");

const questionForm = document.getElementById("question-form");
const questionInput = document.getElementById("question-input");
const guessForm = document.getElementById("guess-form");
const guessInput = document.getElementById("guess-input");

const endStatusHeading = document.getElementById("end-status-heading");
const endMessageText = document.getElementById("end-message-text");
const revealBox = document.getElementById("reveal-box");
const secretWordDisplay = document.getElementById("secret-word-display");
const restartBtn = document.getElementById("restart-btn");

const inputSection = document.getElementById("input-section");
const gameOverPanel = document.getElementById("game-over-panel");
const analysisToggle = document.getElementById("analysis-toggle");

// ==========================================
// EVENT LISTENERS & INITIALIZATION
// ==========================================

// Run this function automatically when the page finishes loading
document.addEventListener("DOMContentLoaded", () => {
    fetchCategories();
});

async function fetchCategories() {
    const grid = document.getElementById("category-grid");
    
    try {
        const response = await fetch(`${API_BASE_URL}/game/categories`);
        const data = await response.json();
        
        if (!response.ok) throw new Error("Failed to load categories");
        
        // Clear out anything inside the grid just in case
        grid.innerHTML = "";
        
        // Dynamically build buttons for every category returned by Flask
        data.categories.forEach(category => {
            const button = document.createElement("button");
            button.className = "btn category-btn";
            button.setAttribute("data-category", category);
            
            // Capitalize the first letter nicely for the UI (e.g., "food" -> "Food")
            const formattedName = category.charAt(0).toUpperCase() + category.slice(1);
            button.textContent = formattedName;
            
            // Attach the click handler to initialize the match
            button.addEventListener("click", () => {
                initializeGame(category);
            });
            
            grid.appendChild(button);
        });
        
    } catch (err) {
        grid.innerHTML = `<p class="error">⚠️ Error loading categories: ${err.message}</p>`;
    }
}

// Category selection + Game initialization
document.querySelectorAll(".category-btn").forEach(button => {
    button.addEventListener("click", () => {
        const selectedCategory = button.getAttribute("data-category");
        initializeGame(selectedCategory);
    });
});

// Intercept Question Submit Form
questionForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = questionInput.value.trim();
    if (!text) return;
    
    questionInput.value = "";
    await submitQuestion(text);
});

// Intercept Guess Submit Form
guessForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = guessInput.value.trim();
    if (!text) return;
    
    guessInput.value = "";
    await submitGuess(text);
});

// Reset visual elements to pick a new match
restartBtn.addEventListener("click", () => {
    currentGameId = null;
    gameAnalysisHistory = [];
    currentTurnIndex = 0;

    analysisToggle.checked = false;
    chatDisplay.innerHTML = "";
    revealBox.classList.add("hidden");
    secretWordDisplay.textContent = "";
    
    // Reset structural section block layouts back to original states
    gameOverPanel.classList.add("hidden");
    inputSection.classList.remove("hidden");
    
    gameContainer.classList.add("hidden");
    setupContainer.classList.remove("hidden");
});

analysisToggle.addEventListener("change", async () => {
    if (analysisToggle.checked) {
        // 🟢 SWITCH TURNED ON: Fetch and Display Reasoning
        try {
            // Only fetch from the backend if we haven't loaded it yet for this match
            if (gameAnalysisHistory.length === 0) {
                const response = await fetch(`${API_BASE_URL}/game/${currentGameId}/analysis`);
                
                if (!response.ok) {
                    throw new Error("Could not retrieve internal AI thinking metrics.");
                }
                
                const data = await response.json();
                gameAnalysisHistory = data.chat_history; // Array of turns containing 'analysis'
            }
            
            // Inject the reasoning blocks into the UI
            revealAIReasoning();
            
        } catch (err) {
            console.error(err);
            alert(`⚠️ Error loading AI analysis: ${err.message}`);
            analysisToggle.checked = false; // Flip switch back to off state on failure
        }
    } else {
        // 🔴 SWITCH TURNED OFF: Cleanly remove thoughts boxes
        hideAIReasoning();
    }
});

// ==========================================
// CORE ASYNC NETWORK UTILITIES (FETCH)
// ==========================================

/**
 * Executes a POST request /api/game/start to boot a match
 */
async function initializeGame(category) {
    try {
        const response = await fetch(`${API_BASE_URL}/game/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: category })
        });
        
        const data = await response.json();
        
        if (!response.ok) throw new Error(data.error || "Failed to start match.");
        
        // Populate system references using returning schema metrics
        currentGameId = data.game_id;
        categoryBadge.textContent = `Category: ${data.category}`;
        turnCounter.textContent = `Questions Used: 0 / ${data.max_questions}`;
        
        // Swap visibility views
        setupContainer.classList.add("hidden");
        gameContainer.classList.remove("hidden");
        questionInput.focus();
        
        appendMessage("AI", `I am thinking of a secret answer. Begin asking questions!`);
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

/**
 * Dispatches a question payload to /api/game/question
 */
async function submitQuestion(questionText) {
    appendMessage("user-q", `Q: ${questionText}`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/game/question`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_id: currentGameId,
                question_text: questionText
            })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Turn processing error.");

        appendMessage("AI", `AI: ${data.response}`, currentTurnIndex);
        
        currentTurnIndex++;
        turnCounter.textContent = `Questions Used: ${data.question_count} / 20`;
        
        // Check if forced transitions apply
        if (data.game_stage === "FINAL_GUESS") {
            appendMessage("AI", "⚠️ Out of turns! You must now enter a final structural guess.");
        }
    } catch (err) {
        appendMessage("AI", `❌ Error: ${err.message}`);
    }
}

/**
 * Dispatches guess comparison payload to /api/game/guess
 */
async function submitGuess(guessText) {
    appendMessage("user-g", `Guess attempt submitted: "${guessText}"`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/game/guess`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_id: currentGameId,
                guess_text: guessText
            })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Guess resolution framework error.");
        
        appendMessage("AI", `Result: ${data.response}`);
        turnCounter.textContent = `Questions Used: ${data.question_count} / 20`;
        
        // Evaluate structural conditions returning from structural backend loops
        if (data.game_stage === "GAME_OVER") {
            handleGameOver(data.game_result, data.secret_answer);
        }
    } catch (err) {
        appendMessage("AI", `❌ Error: ${err.message}`);
    }
}

// ==========================================
// UI DOM TRANSITION MANIPULATION UTILITIES
// ==========================================
function appendMessage(sender, text, index = null) {
    const messageElement = document.createElement("div");
    
    // 1. Give it the structural bubble base style
    messageElement.classList.add("chat-bubble");
    
    // 2. Map the incoming sender tag directly to your specific style variations
    if (sender === "AI") {
        messageElement.classList.add("ai-a");
        // Assign the evaluation look-up tracker attribute if index is provided
        if (index !== null) {
            messageElement.setAttribute("data-ai-index", index);
        }
    } else if (sender === "USER_GUESS") { // Or whatever string you pass for a guess block
        messageElement.classList.add("user-g");
    } else {
        // Default standard user questions
        messageElement.classList.add("user-q");
    }
    
    messageElement.textContent = text;
    
    chatDisplay.appendChild(messageElement);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

function handleGameOver(result, secretAnswer) {
    // Lock out text entry fields by hiding input container blocks
    inputSection.classList.add("hidden");
    
    // Unveil the resolution details right below the current history log
    gameOverPanel.classList.remove("hidden");
    
    if (result === "WIN") {
        endStatusHeading.textContent = "🎉 Victory is Yours!";
        endMessageText.textContent = "Incredible tracking skills! You parsed the semantic blocks and defeated the AI engine.";
    } else {
        endStatusHeading.textContent = "💀 Defeat!";
        endMessageText.textContent = "The internal session has collapsed. You ran out of available opportunities.";
    }
    
    if (secretAnswer) {
        secretWordDisplay.textContent = secretAnswer;
        revealBox.classList.remove("hidden");
    }
    
    // Auto-scroll the chat log window one last time so the final status notification fits
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

function revealAIReasoning() {
    gameAnalysisHistory.forEach((turn, index) => {
        // Find the specific AI bubble corresponding to this turn index
        const aiBubble = document.querySelector(`[data-ai-index="${index}"]`);
        
        // Safety check: ensure the element exists and hasn't had thoughts added yet
        if (aiBubble && !aiBubble.querySelector(".ai-thought-box") && turn.analysis) {
            const thoughtBox = document.createElement("div");
            thoughtBox.className = "ai-thought-box";
            
            // Format it nicely with an explicit label
            thoughtBox.innerHTML = `<strong>🧠 AI Evaluation:</strong> "${turn.analysis}"`;
            
            aiBubble.appendChild(thoughtBox);
        }
    });
    
    // Auto-scroll to make sure text expansion doesn't push current views out of framework
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

// Function to strip the thought containers out when toggle is flicked off
function hideAIReasoning() {
    const activeThoughtBoxes = document.querySelectorAll(".ai-thought-box");
    activeThoughtBoxes.forEach(box => box.remove());
}