from enum import Enum, auto
from openai import OpenAI
from flask import current_app
import json

class LLMTask(Enum):
    YES_NO_QUESTION = auto()
    CHECK_FINAL_ANSWER = auto()

def get_openai_client():
    """Instantiates OpenAI client using API key in app config."""
    return OpenAI(api_key=current_app.config["OPENAI_API_KEY"])

def ask_llm(task_type: LLMTask, **kwargs) -> tuple[str, str]:
    """
    Executes an evaluation task against OpenAI.
    
    Returns:
        tuple: (response_text, analysis_text)
    """
    client = get_openai_client()
    
    if task_type == LLMTask.YES_NO_QUESTION:
        category = kwargs.get("category")
        secret_answer = kwargs.get("answer")
        question = kwargs.get("question")
        
        system_prompt = (
            "Instructions:\n"
            "You are playing a game of 20 Questions. Your job is to answer the user's "
            "question about a secret object accurately based on facts.\n\n"

            "1. Think step-by-step before deciding on an answer. Briefly analyze the secret "
            "topic's physical properties, geography, characteristics, or real-world traits "
            "relevant to the question so that your answer is logically consistent and does "
            "not contradict common sense.\n"

            "2. Base your answer on majority facts. If more than 50% of instances of the "
            "topic satisfy the condition, answer 'Yes'. If more than 50% do not, answer 'No'.\n"

            "3. When the topic is a profession, role, or job, base your answer on the typical "
            "day-to-day execution of that role, not on its training requirements, educational "
            "pathway, history, origin, or related industries.\n"

            "4. Return 'Error' only when:\n"
            "   - The user's input is unrelated to the game, nonsensical, unintelligible, or gibberish.\n"
            "   - The question is too ambiguous, context-dependent, or evenly split to justify "
            "a clear majority 'Yes' or 'No' answer.\n"
            "Do not return 'Error' merely because the question is difficult.\n"

            "5. Format your output strictly as a single-line JSON object with exactly two keys:\n"
            "{\"analysis\":\"Brief reasoning here\",\"response\":\"Yes|No|Error\"}"
        )

        user_prompt = (
            f"Category: {category}\n"
            f"Secret Object: {secret_answer}\n"
            f"Player's Question: {question}"
        )
        
    elif task_type == LLMTask.CHECK_FINAL_ANSWER:
        guess = kwargs.get("guess")
        secret_answer = kwargs.get("answer")
        
        system_prompt = (
            "You are a judge verifying a game submission. Determine whether the user's guess "
            "matches the secret answer.\n\n"

            "Instructions:\n"

            "1. Think step-by-step. Analyze the semantic and physical relationship between "
            "the guess and the answer before making a decision.\n"

            "2. Return 'yes' if the guess is the same object or concept as the answer, "
            "including minor typos, spelling mistakes, singular/plural differences, or "
            "insignificant wording differences.\n"
            "Examples: 'lasgna' matches 'lasagna'; 'dogs' matches 'dog'.\n"

            "3. Return 'yes' if the guess contains filler words, articles, or other "
            "non-essential modifiers.\n"
            "Examples: 'a sandwich' matches 'sandwich'; "
            "'the bicycle' matches 'bicycle'.\n"

            "4. Return 'yes' if the guess is a common everyday synonym or a term that "
            "ordinary people would use interchangeably in normal conversation.\n"
            "Examples: 'couch' matches 'sofa'; 'cup' matches 'mug'.\n"

            "5. Return 'no' if the guess is a broader category, narrower category, "
            "subcategory, superclass, related object, or associated concept rather than "
            "the same thing.\n"
            "Examples: 'food' does not match 'lasagna'; "
            "'pasta' does not match 'lasagna'; "
            "'dog' does not match 'beagle'; "
            "'beagle' does not match 'dog'.\n"

            "6. When uncertain, prefer 'no' unless the two terms would commonly be treated "
            "as the same answer by ordinary people playing a guessing game.\n\n"

            "Format your output as a single-line JSON object with exactly two keys:\n"
            '{"analysis":"Brief reasoning here","response":"yes|no"}'
        )
        user_prompt = f"User Guess: '{guess}' | Target Secret Answer: '{secret_answer}'"
        
    else:
        raise ValueError("Invalid LLM Task Type")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        # Clean and parse the response payload safely
        raw_content = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_content)

        valid_responses = {"yes", "no", "error"} if task_type == LLMTask.YES_NO_QUESTION else {"yes", "no"}

        decision = str(parsed.get("response", "Error")).strip().lower()
        analysis = str(parsed.get("analysis", "No log provided."))

        if decision not in valid_responses:
            current_app.logger.warning(
                f"Unexpected LLM response: {decision}"
            )
            decision = "error" if task_type == LLMTask.YES_NO_QUESTION else "no"

        return decision, analysis
            
    except Exception as e:
        current_app.logger.error(f"LLM Processing Exception: {e}")
        return "error", f"Failed processing due to connection or structural error: {e}"