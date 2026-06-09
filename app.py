import streamlit as st
import json
import random
from llm_client import ask_llm, LLMTask

# --- Configuration & Setup ---
@st.cache_data
def load_config():
    with open("config.json", 'r') as f:
        return json.load(f)

CONFIG = load_config()
CATEGORY_DATA = CONFIG["categories"] # A dict of dicts
CATEGORY_LIST = list(CATEGORY_DATA.keys()) 
MAX_QUESTION = CONFIG["max_questions"]

# --- Initialize Session State (The App's Memory) ---
if "game_stage" not in st.session_state:
    st.session_state.game_stage = "CHOOSE_CATEGORY" # Stages: CHOOSE_CATEGORY, PLAYING, GAME_OVER
if "category" not in st.session_state:
    st.session_state.category = ""
if "secret_answer" not in st.session_state:
    st.session_state.secret_answer = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] # Stores list of tuples: (question, answer)
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "game_result" not in st.session_state:
    st.session_state.game_result = None
if "question_text_input" not in st.session_state:
    st.session_state.question_text_input = ""

# --- Helper Functions ---
def check_answer(guess, answer):
    result = ask_llm(LLMTask.CHECK_FINAL_ANSWER, guess=guess, answer=answer)
    return result.lower() == 'yes'

def reset_game():
    st.session_state.game_stage = "CHOOSE_CATEGORY"
    st.session_state.category = None
    st.session_state.secret_answer = None
    st.session_state.chat_history = []
    st.session_state.question_count = 0
    st.session_state.game_result = None
    st.session_state.question_text_input = ""

# --- Web UI Layout ---
st.set_page_config(
    page_title="AI Akinator",
    layout="wide"
)

st.title("🤖 AI Akinator (20 Questions)")
st.write("---")

# STAGE 1: Choose Category

st.markdown("""
    <style>
    div.stButton > button p {
        font-size: 22px; 
        font-weight: bold ; 
        color: lightgreen;
    }
    </style>
""", unsafe_allow_html=True)

if st.session_state.game_stage == "CHOOSE_CATEGORY":
    st.markdown('<h3 tabindex="-1">Select a Category to Begin</h3>', unsafe_allow_html=True)
        
    selected_via_button = None
    NUM_COLS = 3

    for i in range(0, len(CATEGORY_LIST), NUM_COLS):
        cols = st.columns(NUM_COLS)
        row_categories = CATEGORY_LIST[i : i + NUM_COLS]
        
        for idx, cat in enumerate(row_categories):
            if cols[idx].button(cat.title(), use_container_width=True):
                selected_via_button = cat

    # Process category choice
    category = selected_via_button

    if category:
        st.session_state.category = category
        available_items = CATEGORY_DATA[category]["words"]
        st.session_state.secret_answer = random.choice(available_items)
        st.session_state.game_stage = "PLAYING"
        st.rerun()


# STAGE 2: The Main Game Loop
elif st.session_state.game_stage == "PLAYING":
    st.subheader(f"**Category:** `{st.session_state.category.title()}` | **Questions Used:** `{st.session_state.question_count} / {MAX_QUESTION}`")
    
    # Safe Progress Bar
    st.progress(min(st.session_state.question_count / MAX_QUESTION, 1.0))
    
    # --- Chat History Display ---
    st.write("### Game Log")
    for q_num, (q, a) in enumerate(st.session_state.chat_history, 1):
        st.write(f"**Q{q_num}:** {q}")
        st.write(f"💡 *AI Answer:* {a}")
        st.write("")

    action_taken = False

    st.write("---")


    col1, col2 = st.columns(2)

    current_cat = st.session_state.category.lower()
    example = CATEGORY_DATA[current_cat]["words"][0]
    example_q = CATEGORY_DATA[current_cat]["example_question"]

    # --- FORM 1: ASK A QUESTION ---
    with col1:
        st.markdown("### ❓ Ask a Question")
        
        # 1. Define a callback function that safely handles the text injection
        def copy_previous_question():
            if st.session_state.chat_history:
                # Get the last item's question string. 
                prev_question = st.session_state.chat_history[-1][0]
                
                if prev_question.startswith("Guess: "):
                    prev_question = prev_question.replace("Guess: ", "")
                    
                # Inject it into the state key BEFORE the widget renders
                st.session_state.question_text_input = prev_question

        # 2. Render the button and link it to the callback
        if st.session_state.chat_history:
            st.button(
                "📋 Copy Previous", 
                use_container_width=True, 
                on_click=copy_previous_question  # <-- This is the secret sauce
            )

        # 3. Now render the form and the widget. It will safely read the newly injected state!
        with st.form(key="ask_question_form", clear_on_submit=True):
            question_input = st.text_input(
                "Ask a Yes/No question:", 
                placeholder=f"{example_q}",
                key="question_text_input"
            )
            submit_question = st.form_submit_button(label="Ask AI")

    # --- FORM 2: MAKE A GUESS ---
    with col2.form(key="make_guess_form", clear_on_submit=True):
        st.markdown("### 🏆 Make a Guess")
        guess_input = st.text_input(f"What's your guess?", placeholder=f"{example}")
        submit_guess = st.form_submit_button(label="Submit Guess")
    
    # --- HANDLE QUESTION SUBMISSION ---
    if submit_question and question_input.strip():
        question_clean = question_input.strip()
        with st.spinner("AI is thinking..."):
            response = ask_llm(
                LLMTask.YES_NO_QUESTION, 
                category=st.session_state.category, 
                answer=st.session_state.secret_answer, 
                question=question_clean
            )
            
            if response.lower() != 'error':
                st.session_state.chat_history.append((question_clean, response))
                st.session_state.question_count += 1
                action_taken = True
            else:
                st.error("The AI couldn't process that question. Try rephrasing.")

    # --- HANDLE GUESS SUBMISSION ---
    if submit_guess and guess_input.strip():
        guess_clean = guess_input.strip()
        with st.spinner("Checking your guess..."):
            st.session_state.question_count += 1 
            if check_answer(guess_clean, st.session_state.secret_answer):
                st.session_state.chat_history.append((f"Guess: {guess_clean}", "✅ Correct."))
                st.session_state.game_stage = "GAME_OVER"
                st.session_state.game_result = "WIN"
                action_taken = True
            else:
                st.session_state.chat_history.append((f"Guess: {guess_clean}", "❌ Incorrect."))
                action_taken = True

    # --- POST-ACTION GAME STATE CHECK ---
    if action_taken:
        # If they haven't won yet but hit the question limit, force final guess stage
        if st.session_state.game_stage != "GAME_OVER" and st.session_state.question_count >= MAX_QUESTION:
            st.session_state.game_stage = "FINAL_GUESS"
            
        st.rerun()

# STAGE 3: Final Guess Sequence
elif st.session_state.game_stage == "FINAL_GUESS":
    # --- Chat History Display ---
    st.write("### Game Log")
    for q_num, (q, a) in enumerate(st.session_state.chat_history, 1):
        st.markdown(f"**Q{q_num}:** {q}")
        st.markdown(f"💡 *AI Answer:* {a}")
        st.write("")
    st.warning("⚠️ Out of turns! Time for your final guess.")
    
    with st.form(key="final_form"):
        final_guess = st.text_input("Enter your final absolute guess:")
        final_submit = st.form_submit_button("Submit Final Guess")
        
    if final_submit and final_guess.strip():
        guess_clean = final_guess.strip()
        st.session_state.question_count += 1 
        if check_answer(final_guess.strip(), st.session_state.secret_answer):
            st.session_state.chat_history.append((f"Guess: {guess_clean}", "✅ Correct."))
            st.session_state.game_result = "WIN"
        else:
            st.session_state.chat_history.append((f"Guess: {guess_clean}", "❌ Incorrect."))
            st.session_state.game_result = "LOSE"
        
        st.session_state.game_stage = "GAME_OVER"
        st.rerun()

# STAGE 4: Game Over Screen
elif st.session_state.game_stage == "GAME_OVER":
    # --- Chat History Display ---
    st.write("### Game Log")
    for q_num, (q, a) in enumerate(st.session_state.chat_history, 1):
        st.markdown(f"**Q{q_num}:** {q}")
        st.markdown(f"💡 *AI Answer:* {a}")
        st.write("")

    if st.session_state.game_result == "WIN":
        st.balloons()
        st.success(f"🎉 **Congratulations! You Won!** The answer was indeed **{st.session_state.secret_answer}**.")
    else:
        st.error(f"💀 **Game Over!** You couldn't crack it. The secret answer was **{st.session_state.secret_answer}**.")
        
    if st.button("Play Again"):
        reset_game()
        st.rerun()
