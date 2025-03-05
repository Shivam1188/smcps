from datetime import datetime
from bson import ObjectId


class AiResponse:
    def __init__(self, image_url: str, prompt: str, user_id: str):
        self.id = ObjectId()
        self.image_url = image_url
        self.prompt = prompt
        self.user_id = user_id  # Added user_id field
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_prompt(self, new_prompt: str):
        self.prompt = new_prompt
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": str(self.id),
            "image_url": self.image_url,
            "prompt": self.prompt,
            "user_id": self.user_id,  # Include user_id in the dictionary
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
