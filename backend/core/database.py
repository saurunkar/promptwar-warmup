from google.cloud import firestore
import os
from models.user import UserProfile, LearningState

class DatabaseClient:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "gdgpune-455206")
        if self.project_id:
            try:
                self.db = firestore.Client(project=self.project_id)
            except Exception as e:
                print(f"Error initializing Firestore: {e}")
                self.db = None
        else:
            self.db = None

    async def get_user_profile(self, user_id: str) -> UserProfile:
        if self.db:
            try:
                doc = self.db.collection("users").document(user_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    # Ensure all new fields are handled
                    return UserProfile(**data)
            except Exception as e:
                print(f"Error fetching profile: {e}")
        
        # Return default profile for new users
        return UserProfile(
            user_id=user_id, 
            current_state=LearningState.IDLE,
            knowledge_graph={"concepts": {"Neural Networks": 0.5}}
        )

    async def save_user_profile(self, profile: UserProfile):
        if self.db:
            try:
                self.db.collection("users").document(profile.user_id).set(profile.dict())
            except Exception as e:
                print(f"Error saving profile: {e}")
        else:
            print(f"Mock Save: {profile.user_id} state is now {profile.current_state}")
