"""
Database Client — Firestore integration for user profiles, content store,
and session memory management.
"""
from google.cloud import firestore
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from models.user import UserProfile, LearningState, KnowledgeGraph

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Manages all Firestore operations for the learning assistant."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "gdgpune-455206")
        self.db = None

        try:
            self.db = firestore.Client(project=self.project_id)
            logger.info(f"Firestore initialized for project: {self.project_id}")
        except Exception as e:
            logger.warning(f"Firestore init failed (mock mode): {e}")
            self.db = None

        # In-memory session store (short-term memory)
        self._sessions: Dict[str, Dict] = {}

    # ─── User Profile Operations ─────────────────────────────────

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Fetch user profile from Firestore or return default."""
        if self.db:
            try:
                doc = self.db.collection("users").document(user_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    return UserProfile(**data)
            except Exception as e:
                logger.error(f"Error fetching profile for {user_id}: {e}")

        # Default profile for new users
        return UserProfile(
            user_id=user_id,
            current_state=LearningState.IDLE,
            knowledge_graph=KnowledgeGraph(concepts={}),
        )

    async def save_user_profile(self, profile: UserProfile):
        """Save user profile to Firestore."""
        if self.db:
            try:
                self.db.collection("users").document(profile.user_id).set(
                    profile.dict(), merge=True
                )
                logger.info(f"Profile saved for user: {profile.user_id}")
            except Exception as e:
                logger.error(f"Error saving profile for {profile.user_id}: {e}")
        else:
            logger.info(f"[MOCK DB] Profile saved: {profile.user_id} | state={profile.current_state}")

    # ─── Content Store Operations ────────────────────────────────

    async def get_content(self, topic: str) -> Optional[Dict[str, Any]]:
        """Retrieve educational content for a topic from the content store."""
        if self.db:
            try:
                doc = self.db.collection("content").document(topic.lower().replace(" ", "_")).get()
                if doc.exists:
                    return doc.to_dict()
            except Exception as e:
                logger.error(f"Error fetching content for {topic}: {e}")

        # Default content structure
        return {
            "topic": topic,
            "summary": f"Core concepts of {topic}",
            "prerequisites": [],
            "related_topics": [],
            "difficulty_levels": ["beginner", "intermediate", "advanced"],
        }

    async def save_content(self, topic: str, content: Dict[str, Any]) -> None:
        """Save educational content to Firestore."""
        if self.db:
            try:
                self.db.collection("content").document(
                    topic.lower().replace(" ", "_")
                ).set(content, merge=True)
            except Exception as e:
                logger.error(f"Error saving content for {topic}: {e}")

    # ─── Interaction History ─────────────────────────────────────

    async def save_interaction(self, user_id: str, interaction: Dict[str, Any]) -> None:
        """Save a learning interaction to Firestore for analytics."""
        if self.db:
            try:
                interaction["timestamp"] = datetime.now(timezone.utc).isoformat()
                self.db.collection("interactions").add({
                    "user_id": user_id,
                    **interaction,
                })
            except Exception as e:
                logger.error(f"Error saving interaction: {e}")

    # ─── Session Memory (Short-term) ─────────────────────────────

    def get_session(self, user_id: str) -> Dict[str, Any]:
        """Get the in-memory session context for a user."""
        if user_id not in self._sessions:
            self._sessions[user_id] = {
                "messages": [],
                "current_quiz": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        return self._sessions[user_id]

    def update_session(self, user_id: str, key: str, value: Any) -> None:
        """Update a session value."""
        session = self.get_session(user_id)
        session[key] = value

    def add_to_session_history(self, user_id: str, role: str, content: str) -> None:
        """Add a message to the session's conversation history."""
        session = self.get_session(user_id)
        session["messages"].append({
            "role": role,
            "content": content[:1000],  # Truncate for memory management
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep only last 20 messages (short-term memory window)
        if len(session["messages"]) > 20:
            session["messages"] = session["messages"][-20:]

    def get_session_history(self, user_id: str, last_n: int = 5) -> List[Dict[str, Any]]:
        """Get the last N messages from the session."""
        session = self.get_session(user_id)
        return session["messages"][-last_n:]
