from datetime import datetime
from bson import ObjectId

class MediaLibrary:
    def __init__(self, image, prompt, media_type,user_id , public_id):
        self.image = image
        self.prompt = prompt
        self.media_type  = media_type
        self.user_id = user_id
        self.public_id = public_id
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            'image': self.image,
            'prompt': self.prompt,
            'media_type': self.media_type,
            'user_id': self.user_id,
            'public_id': self.public_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def update(self, image=None, prompt=None, media_type=None , public_id=None):
        if image:
            self.image = image
        if prompt:
            self.prompt = prompt
        if media_type:
            self.media_type = media_type
        if public_id:
            self.public_id= public_id
        self.updated_at = datetime.utcnow()