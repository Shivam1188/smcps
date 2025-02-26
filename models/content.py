from datetime import datetime
from bson import ObjectId

class Content:
    def __init__(self, 
                 title, 
                 content_theme, 
                 target_audience, 
                 video_format, 
                 tone, 
                 platform, 
                 keywords, 
                 hashtags, 
                 user_id, 
                 reference_files=None):
        self.title = title
        self.content_theme = content_theme
        self.target_audience = target_audience
        self.video_format = video_format
        self.tone = tone
        self.platform = platform
        self.keywords = keywords
        self.hashtags = hashtags
        self.user_id = user_id
        self.reference_files = reference_files if reference_files else []
        self.created_at = datetime.utcnow()
        self.status = 'draft'
        self.qc_status = 'pending'
        self.qc_feedback = []
        self.storyboard = None

    def to_dict(self):
        return {
            'title': self.title,
            'content_theme': self.content_theme,
            'target_audience': self.target_audience,
            'video_format': self.video_format,
            'tone': self.tone,
            'platform': self.platform,
            'keywords': self.keywords,
            'hashtags': self.hashtags,
            'user_id': self.user_id,
            'reference_files': self.reference_files,
            'created_at': self.created_at,
            'status': self.status,
            'qc_status': self.qc_status,
            'qc_feedback': self.qc_feedback,
            'storyboard': self.storyboard
        }
