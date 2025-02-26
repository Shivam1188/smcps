import os
import json
import requests
from datetime import datetime
import googleapiclient.discovery
from typing import List, Dict

class SocialMediaTrends:
    def __init__(self, youtube_api_key: str, instagram_access_token: str):
        self.youtube_api_key = youtube_api_key
        self.instagram_access_token = instagram_access_token

    def init_youtube(self):
        """Initialize YouTube API client"""
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        return googleapiclient.discovery.build(
            "youtube", "v3", 
            developerKey=self.youtube_api_key
        )

    def get_youtube_trending_videos(self, region_code: str = "IN", max_results: int = 10) -> List[Dict]:
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

    def get_instagram_trending_posts(self, hashtag: str = "trending", max_results: int = 10) -> List[Dict]:
        """Fetch Instagram posts using the Instagram Graph API"""
        url = f"https://graph.facebook.com/v18.0/ig_hashtag_search?user_id=YOUR_USER_ID&q={hashtag}&access_token={self.instagram_access_token}"
        try:
            response = requests.get(url)
            data = response.json()

            if "error" in data:
                print(f"Instagram API Error: {data['error']['message']}")
                return []

            hashtag_id = data["data"][0]["id"]
            hashtag_posts_url = f"https://graph.facebook.com/v18.0/{hashtag_id}/top_media?user_id=YOUR_USER_ID&fields=id,caption,media_url,permalink,like_count,comments_count&limit={max_results}&access_token={self.instagram_access_token}"

            response = requests.get(hashtag_posts_url)
            posts_data = response.json()

            if "error" in posts_data:
                print(f"Instagram API Error: {posts_data['error']['message']}")
                return []

            posts = []
            for post in posts_data["data"]:
                posts.append({
                    "caption": post.get("caption", ""),
                    "url": post["permalink"],
                    "media_url": post["media_url"],
                    "likes": post.get("like_count", 0),
                    "comments": post.get("comments_count", 0),
                })

            return posts

        except Exception as e:
            print(f"Error fetching Instagram posts: {str(e)}")
            return []

    def save_to_file(self, data: Dict, filename: str):
        """Save the trending data to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {str(e)}")

def main():
    # Configuration
    YOUTUBE_API_KEY = "AIzaSyCzWPGsCrmfXkVk-WxUCAr7WL0iKG7qHxo"
    INSTAGRAM_ACCESS_TOKEN = "YOUR_INSTAGRAM_ACCESS_TOKEN"

    # Initialize the trends tracker
    tracker = SocialMediaTrends(youtube_api_key=YOUTUBE_API_KEY, instagram_access_token=INSTAGRAM_ACCESS_TOKEN)

    # Fetch YouTube trending videos
    print("\nFetching YouTube Trending Videos...")
    youtube_trending = tracker.get_youtube_trending_videos(max_results=5)
    
    if youtube_trending:
        print("\nYouTube Trending Videos:")
        for video in youtube_trending:
            print(f"\nTitle: {video['title']}")
            print(f"Channel: {video['channel']}")
            print(f"URL: {video['video_url']}")
            print(f"Views: {video['views']:,}")
            print(f"Likes: {video['likes']:,}")
            print(f"Comments: {video['comments']:,}")
            print("-" * 50)

    # Fetch Instagram trending posts
    print("\nFetching Instagram Trending Posts...")
    instagram_trending = tracker.get_instagram_trending_posts(max_results=5)
    
    if instagram_trending:
        print("\nInstagram Posts:")
        for post in instagram_trending:
            print(f"\nCaption: {post['caption'][:100]}...")
            print(f"URL: {post['url']}")
            print(f"Media URL: {post['media_url']}")
            print(f"Likes: {post['likes']:,}")
            print(f"Comments: {post['comments']:,}")
            print("-" * 50)

    # Save all data to a JSON file
    all_data = {
        "youtube_trending": youtube_trending,
        "instagram_trending": instagram_trending,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    tracker.save_to_file(all_data, "trending_data.json")

if __name__ == "__main__":
    main()
