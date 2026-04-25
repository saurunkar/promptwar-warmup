from typing import List, Dict
from models.user import UserProfile, KnowledgeGraph
import google.generativeai as genai
import os

class LearningOrchestrator:
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        # Initialize Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    async def decide_next_step(self, user_query: str) -> Dict:
        """
        Main decision loop for the orchestrator.
        """
        # 1. Analyze user query and current knowledge state
        # 2. Decide if we need to explain, quiz, or adapt
        
        # Mocking the flow for now
        context = self._build_context(user_query)
        
        if "explain" in user_query.lower() or "?" in user_query:
            return await self._get_explanation(user_query, context)
        else:
            return {
                "type": "conversation",
                "content": "I understand. How can I help you progress in your learning journey today?"
            }

    def _build_context(self, query: str) -> str:
        kg = self.user_profile.knowledge_graph.concepts
        context = f"User Learning Style: {self.user_profile.learning_style}\n"
        context += f"User Pace: {self.user_profile.pace}\n"
        context += "Knowledge State:\n"
        for concept, score in kg.items():
            context += f"- {concept}: {score}\n"
        return context

    async def _get_explanation(self, query: str, context: str) -> Dict:
        prompt = f"""
        System: You are an Intelligent Learning Assistant.
        Context:
        {context}
        
        User Query: {query}
        
        Task: Provide a personalized explanation based on the user's learning style and current knowledge.
        Include 2 follow-up questions to test their understanding.
        """
        
        if self.model:
            response = self.model.generate_content(prompt)
            return {
                "type": "explanation",
                "content": response.text,
                "suggested_actions": ["Take Quiz", "Deep Dive"]
            }
        else:
            return {
                "type": "explanation",
                "content": f"Mock explanation for {query} with context {context}",
                "suggested_actions": ["Take Quiz", "Deep Dive"]
            }
