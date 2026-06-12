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

            "1. CRITICAL - Logical Evaluation: Before applying any other rule, check if the question "
            "contains a compound choice, list, or options (e.g., 'A or B', 'X or Y'). You MUST evaluate "
            "these using logical OR. If the secret topic matches ANY single one of the options provided, "
            "your final response MUST be 'Yes'. You are strictly forbidden from answering 'No' just "
            "because one of the options is false.\n"

            "2. Think step-by-step: Briefly analyze the secret topic's physical properties, geography, "
            "characteristics, or real-world traits relevant to the question so that your answer is logically "
            "consistent and does not contradict common sense.\n"

            "3. Base your answer on majority facts:\n"
            "   - If the secret topic is a specific person or unique entity, answer based on absolute factual accuracy.\n"
            "   - If the topic represents a category or class, answer 'Yes' if more than 50% of instances satisfy the condition, and 'No' if they do not.\n"
            "   - For location questions (e.g., 'found at home'), evaluate if the place is a standard, expected storage or usage point, even if the object is mobile.\n"

            "4. Roles and Professions: When the topic is a profession, role, or job, base your answer on the typical day-to-day execution of that role, not on its training requirements, educational pathway, history, origin, or related industries.\n"

            "5. Return 'Error' only when:\n"
            "   - The user's input is unrelated to the game, nonsensical, unintelligible, or gibberish.\n"
            "   - The question is too ambiguous, context-dependent, or evenly split to justify a clear majority 'Yes' or 'No' answer.\n"
            "Do not return 'Error' merely because the question is difficult.\n"

            "6. Format your output strictly as a single-line JSON object with exactly two keys:\n"
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
        
        raw_content = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_content)

        raw_decision = str(parsed.get("response", "Error")).strip().lower()
        analysis = str(parsed.get("analysis", "No log provided."))

        if task_type == LLMTask.YES_NO_QUESTION:
            if raw_decision not in {"yes", "no", "error"}:
                current_app.logger.warning(f"Unexpected LLM response: {raw_decision}")
                decision = "Error"
            else:
                decision = raw_decision
        else:
            if raw_decision not in {"yes", "no"}:
                current_app.logger.warning(f"Unexpected LLM response: {raw_decision}")
                decision = "no"
            else:
                decision = raw_decision

        return decision, analysis
            
    except Exception as e:
        current_app.logger.error(f"LLM Processing Exception: {e}")
        fallback_decision = "error" if task_type == LLMTask.YES_NO_QUESTION else "no"
        return fallback_decision, f"Failed processing due to connection or structural error: {e}"