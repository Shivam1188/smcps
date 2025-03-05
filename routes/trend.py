import requests
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from models.trend import Trend, InstagramTrend
from extensions import mongo
from auth_middleware import token_required
import re
from bson.json_util import dumps
from flask_cors import cross_origin
import ast
import googleapiclient.discovery
from typing import List, Dict
import json

bp = Blueprint('trend', __name__, url_prefix='/api/trends')
# bp = Blueprint('instagram_trend', __name__, url_prefix='/api/instagram-trends')

def clean_views_count(views_text):
    """Convert various view count formats to integer."""
    if isinstance(views_text, (int, float)):
        return int(views_text)
    
    if not isinstance(views_text, str):
        return 0
        
    views_text = views_text.upper().replace('VIEWS', '').strip()
    try:
        if 'K' in views_text:
            return int(float(views_text.replace('K', '')) * 1000)
        elif 'M' in views_text:
            return int(float(views_text.replace('M', '')) * 1000000)
        elif 'B' in views_text:
            return int(float(views_text.replace('B', '')) * 1000000000)
        else:
            number = ''.join(filter(str.isdigit, views_text))
            return int(number) if number else 0
    except (ValueError, TypeError):
        return 0

def validate_video_data(video):
    """Validate and clean individual video data."""
    if not isinstance(video, dict):
        return None
        
    try:
        if not video.get('title') or not video.get('id'):
            return None

        channel_data = video.get('channel', {})
        if not isinstance(channel_data, dict):
            channel_data = {}
        def parse_thumbnail(thumbnail):
            if isinstance(thumbnail, str):  
                try:
                    return ast.literal_eval(thumbnail)  # Convert string to dict safely
                except (SyntaxError, ValueError):  
                    return {"static": thumbnail, "rich": thumbnail}  # Fallback to simple URL
            return thumbnail  # Already a dict, return as is
        return {
            "title": str(video.get('title', '')).strip(),
            "video_id": str(video.get('id', '')),
            "views": clean_views_count(video.get('views', 0)),
            "published_time": str(video.get('published_time', '')),
            "channel": {
                "title": str(channel_data.get('title', 'Unknown')),
                "link": str(channel_data.get('link', '')),
                "thumbnail": parse_thumbnail(channel_data.get('thumbnail', ''))
            },
            "length": str(video.get('length', '')),
            "thumbnail": parse_thumbnail(video.get('thumbnail', '')),   
            "link": str(video.get('link', '')),
            "is_short": bool(video.get('is_short', False))
        }
    except Exception as e:
        print(f"Error validating video data: {str(e)}")
        return None
    
def fetch_trending_videos(category="gaming"):
    """Fetch latest trending YouTube videos with robust error handling."""
    # Get API configuration from environment variables with fallbacks
    api_key = current_app.config['SEARCH_API_KEY']
    api_url = current_app.config['SEARCH_API_URL']

    # Debug logging
    print(f"Using API URL: {api_url}")
    print(f"Category: {category}")

    params = {
        "engine": "youtube",  # Changed to 'youtube' instead of 'youtube_trends'
        "api_key": api_key,
        "type": "video",      # Specify type as video
        "q": f"trending {category}",  # Add search query
        "sort_by": "date",    # Sort by date to get recent videos
        "time": "month"       # Time range
    }

    try:
        # Make the API request with debugging
        print(f"Making request to {api_url} with params: {params}")
        response = requests.get(api_url, params=params, timeout=10)
        
        # Debug response
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        response.raise_for_status()
        
        # Handle potential encoding issues
        text_response = response.text.strip()
        if not text_response:
            return {"success": False, "error": "Empty response from API"}

        print(f"Raw response: {text_response[:500]}...")  # Print first 500 chars of response
        
        data = response.json()
        
        # Debug the parsed JSON
        print(f"Parsed JSON structure: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # Check for different possible response structures
        videos = []
        if isinstance(data, dict):
            videos = (data.get("video_results", []) or 
                     data.get("videos", []) or 
                     data.get("organic_results", []) or 
                     data.get("results", []))
        elif isinstance(data, list):
            videos = data

        if not videos:
            return {"success": False, "error": f"No trending {category} videos found"}

        # Process and validate each video
        valid_videos = []
        for video in videos:
            processed_video = validate_video_data(video)
            if processed_video:
                valid_videos.append(processed_video)

        if not valid_videos:
            return {"success": False, "error": "No valid video data found in response"}

        return {"success": True, "data": valid_videos}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "API request timed out"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API request failed: {str(e)}"}
    except ValueError as e:
        return {"success": False, "error": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@bp.route('/', methods=['GET'])
@cross_origin(origins="*")
@token_required
def get_trends(current_user):
    """Fetch and store YouTube trending videos with improved error handling."""
    try:
        category = request.args.get('category', 'gaming')
        result = fetch_trending_videos(category)

        if not result["success"]:
            return jsonify({
                "success": False,
                "message": result["error"]
            }), 500

        trends = []
        for item in result["data"]:
            try:
                trend = Trend(
                    title=item["title"],
                    platform="YouTube",
                    engagement_metrics={
                        "views": item["views"],
                        "published_time": item["published_time"],
                        "channel": item["channel"]["title"],
                        "channel_link": item["channel"]["link"],
                        "length": item["length"],
                        "thumbnail": item["thumbnail"],
                        "video_link": item["link"],
                        "video_id": item["video_id"],
                        "is_short": item.get("is_short", False)
                    },
                    sentiment_score=None
                )

                result = mongo.db.trends.insert_one(trend.to_dict())
                trend_data = trend.to_dict()
                trend_data["_id"] = str(result.inserted_id)
                trends.append(trend_data)

            except Exception as e:
                print(f"Error processing trend item: {str(e)}")
                continue

        if not trends:
            return jsonify({
                "success": False,
                "message": "No valid trends could be processed"
            }), 500

        return jsonify({
            "success": True,
            "data": trends,
            "count": len(trends)
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500
    

@bp.route('/get_trends', methods=['GET'])
@token_required
def fetch_db_trends(current_user):
    try:
        # Fetch all documents from the 'trends' collection
        trends = mongo.db.trends.find()
        
        # Convert the cursor to a list and then to JSON format
        trends_list = list(trends)
        return jsonify({"success": True, "data": dumps(trends_list)}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@bp.route('/<trend_id>', methods=['PUT'])
@token_required
def update_trend(current_user, trend_id):
    """Update an existing trend."""
    try:
        if not ObjectId.is_valid(trend_id):
            return jsonify({
                "success": False,
                "message": "Invalid trend ID format"
            }), 400

        # Get the request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No update data provided"
            }), 400

        # Find the existing trend
        existing_trend = mongo.db.trends.find_one({'_id': ObjectId(trend_id)})
        if not existing_trend:
            return jsonify({
                "success": False,
                "message": "Trend not found"
            }), 404

        # Validate and prepare update data
        update_data = {}
        
        # Update title if provided
        if 'title' in data:
            update_data['title'] = str(data['title']).strip()

        # Update platform if provided
        if 'platform' in data:
            update_data['platform'] = str(data['platform']).strip()

        # Update engagement metrics if provided
        if 'engagement_metrics' in data:
            metrics = data['engagement_metrics']
            if not isinstance(metrics, dict):
                return jsonify({
                    "success": False,
                    "message": "Invalid engagement metrics format"
                }), 400

            # Validate and clean engagement metrics
            cleaned_metrics = {
                "views": clean_views_count(metrics.get('views', existing_trend['engagement_metrics']['views'])),
                "published_time": str(metrics.get('published_time', existing_trend['engagement_metrics']['published_time'])),
                "channel": str(metrics.get('channel', existing_trend['engagement_metrics']['channel'])),
                "channel_link": str(metrics.get('channel_link', existing_trend['engagement_metrics']['channel_link'])),
                "length": str(metrics.get('length', existing_trend['engagement_metrics']['length'])),
                "thumbnail": str(metrics.get('thumbnail', existing_trend['engagement_metrics']['thumbnail'])),
                "video_link": str(metrics.get('video_link', existing_trend['engagement_metrics']['video_link'])),
                "video_id": str(metrics.get('video_id', existing_trend['engagement_metrics']['video_id'])),
                "is_short": bool(metrics.get('is_short', existing_trend['engagement_metrics']['is_short']))
            }
            update_data['engagement_metrics'] = cleaned_metrics

        # Update sentiment score if provided
        if 'sentiment_score' in data:
            update_data['sentiment_score'] = data['sentiment_score']

        # Add updated_at timestamp
        update_data['updated_at'] = datetime.utcnow()

        # Perform the update
        result = mongo.db.trends.update_one(
            {'_id': ObjectId(trend_id)},
            {'$set': update_data}
        )

        if result.modified_count == 0:
            return jsonify({
                "success": False,
                "message": "No changes made to the trend"
            }), 400

        # Get the updated trend
        updated_trend = mongo.db.trends.find_one({'_id': ObjectId(trend_id)})
        updated_trend['_id'] = str(updated_trend['_id'])

        return jsonify({
            "success": True,
            "message": "Trend updated successfully",
            "data": updated_trend
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error updating trend: {str(e)}"
        }), 500


@bp.route('/<trend_id>', methods=['DELETE'])
@token_required
def delete_trend(current_user, trend_id):
    """Delete a trend by ID."""
    try:
        if not ObjectId.is_valid(trend_id):
            return jsonify({
                "success": False,
                "message": "Invalid trend ID format"
            }), 400

        # Find the trend first to confirm it exists
        existing_trend = mongo.db.trends.find_one({'_id': ObjectId(trend_id)})
        if not existing_trend:
            return jsonify({
                "success": False,
                "message": "Trend not found"
            }), 404

        # Perform the deletion
        result = mongo.db.trends.delete_one({'_id': ObjectId(trend_id)})

        if result.deleted_count == 0:
            return jsonify({
                "success": False,
                "message": "Failed to delete trend"
            }), 500

        return jsonify({
            "success": True,
            "message": "Trend deleted successfully",
            "deleted_id": trend_id
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error deleting trend: {str(e)}"
        }), 500

# Optional: Add a bulk delete route for multiple trends
@bp.route('/bulk-delete', methods=['POST'])
@token_required
def bulk_delete_trends(current_user):
    """Delete multiple trends by IDs."""
    try:
        data = request.get_json()
        if not data or 'trend_ids' not in data:
            return jsonify({
                "success": False,
                "message": "No trend IDs provided"
            }), 400

        trend_ids = data['trend_ids']
        if not isinstance(trend_ids, list):
            return jsonify({
                "success": False,
                "message": "trend_ids must be an array"
            }), 400

        # Validate all IDs first
        valid_ids = []
        invalid_ids = []
        for trend_id in trend_ids:
            if ObjectId.is_valid(trend_id):
                valid_ids.append(ObjectId(trend_id))
            else:
                invalid_ids.append(trend_id)

        if invalid_ids:
            return jsonify({
                "success": False,
                "message": "Invalid trend ID format",
                "invalid_ids": invalid_ids
            }), 400

        # Perform the bulk deletion
        result = mongo.db.trends.delete_many({'_id': {'$in': valid_ids}})

        return jsonify({
            "success": True,
            "message": "Trends deleted successfully",
            "deleted_count": result.deleted_count,
            "deleted_ids": [str(id) for id in valid_ids]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error deleting trends: {str(e)}"
        }), 500


class SocialMediaTrends:
    def __init__(self, youtube_api_key: str):
        self.youtube_api_key = youtube_api_key

    def init_youtube(self):
        """Initialize YouTube API client"""
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        return googleapiclient.discovery.build(
            "youtube", "v3", 
            developerKey=self.youtube_api_key
        )

    def get_youtube_trending_videos(self, region_code: str = "IN", max_results: int = 50) -> List[Dict]:
        """Fetch trending YouTube videos"""
        try:
            youtube = self.init_youtube()
            request = youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region_code,
                maxResults=max_results
            )
            response = request.execute()

            trending_videos = []
            for item in response.get("items", []):
                video_data = {
                    "title": item["snippet"]["title"],
                    "video_url": f"https://www.youtube.com/watch?v={item['id']}",
                    "views": int(item["statistics"].get("viewCount", 0)),
                    "likes": int(item["statistics"].get("likeCount", 0)),
                    "comments": int(item["statistics"].get("commentCount", 0)),
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"]
                }
                trending_videos.append(video_data)

            return trending_videos

        except Exception as e:
            print(f"Error fetching YouTube videos: {str(e)}")
            return []

    def save_to_file(self, data: Dict, filename: str):
        """Save the trending data to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {str(e)}")

            
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
tracker = SocialMediaTrends(youtube_api_key=YOUTUBE_API_KEY)

@bp.route('/trending_videos', methods=['GET'])
def get_trending_videos():
    """
    API endpoint to fetch trending YouTube videos
    Optional query parameters:
    - region: Country code (default: 'IN')
    - max_results: Number of results (default: 50, max: 50)
    """
    # Get query parameters with defaults
    region = request.args.get('region', 'IN')
    max_results = request.args.get('max_results', 50, type=int)
    max_results = min(max_results, 50)  # Ensure max 50 results

    try:
        # Fetch trending videos
        trending_videos = tracker.get_youtube_trending_videos(
            region_code=region, 
            max_results=max_results
        )

        # Prepare response
        response = {
            "trending_videos": trending_videos,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "region": region,
            "total_videos": len(trending_videos)
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to fetch trending videos"
        }), 500

### For Instagram Hastags Trending #############

def fetch_instagram_data_from_serpapi(query):
    try:
        SERPAPI_API_URL = current_app.config['SERPAPI_API_URL']
        SERPAPI_KEY = current_app.config['SERPAPI_KEY']
        params = {
            'q': query,
            'engine': 'google',  # Changed from google_videos to google
            'hl': 'en',
            'gl': 'in',
            'api_key': SERPAPI_KEY
        }
        
        response = requests.get(SERPAPI_API_URL, params=params)
        response.raise_for_status()

        data = response.json()
        # Modified to handle different response structure
        if not data or ('error' in data and data['error']):
            return None
        
        return data
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"SerpAPI request failed: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error in fetch_instagram_data_from_serpapi: {str(e)}")
        return None

@bp.route('/ig', methods=['POST'])
@token_required
def create_instagram_trend(current_user):
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        hashtag = request.json.get('hashtag')
        if not hashtag:
            return jsonify({"error": "Hashtag is required"}), 400

        # Sanitize hashtag
        hashtag = hashtag.strip().lower().replace('#', '')
        
        data = fetch_instagram_data_from_serpapi(f"instagram {hashtag} trending")
        if not data:
            return jsonify({"error": "Failed to fetch data from SerpApi"}), 500

        instagram_trend = InstagramTrend(hashtag=hashtag, data=data)
        result = mongo.db.instagram_trends.insert_one(instagram_trend.to_dict())
        
        # Add _id to the response
        response_data = instagram_trend.to_dict()
        response_data['_id'] = str(result.inserted_id)
        
        return jsonify({
            "message": "Instagram trend created successfully", 
            "trend": response_data
        }), 201

    except Exception as e:
        current_app.logger.error(f"Error in create_instagram_trend: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@bp.route('/ig', methods=['GET'])   
def get_instagram_trends():
    try:
        trends = list(mongo.db.instagram_trends.find())
        # Convert ObjectId to string for JSON serialization
        for trend in trends:
            trend['_id'] = str(trend['_id'])
        return jsonify(trends), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_instagram_trends: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@bp.route('/ig/<id>', methods=['GET'])
def get_instagram_trend(id):
    try:
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Invalid ID format"}), 400

        trend = mongo.db.instagram_trends.find_one({"_id": ObjectId(id)})
        if not trend:
            return jsonify({"error": "Trend not found"}), 404
            
        trend['_id'] = str(trend['_id'])
        return jsonify(trend), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_instagram_trend: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@bp.route('/ig/<id>', methods=['PUT'])
@token_required
def update_instagram_trend(current_user, id):
    try:
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Invalid ID format"}), 400

        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        trend = mongo.db.instagram_trends.find_one({"_id": ObjectId(id)})
        if not trend:
            return jsonify({"error": "Trend not found"}), 404

        hashtag = request.json.get('hashtag')
        if not hashtag:
            return jsonify({"error": "Hashtag not provided"}), 400

        # Sanitize hashtag
        hashtag = hashtag.strip().lower().replace('#', '')
        
        data = fetch_instagram_data_from_serpapi(f"instagram {hashtag} trending")
        if not data:
            return jsonify({"error": "Failed to fetch data from SerpApi"}), 500

        update_result = mongo.db.instagram_trends.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"hashtag": hashtag, "data": data}}
        )

        if update_result.modified_count == 0:
            return jsonify({"error": "No changes made"}), 400

        updated_trend = mongo.db.instagram_trends.find_one({"_id": ObjectId(id)})
        updated_trend['_id'] = str(updated_trend['_id'])
        
        return jsonify({
            "message": "Instagram trend updated successfully",
            "trend": updated_trend
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in update_instagram_trend: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@bp.route('/ig/<id>', methods=['DELETE'])
@token_required
def delete_instagram_trend(current_user, id):
    try:
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Invalid ID format"}), 400

        result = mongo.db.instagram_trends.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Trend not found"}), 404
            
        return jsonify({"message": "Instagram trend deleted successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error in delete_instagram_trend: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

