from flask import Blueprint, request, jsonify
from bson import ObjectId
from extensions import mongo
from models.media import Media
from routes.ai_model import AIFunctions
from datetime import datetime

bp = Blueprint('media', __name__, url_prefix='/api/media')

# Helper function to convert ObjectId to string
def objectid_to_str(o):
    return str(o) if isinstance(o, ObjectId) else o

# Route to create new media using AI
@bp.route('/ai', methods=['POST'])
def create_media_with_ai():
    data = request.get_json()
    
    # Get user input for content generation
    content_theme = data.get('content_theme')
    video_format = data.get('video_format')
    tone = data.get('tone')
    target_audience = data.get('target_audience')
    keywords = data.get('keywords', [])
    target_platform = data.get('target_platform')

    # Step 1: Use AI to generate the script for the media
    script = AIFunctions.generate_script(content_theme, video_format, tone, target_audience, keywords)

    # Step 2: Use AI to suggest a visual style based on the platform
    visual_style = AIFunctions.suggest_visual_style(content_theme, target_platform)

    # Step 3: Use AI to analyze the sentiment of the generated script
    sentiment = AIFunctions.analyze_sentiment(script)

    # Step 4: Generate QC feedback using AI
    qc_feedback = AIFunctions.generate_qc_feedback(script, visual_style)

    # Step 5: Use AI to suggest the best posting time
    posting_time = AIFunctions.suggest_posting_time(target_platform)

    # Create media object with generated AI content
    media = Media(
        content_id=ObjectId(),  # Generate a new ObjectId
        visual_style=visual_style,
        target_platform=target_platform,
        video_length=data.get('video_length'),  # Video length from user input
        custom_assets=data.get('custom_assets', []),
        animation_settings=data.get('animation_settings', {}),
        audio_settings=data.get('audio_settings', {}),
        qc_feedback=qc_feedback
    )

    media_dict = media.to_dict()
    
    # Insert media object into MongoDB
    mongo.db.media.insert_one(media_dict)

    # Return the media content along with AI-generated information
    return jsonify({
        "message": "Media created successfully",
        "content_id": str(media.content_id),
        "script": script,
        "visual_style": visual_style,
        "sentiment": sentiment,
        "qc_feedback": qc_feedback,
        "posting_time": posting_time
    }), 201

# Route to get all media
@bp.route('/', methods=['GET'])
def get_all_media():
    media_items = mongo.db.media.find()
    result = []
    for media in media_items:
        media['_id'] = objectid_to_str(media['_id'])
        result.append(media)
    return jsonify(result), 200

# Route to get media by content_id
@bp.route('/<content_id>', methods=['GET'])
def get_media(content_id):
    media = mongo.db.media.find_one({"content_id": ObjectId(content_id)})
    if media:
        media['_id'] = objectid_to_str(media['_id'])
        return jsonify(media), 200
    else:
        return jsonify({"message": "Media not found"}), 404

# Route to update media by content_id
@bp.route('/<content_id>', methods=['PUT'])
def update_media(content_id):
    data = request.get_json()
    updated_media = {
        "visual_style": data.get('visual_style'),
        "target_platform": data.get('target_platform'),
        "video_length": data.get('video_length'),
        "custom_assets": data.get('custom_assets', []),
        "animation_settings": data.get('animation_settings', {}),
        "audio_settings": data.get('audio_settings', {}),
        "qc_feedback": data.get('qc_feedback', []),
        "status": data.get('status', 'draft'),
        "created_at": datetime.utcnow()
    }

    result = mongo.db.media.update_one(
        {"content_id": ObjectId(content_id)},
        {"$set": updated_media}
    )
    
    if result.matched_count > 0:
        return jsonify({"message": "Media updated successfully"}), 200
    else:
        return jsonify({"message": "Media not found"}), 404

# Route to delete media by content_id
@bp.route('/<content_id>', methods=['DELETE'])
def delete_media(content_id):
    result = mongo.db.media.delete_one({"content_id": ObjectId(content_id)})
    if result.deleted_count > 0:
        return jsonify({"message": "Media deleted successfully"}), 200
    else:
        return jsonify({"message": "Media not found"}), 404
