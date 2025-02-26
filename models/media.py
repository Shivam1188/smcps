from datetime import datetime
from bson import ObjectId


class Media:
    def __init__(self, 
                 content_id, 
                 visual_style, 
                 target_platform, 
                 video_length, 
                 custom_assets=None, 
                 animation_settings=None, 
                 audio_settings=None, 
                 qc_feedback=None):
        self.content_id = content_id
        self.visual_style = visual_style
        self.target_platform = target_platform
        self.video_length = video_length
        self.custom_assets = custom_assets if custom_assets else []
        self.animation_settings = animation_settings if animation_settings else {}
        self.audio_settings = audio_settings if audio_settings else {}
        self.qc_feedback = qc_feedback if qc_feedback else []
        self.status = 'draft'
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            'content_id': self.content_id,
            'visual_style': self.visual_style,
            'target_platform': self.target_platform,
            'video_length': self.video_length,
            'custom_assets': self.custom_assets,
            'animation_settings': self.animation_settings,
            'audio_settings': self.audio_settings,
            'qc_feedback': self.qc_feedback,
            'status': self.status,
            'created_at': self.created_at
        }
