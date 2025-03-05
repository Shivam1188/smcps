from flask import Blueprint, request, jsonify
from routes.ai_model import AIFunctions
from models.ai_response import AiResponse
import os
import openai
from extensions import mongo
from datetime import datetime
# Initialize Blueprint
bp = Blueprint('ai_content', __name__, url_prefix='/api/openai')

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")


@bp.route("/generate-image", methods=["POST"])
def generate_image():
    """
    API endpoint to generate an image using OpenAI's DALL·E model.
    Request body should include:
    - prompt (str): The text description for the image generation.
    - user_id (str): The ID of the user making the request.
    """
    try:
        data = request.json

        if not data or 'prompt' not in data or 'user_id' not in data:
            return jsonify({"error": "Prompt and user_id are required"}), 400

        prompt = data['prompt']
        user_id = data['user_id']  # Extract user_id from request body

        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        image_url = response["data"][0]["url"]
        ai_response = AiResponse(image_url, prompt, user_id)  # Pass user_id
        mongo.db.ai_responses.insert_one(ai_response.to_dict())

        response_data = jsonify({
            "prompt": prompt,
            "image_url": image_url
        })

        response_data.headers.add("Access-Control-Allow-Origin", "*")  # Allow CORS for all origins

        return response_data, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    """
    API endpoint to generate an image using OpenAI's DALL·E model.
    Request body should include:
    - prompt (str): The text description for the image generation.
    - user_id (str): The ID of the user making the request.
    """
    try:
        data = request.json

        if not data or 'prompt' not in data or 'user_id' not in data:
            return jsonify({"error": "Prompt and user_id are required"}), 400

        prompt = data['prompt']
        user_id = data['user_id']  # Extract user_id from request body

        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        image_url = response["data"][0]["url"]
        ai_response = AiResponse(image_url, prompt, user_id)  # Pass user_id
        mongo.db.ai_responses.insert_one(ai_response.to_dict())

        response_data = jsonify({
            "prompt": prompt,
            "image_url": image_url
        })

        response_data.headers.add("Access-Control-Allow-Origin", "*")  # Allow CORS for all origins

        return response_data, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/ai-responses", methods=["GET"])
def get_ai_responses_by_user():
    """
    API endpoint to get paginated AI-generated responses for a specific user.
    Query parameters:
    - user_id (str): The ID of the user whose AI responses should be retrieved.
    - page (int, optional): The page number (default: 1).
    - limit (int, optional): The number of results per page (default: 10).
    """
    try:
        user_id = request.args.get("user_id")
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=10, type=int)

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Calculate pagination values
        skip = (page - 1) * limit
        total_count = mongo.db.ai_responses.count_documents({"user_id": user_id})
        total_pages = (total_count + limit - 1) // limit  # Ceiling division

        # Fetch paginated results sorted by created_at (descending)
        responses = list(
            mongo.db.ai_responses.find({"user_id": user_id})
            .sort("created_at", -1)  # -1 for descending order
            .skip(skip)
            .limit(limit)
        )

        # Convert ObjectId and datetime fields to string format
        for response in responses:
            response["_id"] = str(response["_id"])
            
            # Ensure created_at and updated_at exist before calling isoformat
            if isinstance(response.get("created_at"), datetime):
                response["created_at"] = response["created_at"].isoformat()
            if isinstance(response.get("updated_at"), datetime):
                response["updated_at"] = response["updated_at"].isoformat()

        return jsonify({
            "total_count": total_count,
            "current_page": page,
            "total_pages": total_pages,
            "ai_responses": responses
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/generate-script", methods=["POST"])
def generate_script():
    """
    API endpoint to generate a video script
    Request body should include:
    - content_theme (str)
    - video_format (str)
    - tone (str)
    - target_audience (str)
    - keywords (list of str)
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['content_theme', 'video_format', 'tone', 'target_audience', 'keywords']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        generated_script = AIFunctions.generate_script(
            data['content_theme'], 
            data['video_format'], 
            data['tone'], 
            data['target_audience'], 
            data['keywords']
        )
        
        return jsonify({
            "script": generated_script
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/suggest-visual-style", methods=["GET"])
def suggest_visual_style():
    """
    API endpoint to suggest visual style based on target platform
    Query parameter: platform (str)
    """
    platform = request.args.get('platform', 'default')
    
    suggested_style = AIFunctions.suggest_visual_style(
        content_theme="default", 
        target_platform=platform
    )
    
    return jsonify({
        "platform": platform,
        "suggested_style": suggested_style
    }), 200

@bp.route("/analyze-sentiment", methods=["POST"])
def analyze_sentiment():
    """
    API endpoint to analyze sentiment of a script
    Request body should include:
    - script (str)
    """
    try:
        data = request.json
        
        if not data or 'script' not in data:
            return jsonify({"error": "Script is required"}), 400
        
        script = data['script']
        
        sentiment = AIFunctions.analyze_sentiment(script)
        
        return jsonify({
            "script": script,
            "sentiment": sentiment
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/suggest-posting-time", methods=["GET"])
def suggest_posting_time():
    """
    API endpoint to suggest optimal posting time
    Query parameter: platform (str)
    """
    platform = request.args.get('platform', 'default')
    
    suggested_time = AIFunctions.suggest_posting_time(platform)
    
    return jsonify({
        "platform": platform,
        "suggested_posting_time": suggested_time
    }), 200

@bp.route("/generate-qc-feedback", methods=["POST"])
def generate_qc_feedback():
    """
    API endpoint to generate QC feedback
    Request body should include:
    - script (str)
    - video_style (str)
    """
    try:
        data = request.json
        
        if not data or 'script' not in data or 'video_style' not in data:
            return jsonify({"error": "Script and video style are required"}), 400
        
        script = data['script']
        video_style = data['video_style']
        
        qc_feedback = AIFunctions.generate_qc_feedback(script, video_style)
        
        return jsonify({
            "script": script,
            "video_style": video_style,
            "qc_feedback": qc_feedback
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
