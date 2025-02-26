from datetime import datetime
from bson import ObjectId

class Trend:
    def __init__(self, title, platform, engagement_metrics, sentiment_score=None):
        self.title = title
        self.platform = platform
        self.engagement_metrics = engagement_metrics
        self.sentiment_score = sentiment_score
        self.created_at = datetime.utcnow()
        self.status = 'active'
        self.roi_potential = None

    def to_dict(self):
        return {
            'title': self.title,
            'platform': self.platform,
            'engagement_metrics': self.engagement_metrics,
            'sentiment_score': self.sentiment_score,
            'created_at': self.created_at,
            'status': self.status,
            'roi_potential': self.roi_potential
        }
    

class InstagramTrend:
    def __init__(self, hashtag, data, sentiment_score=None):
        self.hashtag = hashtag  # The hashtag for the trend (e.g., #trending)
        self.data = data  # The data fetched from Instagram API
        self.sentiment_score = sentiment_score  # Sentiment score for the trend (optional)
        self.created_at = datetime.utcnow()  # Timestamp when the trend is created
        self.status = 'active'  # Default status is 'active'
        self.roi_potential = None  # You can calculate or define ROI potential later

    def to_dict(self):
        """Convert the InstagramTrend object to a dictionary format for storing in the database."""
        return {
            '_id': str(ObjectId()),  # Generate a new ObjectId for the document
            'hashtag': self.hashtag,
            'data': self.data,
            'sentiment_score': self.sentiment_score,
            'created_at': self.created_at,
            'status': self.status,
            'roi_potential': self.roi_potential
        }

    @staticmethod
    def from_dict(data):
        """Convert a dictionary to an InstagramTrend object."""
        return InstagramTrend(
            hashtag=data.get('hashtag'),
            data=data.get('data'),
            sentiment_score=data.get('sentiment_score')
        )