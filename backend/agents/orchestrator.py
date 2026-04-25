"""
Learning Orchestrator — Primary Agent that coordinates all sub-agents,
manages learning states, provides RAG context, and tracks session memory.
"""
import logging
from typing import Dict, Optional, List
from models.user import UserProfile, LearningState
from core.llm import llm_client
from core.security import sanitize_input, filter_output
from core.analytics import analytics

logger = logging.getLogger(__name__)

# System instruction for the AI tutor persona
TUTOR_SYSTEM_PROMPT = """You are Aegis, an expert AI tutor and learning assistant. 
Your role is to:
- Explain complex concepts in simple, engaging ways
- Adapt your language to the user's learning style and pace
- Identify and correct misconceptions
- Encourage curiosity and deeper understanding
- Use analogies, examples, and visual descriptions when helpful

Always be encouraging, patient, and thorough."""


class LearningOrchestrator:
    """
    Primary Agent — decides what to teach, when to test,
    and when to simplify based on user state and knowledge graph.
    """

    def __init__(self, user_profile: UserProfile, db_client=None):
        self.profile = user_profile
        self.db = db_client

    async def decide_next_step(self, user_query: str) -> Dict:
        """
        Main orchestration loop:
        1. Sanitize input
        2. Detect topic (LLM-based)
        3. Build personalized context
        4. Route to appropriate handler based on learning state
        5. Filter output
        6. Track analytics
        """
        # Step 1: Input sanitization
        clean_query, is_safe = sanitize_input(user_query)
        if not is_safe:
            return {
                "type": "error",
                "content": "I couldn't process that input. Could you rephrase your question?",
                "state": self.profile.current_state.value,
            }

        # Step 2: Detect topic using LLM
        detected_topic = await self._detect_topic_llm(clean_query)
        old_state = self.profile.current_state.value

        if detected_topic and detected_topic != self.profile.current_topic:
            self.profile.current_topic = detected_topic
            self.profile.current_state = LearningState.INTRODUCTION
            # Track state change
            await analytics.track_state_change(
                self.profile.user_id, old_state, "introduction"
            )

        # Step 3: Route based on state
        if self.profile.current_state == LearningState.INTRODUCTION:
            result = await self._handle_introduction(clean_query)
        elif self.profile.current_state == LearningState.DEEP_DIVE:
            result = await self._handle_deep_dive(clean_query)
        elif self.profile.current_state == LearningState.PRACTICE:
            result = await self._handle_practice(clean_query)
        elif self.profile.current_state == LearningState.MASTERY_REVIEW:
            result = await self._handle_mastery_review(clean_query)
        else:
            result = await self._handle_general_query(clean_query)

        # Step 4: Filter output
        if "content" in result:
            result["content"] = filter_output(result["content"])

        # Step 5: Store session memory
        if self.db:
            self.db.add_to_session_history(self.profile.user_id, "user", clean_query)
            self.db.add_to_session_history(self.profile.user_id, "assistant", result.get("content", ""))

        # Step 6: Track analytics
        await analytics.track_query(
            self.profile.user_id, clean_query, result.get("type", "unknown")
        )

        # Add profile state to response
        result["state"] = self.profile.current_state.value
        result["topic"] = self.profile.current_topic
        result["knowledge"] = self.profile.knowledge_graph.concepts

        return result

    async def _detect_topic_llm(self, query: str) -> Optional[str]:
        """Use LLM to intelligently detect the learning topic from the query."""
        prompt = f"""Analyze this user query and extract the main learning topic.
Return ONLY the topic name (2-4 words max). If no clear topic, return "general".

Query: "{query}"

Topic:"""
        response = await llm_client.generate(prompt)
        topic = response.strip().strip('"').strip("'")

        if topic.lower() == "general" or len(topic) > 50:
            return self.profile.current_topic  # Keep existing topic
        return topic

    async def _handle_introduction(self, query: str) -> Dict:
        """Introduction state: High-level overview adapted to learning style."""
        context = self._build_context()
        session_history = self._get_session_context()

        prompt = f"""{context}

{session_history}

The user is just starting to learn about "{self.profile.current_topic}".
Provide a welcoming, high-level overview of this topic.
Adapt your explanation to their {self.profile.learning_style.value} learning style.
Keep it at a {self.profile.pace.value} pace.
Include 2-3 key concepts they'll learn.
End with an encouraging question to check basic understanding.

User's question: {query}"""

        response = await llm_client.generate(prompt, TUTOR_SYSTEM_PROMPT)

        # Advance state
        self.profile.current_state = LearningState.DEEP_DIVE

        return {
            "type": "explanation",
            "content": response,
            "suggested_actions": ["Explain in Detail", "Give Example", "Simplify"],
        }

    async def _handle_deep_dive(self, query: str) -> Dict:
        """Deep dive state: Detailed technical breakdown with misconception awareness."""
        context = self._build_context()
        session_history = self._get_session_context()

        misconceptions = self.profile.misconceptions.get(self.profile.current_topic or "", [])
        misconception_text = ""
        if misconceptions:
            misconception_text = f"\nKNOWN MISCONCEPTIONS to address: {', '.join(misconceptions)}"

        prompt = f"""{context}
{misconception_text}

{session_history}

The user is now in a DEEP DIVE on "{self.profile.current_topic}".
Provide a detailed, technical explanation building on the introduction.
Include:
- Step-by-step breakdown of core mechanisms
- A practical real-world example or analogy
- Common pitfalls or misconceptions to watch out for
Adapt complexity to their knowledge level: {self.profile.knowledge_graph.concepts.get(self.profile.current_topic or '', 0.0):.1f}/1.0

User's question: {query}"""

        response = await llm_client.generate(prompt, TUTOR_SYSTEM_PROMPT)

        # Advance state
        self.profile.current_state = LearningState.PRACTICE

        return {
            "type": "explanation",
            "content": response,
            "suggested_actions": ["Take a Quiz", "Ask Follow-up", "Show Code Example"],
        }

    async def _handle_practice(self, query: str) -> Dict:
        """Practice state: Offer assessment to test understanding."""
        return {
            "type": "quiz_offer",
            "content": f"Great progress on {self.profile.current_topic}! You've covered the introduction and deep dive. Let's test your understanding with a personalized quiz. Ready?",
            "suggested_actions": ["Start Quiz", "Review Concepts", "Move to Next Topic"],
        }

    async def _handle_mastery_review(self, query: str) -> Dict:
        """Mastery review: Spaced repetition and advanced questions."""
        context = self._build_context()

        prompt = f"""{context}

The user has reached MASTERY REVIEW for "{self.profile.current_topic}".
Their current mastery score is {self.profile.knowledge_graph.concepts.get(self.profile.current_topic or '', 0.0):.1f}/1.0.
Ask them an advanced, thought-provoking question about this topic to reinforce retention.
If their score is below 0.7, include a brief recap of weak points.

User's message: {query}"""

        response = await llm_client.generate(prompt, TUTOR_SYSTEM_PROMPT)

        return {
            "type": "mastery_review",
            "content": response,
            "suggested_actions": ["Answer", "Skip to New Topic", "See My Progress"],
        }

    async def _handle_general_query(self, query: str) -> Dict:
        """Handle general queries outside the state machine."""
        context = self._build_context()
        session_history = self._get_session_context()

        prompt = f"""{context}

{session_history}

The user has a general question. Answer it helpfully while relating it to their 
learning journey when possible.

User's question: {query}"""

        response = await llm_client.generate(prompt, TUTOR_SYSTEM_PROMPT)

        return {
            "type": "conversation",
            "content": response,
            "suggested_actions": ["Start a Topic", "Take a Quiz", "View Progress"],
        }

    def _build_context(self) -> str:
        """Build rich personalization context from user profile."""
        kg = self.profile.knowledge_graph.concepts
        knowledge_summary = "\n".join(
            [f"  - {concept}: {score:.1f}/1.0" for concept, score in kg.items()]
        ) if kg else "  No concepts tracked yet."

        weak = ", ".join(self.profile.weak_areas) if self.profile.weak_areas else "None identified"

        return f"""USER PROFILE:
- Learning Style: {self.profile.learning_style.value}
- Pace: {self.profile.pace.value}
- Current Topic: {self.profile.current_topic or 'None'}
- Current State: {self.profile.current_state.value}
- Weak Areas: {weak}

KNOWLEDGE GRAPH:
{knowledge_summary}"""

    def _get_session_context(self) -> str:
        """Get recent conversation history for context continuity."""
        if not self.db:
            return ""
        history = self.db.get_session_history(self.profile.user_id, last_n=3)
        if not history:
            return ""
        lines = ["RECENT CONVERSATION:"]
        for msg in history:
            lines.append(f"  {msg['role'].upper()}: {msg['content'][:200]}")
        return "\n".join(lines)
