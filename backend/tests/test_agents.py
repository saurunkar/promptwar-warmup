"""
Tests for Sub-Agents (AdaptationAgent, FeedbackAgent)
"""
import pytest
from agents.sub_agents import AdaptationAgent, FeedbackAgent
from models.user import UserProfile, InteractionUpdate, LearningState

@pytest.fixture
def base_profile():
    return UserProfile(user_id="test_user")

class TestAdaptationAgent:
    
    def test_update_knowledge_graph_correct_answer(self, base_profile):
        agent = AdaptationAgent()
        base_profile.knowledge_graph.concepts["Python"] = 0.5
        update = InteractionUpdate(
            user_id="test_user",
            concept="Python",
            is_correct=True,
            response_time_ms=2000 # Fast response
        )
        updated_profile = agent.update_knowledge_graph(base_profile, update)
        
        # Score should increase
        assert updated_profile.knowledge_graph.concepts["Python"] > 0.5
        # Fast response should result in state progressing towards Mastery if it gets high enough
        
    def test_update_knowledge_graph_incorrect_answer(self, base_profile):
        agent = AdaptationAgent()
        base_profile.knowledge_graph.concepts["Python"] = 0.5
        update = InteractionUpdate(
            user_id="test_user",
            concept="Python",
            is_correct=False,
            response_time_ms=5000
        )
        updated_profile = agent.update_knowledge_graph(base_profile, update)
        
        # Score should decrease
        assert updated_profile.knowledge_graph.concepts["Python"] < 0.5
        
    def test_update_knowledge_graph_adds_weak_area(self, base_profile):
        agent = AdaptationAgent()
        base_profile.knowledge_graph.concepts["Calculus"] = 0.3
        update = InteractionUpdate(
            user_id="test_user",
            concept="Calculus",
            is_correct=False,
            response_time_ms=5000
        )
        updated_profile = agent.update_knowledge_graph(base_profile, update)
        
        assert "Calculus" in updated_profile.weak_areas
        
    def test_update_knowledge_graph_removes_weak_area(self, base_profile):
        agent = AdaptationAgent()
        base_profile.knowledge_graph.concepts["Calculus"] = 0.45
        base_profile.weak_areas = ["Calculus"]
        update = InteractionUpdate(
            user_id="test_user",
            concept="Calculus",
            is_correct=True,
            response_time_ms=2000
        )
        updated_profile = agent.update_knowledge_graph(base_profile, update)
        
        assert "Calculus" not in updated_profile.weak_areas

    def test_update_misconceptions(self, base_profile):
        agent = AdaptationAgent()
        updated = agent.update_misconceptions(base_profile, "Python", ["Lists are arrays"])
        assert "Lists are arrays" in updated.misconceptions["Python"]
        
        # Test deduplication
        updated = agent.update_misconceptions(updated, "Python", ["Lists are arrays"])
        assert len(updated.misconceptions["Python"]) == 1

@pytest.mark.asyncio
class TestFeedbackAgent:
    
    async def test_evaluate_answer_mock_fallback(self, base_profile):
        # When LLM is not configured, it should use the deterministic fallback
        agent = FeedbackAgent()
        result = await agent.evaluate_answer(
            question="What is 2+2?",
            user_answer="4",
            correct_answer="4",
            concept="Math",
            user_profile=base_profile
        )
        
        assert result["is_correct"] is True
        assert result["score"] == 1.0
        
    async def test_evaluate_answer_mock_fallback_incorrect(self, base_profile):
        agent = FeedbackAgent()
        result = await agent.evaluate_answer(
            question="What is 2+2?",
            user_answer="5",
            correct_answer="4",
            concept="Math",
            user_profile=base_profile
        )
        
        assert result["is_correct"] is False
        assert result["score"] == 0.0
        assert len(result["misconceptions"]) > 0
