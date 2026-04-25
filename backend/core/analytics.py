"""
Analytics Module — Pub/Sub event publishing and Cloud Logging
for the Agentic Learning Assistant.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Try to import Pub/Sub client
try:
    from google.cloud import pubsub_v1
    PUBSUB_AVAILABLE = True
except ImportError:
    PUBSUB_AVAILABLE = False

# Try to import Cloud Logging
try:
    import google.cloud.logging as cloud_logging
    CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    CLOUD_LOGGING_AVAILABLE = False


class AnalyticsClient:
    """Publishes learning events to Pub/Sub and logs to Cloud Logging."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "gdgpune-455206")
        self.topic_name = os.getenv("PUBSUB_TOPIC", "learning-events")
        self.publisher = None
        self.topic_path = None

        # Initialize Cloud Logging
        if CLOUD_LOGGING_AVAILABLE and os.getenv("ENABLE_CLOUD_LOGGING", "false").lower() == "true":
            try:
                client = cloud_logging.Client(project=self.project_id)
                client.setup_logging()
                logger.info("Cloud Logging initialized.")
            except Exception as e:
                logger.warning(f"Cloud Logging init failed: {e}")

        # Initialize Pub/Sub publisher
        if PUBSUB_AVAILABLE:
            try:
                self.publisher = pubsub_v1.PublisherClient()
                self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
                logger.info(f"Pub/Sub publisher initialized for topic: {self.topic_path}")
            except Exception as e:
                logger.warning(f"Pub/Sub init failed (will log locally): {e}")
                self.publisher = None

    async def track_event(self, event_type: str, user_id: str, data: Optional[Dict] = None):
        """
        Track a learning event. Published to Pub/Sub if available,
        otherwise logged locally.

        Event types: query, quiz_started, quiz_answered, state_change,
                     profile_updated, feedback_given
        """
        event = {
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }

        # Publish to Pub/Sub
        if self.publisher and self.topic_path:
            try:
                message = json.dumps(event).encode("utf-8")
                future = self.publisher.publish(self.topic_path, message)
                future.result(timeout=5)
                logger.info(f"Event published: {event_type} for user {user_id}")
            except Exception as e:
                logger.warning(f"Pub/Sub publish failed: {e}")
                # Fallback to local logging
                logger.info(f"[LOCAL EVENT] {json.dumps(event)}")
        else:
            # Local fallback
            logger.info(f"[LOCAL EVENT] {event_type} | user={user_id} | data={data}")

    async def track_query(self, user_id: str, query: str, response_type: str):
        await self.track_event("query", user_id, {
            "query": query[:500],  # Truncate for storage
            "response_type": response_type,
        })

    async def track_quiz(self, user_id: str, concept: str, score: float):
        await self.track_event("quiz_answered", user_id, {
            "concept": concept,
            "score": score,
        })

    async def track_state_change(self, user_id: str, old_state: str, new_state: str):
        await self.track_event("state_change", user_id, {
            "from": old_state,
            "to": new_state,
        })


# Global singleton
analytics = AnalyticsClient()
