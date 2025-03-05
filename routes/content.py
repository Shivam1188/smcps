from flask import Blueprint, request, jsonify
from bson import ObjectId
from extensions import mongo
from models.content import Content
from auth_middleware import token_required, admin_required
from routes.ai_model import AIFunctions

bp = Blueprint('content', __name__, url_prefix='/api/content')

@bp.route('/', methods=['GET'])
@token_required
def get_content(current_user):
    # Users can only see their content, admins can see all
    if current_user['role'] == 'admin':
        content = list(mongo.db.content.find())
    else:
        content = list(mongo.db.content.find({'user_id': str(current_user['_id'])}))
    
    for item in content:
        item['_id'] = str(item['_id'])
    return jsonify(content), 200

@bp.route('/', methods=['POST'])
@token_required
def create_content(current_user):
    data = request.get_json()
    generated_script = AIFunctions.generate_script(
        content_theme=data['content_theme'],
        video_format=data['video_format'],
        tone=data['tone'],
        target_audience=data['target_audience'],
        keywords=data.get('keywords', [])
    )
    
    content = Content(
        title=data['title'],
        content_theme=data['content_theme'],
        target_audience=data['target_audience'],
        video_format=data['video_format'],
        tone=data['tone'],
        platform=data['platform'],
        keywords=data.get('keywords', []),
        hashtags=data.get('hashtags', []),
        user_id=str(current_user['_id']),
        reference_files=data.get('reference_files', []),
    )
    content.generated_script = generated_script
    
    result = mongo.db.content.insert_one(content.to_dict())
    return jsonify({'message': 'Content created', 'id': str(result.inserted_id), 'generated_script': generated_script}), 201

@bp.route('/<content_id>', methods=['PUT'])
@token_required
def update_content(current_user, content_id):
    data = request.get_json()
    try:
        # Check ownership or admin status
        content = mongo.db.content.find_one({'_id': ObjectId(content_id)})
        if not content:
            return jsonify({'message': 'Content not found'}), 404
        
        if str(content['user_id']) != str(current_user['_id']) and current_user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
        
        # If script-related fields are updated, regenerate the script
        if 'content_theme' in data or 'video_format' in data or 'tone' in data or 'target_audience' in data or 'keywords' in data:
            data['generated_script'] = AIFunctions.generate_script(
                content_theme=data.get('content_theme', content['content_theme']),
                video_format=data.get('video_format', content['video_format']),
                tone=data.get('tone', content['tone']),
                target_audience=data.get('target_audience', content['target_audience']),
                keywords=data.get('keywords', content.get('keywords', []))
            )
        
        mongo.db.content.update_one(
            {'_id': ObjectId(content_id)},
            {'$set': data}
        )
        return jsonify({'message': 'Content updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': 'Error updating content', 'error': str(e)}), 400