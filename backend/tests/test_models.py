"""
Tests for Data Models.
"""
import pytest
from models.user import UserProfile, LearningStyle, Pace, LearningState, KnowledgeGraph, InteractionUpdate

def test_user_profile_defaults():
    profile = UserProfile(user_id="test_user")
    assert profile.learning_style == LearningStyle.MIXED
    assert profile.pace == Pace.MEDIUM
    assert profile.current_state == LearningState.IDLE
    assert profile.current_topic is None
    assert isinstance(profile.knowledge_graph, KnowledgeGraph)
    assert profile.history == []
    assert profile.weak_areas == []
    assert profile.misconceptions == {}

def test_knowledge_graph_defaults():
    kg = KnowledgeGraph()
    assert kg.concepts == {}

def test_interaction_update():
    update = InteractionUpdate(
        user_id="test_user",
        concept="Python",
        is_correct=True,
        response_time_ms=5000
    )
    assert update.user_id == "test_user"
    assert update.concept == "Python"
    assert update.is_correct is True
    assert update.response_time_ms == 5000
