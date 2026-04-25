from typing import List, Dict
import google.generativeai as genai
from models.user import UserProfile, InteractionUpdate

class AssessmentAgent:
    def __init__(self, model):
        self.model = model

    async def generate_quiz(self, concept: str, user_profile: UserProfile) -> Dict:
        """
        Generates a quiz based on the user's proficiency level in the concept.
        """
        score = user_profile.knowledge_graph.concepts.get(concept, 0.0)
        difficulty = "beginner" if score < 0.4 else "intermediate" if score < 0.8 else "advanced"
        
        prompt = f"""
        Generate a 3-question quiz for the concept: {concept}.
        Difficulty: {difficulty}
        User Learning Style: {user_profile.learning_style}
        
        Format the output as a JSON list of questions, each with 'question', 'options', and 'correct_answer'.
        """
        
        if self.model:
            response = self.model.generate_content(prompt)
            # In a real app, we would parse JSON here.
            return {"questions": response.text, "difficulty": difficulty}
        return {"questions": "Mock quiz questions", "difficulty": difficulty}

class AdaptationAgent:
    def __init__(self, db_client):
        self.db = db_client

    def update_knowledge_graph(self, profile: UserProfile, update: InteractionUpdate) -> UserProfile:
        """
        Updates the user's knowledge graph based on their interaction.
        """
        current_score = profile.knowledge_graph.concepts.get(update.concept, 0.5)
        
        if update.is_correct:
            # Increase score, faster for lower scores
            new_score = min(1.0, current_score + (0.1 * (1.0 - current_score)))
        else:
            # Decrease score
            new_score = max(0.0, current_score - 0.2)
            
        profile.knowledge_graph.concepts[update.concept] = new_score
        
        # Track weak areas
        if new_score < 0.3 and update.concept not in profile.weak_areas:
            profile.weak_areas.append(update.concept)
        elif new_score > 0.5 and update.concept in profile.weak_areas:
            profile.weak_areas.remove(update.concept)
            
        return profile
