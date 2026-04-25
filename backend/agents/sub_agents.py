"""
Sub-Agents — Assessment, Feedback, Content Generation, and Adaptation agents
for the Agentic Learning Assistant.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from models.user import UserProfile, InteractionUpdate, LearningState
from core.llm import llm_client

logger = logging.getLogger(__name__)


class AssessmentAgent:
    """Generates personalized quizzes based on user proficiency and learning style."""

    async def generate_quiz(self, concept: str, user_profile: UserProfile) -> Dict[str, Any]:
        score = user_profile.knowledge_graph.concepts.get(concept, 0.0)
        difficulty = "beginner" if score < 0.3 else "intermediate" if score < 0.7 else "advanced"

        prompt = f"""Generate a quiz for the learning concept: "{concept}"
Difficulty level: {difficulty}
User's learning style: {user_profile.learning_style.value}
User's current mastery: {score:.1f}/1.0

Create exactly 3 multiple-choice questions. Each question must have:
- "question": the question text
- "options": exactly 4 answer options as a list
- "correct_answer": the correct option text (must match one of the options exactly)
- "explanation": a brief explanation of why the answer is correct

Return a JSON array of 3 question objects."""

        result = await llm_client.generate_json(prompt)

        if result and isinstance(result, list):
            return {
                "concept": concept,
                "difficulty": difficulty,
                "questions": result,
                "total_questions": len(result),
            }

        # Fallback quiz
        return {
            "concept": concept,
            "difficulty": difficulty,
            "questions": [
                {
                    "question": f"What is the fundamental purpose of {concept}?",
                    "options": [
                        "Data storage optimization",
                        "Pattern recognition and learning from data",
                        "Network security management",
                        "Operating system design",
                    ],
                    "correct_answer": "Pattern recognition and learning from data",
                    "explanation": f"{concept} is fundamentally about recognizing patterns and learning from data.",
                },
                {
                    "question": f"Which of these is a key component of {concept}?",
                    "options": [
                        "Layers of processing units",
                        "Physical circuit boards",
                        "Mechanical actuators",
                        "Analog signals only",
                    ],
                    "correct_answer": "Layers of processing units",
                    "explanation": "Processing units organized in layers are a core component.",
                },
                {
                    "question": f"What does 'training' mean in the context of {concept}?",
                    "options": [
                        "Physical exercise for computers",
                        "Adjusting parameters to minimize error",
                        "Installing new software",
                        "Increasing CPU speed",
                    ],
                    "correct_answer": "Adjusting parameters to minimize error",
                    "explanation": "Training refers to the iterative process of adjusting model parameters.",
                },
            ],
            "total_questions": 3,
        }


class FeedbackAgent:
    """Evaluates user answers using LLM, detects misconceptions, and provides guidance."""

    async def evaluate_answer(
        self, question: str, user_answer: str, correct_answer: str,
        concept: str, user_profile: UserProfile
    ) -> Dict[str, Any]:
        prompt = f"""You are evaluating a student's answer to a quiz question.

Concept: {concept}
Question: {question}
Student's Answer: {user_answer}
Correct Answer: {correct_answer}
Student's learning style: {user_profile.learning_style.value}

Evaluate the answer and respond with JSON containing:
- "is_correct": boolean
- "score": float between 0.0 and 1.0 (partial credit allowed)
- "explanation": a helpful, encouraging explanation
- "misconceptions": list of any misconceptions detected (empty list if none)
- "suggestions": list of 1-2 suggestions for improvement"""

        result = await llm_client.generate_json(prompt)

        if result and isinstance(result, dict):
            return result

        # Deterministic fallback
        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        return {
            "is_correct": is_correct,
            "score": 1.0 if is_correct else 0.0,
            "explanation": "Correct! Well done." if is_correct else f"The correct answer is: {correct_answer}",
            "misconceptions": [] if is_correct else [f"Confusion about {concept} fundamentals"],
            "suggestions": ["Keep practicing!" if is_correct else "Review the core concepts again"],
        }


class ContentGeneratorAgent:
    """Generates multi-format educational content adapted to learning style."""

    async def generate_content(
        self, topic: str, user_profile: UserProfile, content_type: str = "explanation"
    ) -> Dict[str, Any]:
        style = user_profile.learning_style.value
        pace = user_profile.pace.value
        score = user_profile.knowledge_graph.concepts.get(topic, 0.0)

        style_instructions = {
            "visual": "Use diagrams described in text, bullet points, structured layouts, and visual metaphors.",
            "textual": "Use detailed prose, definitions, and thorough written explanations.",
            "mixed": "Combine structured bullet points with detailed explanations and visual metaphors.",
        }

        pace_instructions = {
            "slow": "Be very thorough. Explain every term. Use simple language.",
            "medium": "Balance detail with conciseness. Assume basic familiarity.",
            "fast": "Be concise and technical. Skip basics. Focus on advanced insights.",
        }

        prompt = f"""Create educational content about "{topic}".
Content type: {content_type}
User knowledge level: {score:.1f}/1.0

Style: {style_instructions.get(style, style_instructions['mixed'])}
Pace: {pace_instructions.get(pace, pace_instructions['medium'])}

Structure your response with:
1. A clear title
2. Key concepts (3-5 bullet points)
3. Detailed explanation
4. A practical example
5. A summary

Make it engaging and memorable."""

        content = await llm_client.generate(prompt)

        return {
            "topic": topic,
            "content_type": content_type,
            "learning_style": style,
            "body": content,
        }


class AdaptationAgent:
    """Updates user knowledge models based on learning interactions."""

    def __init__(self, db_client: Optional[Any] = None) -> None:
        self.db = db_client

    def update_knowledge_graph(
        self, profile: UserProfile, update: InteractionUpdate
    ) -> UserProfile:
        """
        Reinforcement learning-style knowledge graph update.
        Scores are adjusted based on correctness and response time.
        """
        current_score = profile.knowledge_graph.concepts.get(update.concept, 0.5)

        # Factor in response time (faster correct answers = higher confidence)
        time_factor = 1.0
        if update.response_time_ms < 5000:
            time_factor = 1.2  # Fast response bonus
        elif update.response_time_ms > 30000:
            time_factor = 0.8  # Slow response penalty

        if update.is_correct:
            # Increase score, with diminishing returns at higher levels
            delta = 0.1 * (1.0 - current_score) * time_factor
            new_score = min(1.0, current_score + delta)
        else:
            # Decrease score
            new_score = max(0.0, current_score - 0.15)

        profile.knowledge_graph.concepts[update.concept] = round(new_score, 3)

        # Update weak areas
        if new_score < 0.3 and update.concept not in profile.weak_areas:
            profile.weak_areas.append(update.concept)
            logger.info(f"Added weak area: {update.concept} for user {profile.user_id}")
        elif new_score >= 0.5 and update.concept in profile.weak_areas:
            profile.weak_areas.remove(update.concept)
            logger.info(f"Removed weak area: {update.concept} for user {profile.user_id}")

        # Update learning state based on mastery
        if new_score >= 0.8:
            profile.current_state = LearningState.MASTERY_REVIEW
        elif new_score < 0.3:
            profile.current_state = LearningState.INTRODUCTION

        return profile

    def update_misconceptions(
        self, profile: UserProfile, concept: str, misconceptions: List[str]
    ) -> UserProfile:
        """Track misconceptions identified by the FeedbackAgent."""
        if concept not in profile.misconceptions:
            profile.misconceptions[concept] = []

        for m in misconceptions:
            if m not in profile.misconceptions[concept]:
                profile.misconceptions[concept].append(m)
                logger.info(f"Tracked misconception for {profile.user_id}: {concept} -> {m}")

        # Keep only last 10 misconceptions per concept
        profile.misconceptions[concept] = profile.misconceptions[concept][-10:]
        return profile
