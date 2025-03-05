from flask import Blueprint, request, jsonify
from bson import ObjectId
from extensions import mongo
from models.media_type import MediaLibrary
from datetime import datetime
import cloudinary
import cloudinary.uploader
bp = Blueprint('media_type', __name__, url_prefix='/api/types')
cloudinary.config(
    cloud_name="ddqqd5hju",
    api_secret="_5-ekzPeYT5JA2xCr_EvI870Z9I",
    api_key="342194671316377"
)
# Create a new media entry
@bp.route('/media', methods=['POST'])
def create_media():
    data = request.json
    if 'user_id' not in data:
        return jsonify({"message": "User ID is required"}), 400

    media = MediaLibrary(
        image=data['image'],
        prompt=data['prompt'],
        media_type=data['media_type'],
        user_id=data['user_id'],  # Associate with a user
        public_id=data['public_id'] )
    
    result = mongo.db.media_type.insert_one(media.to_dict())
    return jsonify({"message": "Media created", "id": str(result.inserted_id)}), 201


@bp.route('/media/user/<user_id>', methods=['GET'])
def get_media_by_user(user_id):
    # Get query parameters for date range
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    print(from_date , to_date)
    # Base query to filter by user_id
    query = {"user_id": user_id}

    # Add date range filtering if from_date and to_date are provided
    if from_date and to_date:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d')
            query["created_at"] = {"$gte": from_date, "$lte": to_date}
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Fetch media entries based on the query
    media_list = list(mongo.db.media_type.find(query))
    
    # Convert ObjectId to string for JSON serialization
    for media in media_list:
        media['_id'] = str(media['_id'])
        media['user_id'] = str(media['user_id'])
    
    return jsonify(media_list), 200

# Update a media entry by ID
@bp.route('/media/<id>', methods=['PUT'])
def update_media(id):
    data = request.json
    if 'user_id' not in data:
        return jsonify({"message": "User ID is required"}), 400

    media = mongo.db.media_type.find_one({"_id": ObjectId(id), "user_id": ObjectId(data['user_id'])})
    if not media:
        return jsonify({"message": "Media not found or unauthorized"}), 404

    update_data = {k: data[k] for k in ['image', 'prompt', 'media_type'] if k in data}
    update_data['updated_at'] = datetime.utcnow()

    mongo.db.media_type.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    return jsonify({"message": "Media updated"}), 200


# Delete a media entry by ID
@bp.route('/media/<id>', methods=['DELETE'])
def delete_media(id):
    data = request.json
    if 'user_id' not in data:
        return jsonify({"message": "User ID is required"}), 400

    # Find the media in MongoDB
    media = mongo.db.media_type.find_one({"_id": ObjectId(id), "user_id": data['user_id']})
    
    if not media:
        return jsonify({"message": "Media not found or unauthorized"}), 404

    # Extract Cloudinary public_id from the database
    public_id = media.get("public_id")
    if not public_id:
        return jsonify({"message": "No Cloudinary ID found for this media"}), 400

    try:
        # Delete from Cloudinary
        cloudinary_res = cloudinary.uploader.destroy(public_id)
        if cloudinary_res.get("result") != "ok":
            return jsonify({"message": "Failed to delete from Cloudinary"}), 500

        # Delete from MongoDB
        mongo.db.media_type.delete_one({"_id": ObjectId(id), "user_id": data['user_id']})

        return jsonify({"message": "Media deleted from Cloudinary and database"}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
