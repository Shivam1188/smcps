from datetime import datetime
from bson import ObjectId


class Publishing:
    def __init__(self, 
                 user_id,
                 content_id,
                 platform,
                 scheduled_time=None,
                 analytics_data=None,
                 qc_feedback=None,
                 status='pending'):
        self.user_id = user_id
        self.content_id = content_id
        self.platform = platform
        self.scheduled_time = scheduled_time
        self.analytics_data = analytics_data if analytics_data else {}
        self.qc_feedback = qc_feedback if qc_feedback else []
        self.status = status
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'content_id': self.content_id,
            'platform': self.platform,
            'scheduled_time': self.scheduled_time,
            'analytics_data': self.analytics_data,
            'qc_feedback': self.qc_feedback,
            'status': self.status,
            'created_at': self.created_at
        }
