import os
from enum import Enum, auto
from openai import OpenAI
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()
client = OpenAI()

class LLMTask(Enum):
    YES_NO_QUESTION = auto()
    CHECK_FINAL_ANSWER = auto()

def ask_llm(task_type: LLMTask, **kwargs) -> str:
    messages: list[ChatCompletionMessageParam] = []

    if task_type == LLMTask.YES_NO_QUESTION:
        category = kwargs.get("category")
        answer = kwargs.get("answer")
        question = kwargs.get("question")
        messages = [
            {
                "role": "user", 
                "content": (
                    f"Category of Akinator: {category}\n"
                    f"Secret Topic: {answer}\n"
                    f"Question: {question}\n\n"
                    "Instructions:\n"
                    "1. Think step-by-step: Briefly analyze the secret topic's physical properties, "
                    "geography, or traits relative to the question so you don't contradict common sense.\n"
                    "2. Base your answer on majority facts (e.g., if >50% of the population matches, it is 'Yes.').\n"
                    "3. Base your answers on the day-to-day execution of the topic/job itself, not the background training, origin, or peripheral industries associated with it."
                    "4. End your response by providing your final answer on a brand new line starting with 'FINAL_ANSWER: ' "
                    "followed ONLY by 'Yes.', 'No.', or 'Error'.\n\n"
                    "Example Output Format:\n"
                    "Analysis: Watermelons are large, heavy, spherical/oblong fruits that grow on vines. While they have thick rinds, people do not eat the rind; they slice it and eat the red flesh inside. Therefore, people do peel/remove the rind or slice it.\n"
                    "FINAL_ANSWER: No."
                )
            }
        ]

    elif task_type == LLMTask.CHECK_FINAL_ANSWER:
        guess = kwargs.get("guess")
        answer = kwargs.get("answer")
        messages = [
            {
                "role": "user", 
                "content": (
                    "Determine if the user's guess matches the secret answer well enough to count as a win in a game of 20 Questions.\n\n"
                    f"User Guess: '{guess}'\n"
                    f"Secret Answer: '{answer}'\n\n"
                    "Instructions:\n"
                    "1. Think step-by-step: Analyze the physical and semantic relationship between the guess and the answer.\n"
                    "2. Return 'yes' if the guess is the exact same word, or includes minor typos/spelling mistakes (e.g., 'lasgna' for 'lasagna').\n"
                    "3. Return 'yes' if they included filler words or articles (e.g., 'a sandwich' matches 'sandwich').\n"
                    "4. Return 'no' if the guess is a massive, broad umbrella category (e.g., if the answer is 'lasagna', then 'pasta', 'food', or 'italian food' is 'no').\n"
                    "5. Return 'yes' if the guess is a ubiquitous, everyday synonym or immediate parent category that completely overlaps in casual human conversation (e.g., if the answer is 'mug', then 'cup' is acceptable and should be 'yes'. If the answer is 'sofa', 'couch' is 'yes'). Use reasonable human leniency for these tight physical duplicates.\n"
                    "6. End your response by providing your final answer on a brand new line starting with 'FINAL_ANSWER: ' "
                    "followed ONLY by 'yes' or 'no'.\n\n"
                    "Example 1 (Too Broad):\n"
                    "Analysis: The user guessed 'pasta' but the secret answer is 'lasagna'. 'Pasta' is a massive macro-category containing hundreds of distinct dishes, so it is too broad.\n"
                    "FINAL_ANSWER: no.\n\n"
                    "Example 2 (Close Synonym/Overlapping Sub-type):\n"
                    "Analysis: The user guessed 'cup' but the secret answer is 'mug'. While a mug is technically a specific type of cup with a handle, in casual speech they are functionally interchangeable everyday drinking vessels. This is close enough for a casual game win.\n"
                    "FINAL_ANSWER: yes."
                )
            }
        ]

    else:
        raise ValueError("Invalid LLM task type provided.")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.0  
        )
        
        content = response.choices[0].message.content or ""
        
        if "FINAL_ANSWER:" in content:
            print("\n" + "="*60)
            if task_type == LLMTask.YES_NO_QUESTION:
                print(f"❓ QUESTION: {kwargs.get('question')}")
            else:
                print(f"🏆 GUESS CHECK | Guess: '{kwargs.get('guess')}' vs Answer: '{kwargs.get('answer')}'")
            print("-"*60)
            print(content.strip())
            print("="*60 + "\n")
            
            # Extract just the raw token value
            content = content.split("FINAL_ANSWER:")[-1]

        return content.strip().replace(".", "") # Cleans up any trailing periods
        
    except Exception as e:
        print(f"\n[LLM Error]: {e}")
        return "error"