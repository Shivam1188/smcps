from flask import Blueprint, request, jsonify
from extensions import mongo
from models.user import User
from bson.objectid import ObjectId 
import os
from werkzeug.utils import secure_filename
import base64
import requests
bp = Blueprint('profile', __name__, url_prefix='/api')

# Configure upload folder
UPLOAD_FOLDER = 'uploads/profile_pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @bp.route("/profile", methods=["POST"])
# def create_profile():
#     data = request.form
#     profile_picture = request.files.get("profile_picture")

#     # Validate required fields
#     if not all(key in data for key in ("email", "password", "confirm_password", "full_name")):
#         return jsonify({"error": "Missing required fields"}), 400

#     if data["password"] != data["confirm_password"]:
#         return jsonify({"error": "Passwords do not match"}), 400

#     # Save profile picture if provided
#     picture_path = None
#     if profile_picture and allowed_file(profile_picture.filename):
#         filename = secure_filename(profile_picture.filename)
#         picture_path = os.path.join(UPLOAD_FOLDER, filename)
#         profile_picture.save(picture_path)

#     # Create a new user
#     user = User(
#         email=data["email"],
#         password=data["password"],
#         full_name=data["full_name"],
#         business_name=data.get("business_name"),
#         profile_picture=picture_path
#     )

#     # Insert into the database
#     user_id = mongo.db.users.insert_one(user.to_dict()).inserted_id
#     return jsonify({"message": "User created successfully", "user_id": str(user_id)}), 201

@bp.route("/profile/<user_id>", methods=["GET"])
def get_profile(user_id):
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404

        user["_id"] = str(user["_id"])
        return jsonify(user), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route("/profile/<user_id>", methods=["PUT"])
def update_profile(user_id):
    data = request.json  # Get JSON payload
    updates = {}
    print(data)
    try:
        # Process Base64-encoded profile picture
        profile_picture = data.get("profile_picture")
        if profile_picture:
            
            updates["profile_picture"] = profile_picture  # Save path to DB

        # Update preferences if provided
        if "preferences" in data:
            updates["preferences"] = data["preferences"]

        # Update other fields if provided
        user_fields = [
            "full_name", "business_name", "date_of_birth", "phone_number",
            "country", "city", "postal_code"
        ]
        for field in user_fields:
            if field in data:
                updates[field] = data[field]

        # Update user in the database
        if updates:
            mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
            return jsonify({"message": "Profile updated successfully"}), 200
        else:
            return jsonify({"error": "No updates provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route("/profile/<user_id>", methods=["DELETE"])
def delete_profile(user_id):
    try:
        result = mongo.db.users.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "Profile deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/countries", methods=["GET"])
def get_countries():
    try:
        # Fetch data from an external API
        response = requests.get("https://restcountries.com/v3.1/all")
        if response.status_code == 200:
            countries = [country["name"]["common"] for country in response.json()]
            return jsonify({"countries": countries}), 200  # Return JSON-serializable data
        else:
            return jsonify({"error": "Failed to fetch countries"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/cities/<country_name>", methods=["GET"])
def get_cities(country_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search?country={country_name}&format=json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            cities = list(set([place["display_name"].split(",")[0] for place in data]))  # Extract unique city names
            return jsonify({"cities": cities}), 200
        else:
            return jsonify({"error": "Failed to fetch cities"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500