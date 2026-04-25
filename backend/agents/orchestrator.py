from typing import List, Dict, Optional
from models.user import UserProfile, KnowledgeGraph, LearningState
import google.generativeai as genai
import os

class LearningOrchestrator:
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    async def decide_next_step(self, user_query: str) -> Dict:
        """
        Advanced decision loop with state management and misconception tracking.
        """
        # 1. Update topic if new concept detected
        detected_topic = self._detect_topic(user_query)
        if detected_topic and detected_topic != self.user_profile.current_topic:
            self.user_profile.current_topic = detected_topic
            self.user_profile.current_state = LearningState.INTRODUCTION

        # 2. Determine state transition
        if self.user_profile.current_state == LearningState.INTRODUCTION:
            return await self._handle_introduction(user_query)
        elif self.user_profile.current_state == LearningState.DEEP_DIVE:
            return await self._handle_deep_dive(user_query)
        elif self.user_profile.current_state == LearningState.PRACTICE:
            return await self._handle_practice(user_query)
        else:
            return await self._handle_general_query(user_query)

    def _detect_topic(self, query: str) -> Optional[str]:
        # Simple detection for now, could use LLM
        topics = ["Neural Networks", "Calculus", "Python", "Data Science"]
        for topic in topics:
            if topic.lower() in query.lower():
                return topic
        return None

    async def _handle_introduction(self, query: str) -> Dict:
        prompt = self._build_prompt("Provide a high-level overview. Keep it simple and use their preferred learning style.")
        response = await self._get_llm_response(prompt)
        
        # Move to Deep Dive after intro
        self.user_profile.current_state = LearningState.DEEP_DIVE
        
        return {
            "type": "explanation",
            "state": "INTRODUCTION",
            "content": response,
            "suggested_actions": ["Explain in Detail", "Give Example"]
        }

    async def _handle_deep_dive(self, query: str) -> Dict:
        prompt = self._build_prompt("Provide a detailed technical breakdown. Address any weak areas or misconceptions.")
        response = await self._get_llm_response(prompt)
        
        # Move to Practice after deep dive
        self.user_profile.current_state = LearningState.PRACTICE
        
        return {
            "type": "explanation",
            "state": "DEEP_DIVE",
            "content": response,
            "suggested_actions": ["Take a Quiz", "Ask Question"]
        }

    async def _handle_practice(self, query: str) -> Dict:
        # Here we would call the AssessmentAgent
        return {
            "type": "quiz_offer",
            "state": "PRACTICE",
            "content": "You've covered the core concepts. Ready to test your knowledge with a personalized quiz?",
            "suggested_actions": ["Start Quiz", "Review Concepts"]
        }

    async def _handle_general_query(self, query: str) -> Dict:
        prompt = self._build_prompt(f"Answer the user's specific query: {query}")
        response = await self._get_llm_response(prompt)
        return {
            "type": "conversation",
            "content": response
        }

    def _build_prompt(self, task_instruction: str) -> str:
        context = f"""
        User Profile:
        - Style: {self.user_profile.learning_style}
        - Pace: {self.user_profile.pace}
        - Current Topic: {self.user_profile.current_topic}
        - Knowledge Level: {self.user_profile.knowledge_graph.concepts.get(self.user_profile.current_topic or '', 0.0)}
        - Known Misconceptions: {self.user_profile.misconceptions.get(self.user_profile.current_topic or '', [])}
        """
        return f"System: You are an AI tutor.\nContext: {context}\nTask: {task_instruction}"

    async def _get_llm_response(self, prompt: str) -> str:
        if self.model:
            response = self.model.generate_content(prompt)
            return response.text
        return "Gemini API not configured. This is a mock response."
