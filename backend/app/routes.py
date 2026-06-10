import uuid
import random
from flask import Blueprint, request, jsonify, current_app
from app.database import get_games_collection
from app.services.llm_service import ask_llm, LLMTask

# Create a Flask Blueprint for our API routes
api_bp = Blueprint("api", __name__)

# TODO: Integrate with config.json
MOCK_CATEGORIES = {
    "food": ["donut", "lasagna", "burger", "sushi"],
    "animals": ["kangaroo", "beagle", "penguin", "axolotl"]
}

@api_bp.route("/api/game/start", methods=["POST"])
def start_game():
    """
    Initializes a completely new game record.
    Expects JSON input: { "category": "food" }
    Returns a JSON {"game_id", "category", "max_questions", "game_stage"} 201 if successful
    """

    data = request.get_json() or {}
    category = data.get("category", "").strip().lower()
    
    if category not in MOCK_CATEGORIES:
        return jsonify({"error": f"Invalid category. Choose from: {list(MOCK_CATEGORIES.keys())}"}), 400
    
    # Choose secret word and generate unique ID
    secret_word = random.choice(MOCK_CATEGORIES[category])
    game_id = str(uuid.uuid4())
    
    new_game_document = {
        "_id": game_id,
        "category": category,
        "secret_answer": secret_word,
        "question_count": 0,
        "max_questions": 20,
        "game_stage": "PLAYING",
        "chat_history": [],
        "game_result": None
    }
    
    try:
        # Save the record to our database
        games_collection = get_games_collection()
        games_collection.insert_one(new_game_document)
        
        return jsonify({
            "game_id": game_id,
            "category": category,
            "max_questions": 20,
            "game_stage": "PLAYING"
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Database insertion crash on game initialization: {e}")
        return jsonify({"error": "Failed to create game session due to an internal server error."}), 500
    

@api_bp.route("/api/game/question", methods=["POST"])
def execute_turn():
    """
    Processes a single yes/no question turn.
    Expects JSON input: { "game_id": UUID-STRING, "question_text": "Is it a fruit?" }
    Returns JSON: {"game_id", "response", "question_count", "game_stage"} 200 if successful
    """

    data = request.get_json() or {}
    game_id = data.get("game_id", "").strip()
    question_text = data.get("question_text", "").strip()
    
    # 1. Validation checks on incoming request parameters
    if not game_id or not question_text:
        return jsonify({"error": "Missing game_id or question_text in request body."}), 400
        
    games_collection = get_games_collection()
    
    # 2. Fetch current game state
    game = games_collection.find_one({"_id": game_id})
    if not game:
        return jsonify({"error": "Game session not found."}), 404
        
    if game["game_stage"] == "GAME_OVER":
        return jsonify({"error": "This match has already ended."}), 400
        
    if game["game_stage"] == "FINAL_GUESS":
        return jsonify({
            "error": "You have exhausted your questions! You must make a final guess.",
            "game_stage": "FINAL_GUESS"
        }), 400
    
    current_count = game["question_count"]
    max_questions = game["max_questions"]
    
    if current_count >= max_questions:
        return jsonify({
            "error": "You have exhausted your 20 questions! You must make a final guess.",
            "game_stage": "FINAL_GUESS"
        }), 400

    # 3. Get LLM response
    decision, analysis = ask_llm(
        task_type=LLMTask.YES_NO_QUESTION,
        category=game["category"],
        answer=game["secret_answer"],
        question=question_text
    )
    
    new_count = current_count + 1
    
    new_stage = "PLAYING" if new_count < max_questions else "FINAL_GUESS"

    # 4. Save new chat history block 
    new_turn_history = {
        "type": "question",
        "text": question_text,
        "response": decision,
        "analysis": analysis
    }
    
    try:
        games_collection.update_one(
            {"_id": game_id},
            {
                "$set": {
                    "question_count": new_count,
                    "game_stage": new_stage
                },
                "$push": {
                    "chat_history": new_turn_history
                }
            }
        )
        
        # 5. Return response to frontend. 
        return jsonify({
            "game_id": game_id,
            "response": decision,
            "question_count": new_count,
            "game_stage": new_stage
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Database update crash during question processing: {e}")
        return jsonify({"error": "Internal server database modification failure."}), 500
    
@api_bp.route("/api/game/guess", methods=["POST"])
def submit_guess():
    data = request.get_json() or {}
    game_id = data.get("game_id", "").strip()
    guess_text = data.get("guess_text", "").strip()
    
    if not game_id or not guess_text:
        return jsonify({"error": "Missing game_id or guess_text in request body."}), 400
        
    games_collection = get_games_collection()
    game = games_collection.find_one({"_id": game_id})
    if not game:
        return jsonify({"error": "Game session not found."}), 404
        
    if game["game_stage"] == "GAME_OVER":
        return jsonify({"error": "This match has already ended."}), 400

    # 1. Evaluate the semantic accuracy of the guess via LLM
    decision, analysis = ask_llm(
        task_type=LLMTask.CHECK_FINAL_ANSWER,
        guess=guess_text,
        answer=game["secret_answer"]
    )
    
    current_count = game["question_count"] + 1 
    max_questions = game["max_questions"]
    current_stage = game["game_stage"]
    
    # 2. Determine game structural logic branch outcomes
    if decision == "yes":   # We end the game regardless of current state
        new_stage = "GAME_OVER"
        result = "WIN"
    else:
        if current_stage == "FINAL_GUESS" or current_count >= max_questions:
            new_stage = "GAME_OVER"
            result = "LOSE"
        # Still have remaining questions
        else:
            new_stage = "PLAYING"
            result = None

    # 3. Append history payload log
    new_guess_history = {
        "type": "guess",
        "text": guess_text,
        "response": "Correct" if decision == "yes" else "Incorrect",
        "analysis": analysis
    }
    
    try:
        games_collection.update_one(
            {"_id": game_id},
            {
                "$set": {
                    "question_count": current_count,
                    "game_stage": new_stage,
                    "game_result": result
                },
                "$push": {
                    "chat_history": new_guess_history
                }
            }
        )
        
        # 4. Formulate standard payload response back to JavaScript
        response_payload = {
            "game_id": game_id,
            "game_stage": new_stage,
            "game_result": result,
            "response": "Correct" if decision == "yes" else "Incorrect",
            "question_count": current_count
        }
        
        if new_stage == "GAME_OVER":
            response_payload["secret_answer"] = game["secret_answer"]
            
        return jsonify(response_payload), 200
        
    except Exception as e:
        current_app.logger.error(f"Database update crash during guess resolution: {e}")
        return jsonify({"error": "Internal server database modification failure."}), 500