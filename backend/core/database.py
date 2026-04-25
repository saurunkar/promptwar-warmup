from google.cloud import firestore
import os
from models.user import UserProfile

class DatabaseClient:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        if self.project_id:
            self.db = firestore.Client(project=self.project_id)
        else:
            self.db = None
            print("Running with Mock Database")

    async def get_user_profile(self, user_id: str) -> UserProfile:
        if self.db:
            doc = self.db.collection("users").document(user_id).get()
            if doc.exists:
                return UserProfile(**doc.to_dict())
        
        # Return default profile if not found or no DB
        return UserProfile(user_id=user_id, knowledge_graph={"concepts": {"Neural Networks": 0.5, "Calculus": 0.2}})

    async def save_user_profile(self, profile: UserProfile):
        if self.db:
            self.db.collection("users").document(profile.user_id).set(profile.dict())
        else:
            print(f"Mock Save: Profile for {profile.user_id} updated.")
