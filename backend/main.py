"""
Agentic Intelligent Learning Assistant — API Server
FastAPI backend with full agent orchestration, quiz flow, profile management,
analytics, security middleware, and observability.
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from agents.orchestrator import LearningOrchestrator
from agents.sub_agents import AssessmentAgent, FeedbackAgent, AdaptationAgent, ContentGeneratorAgent
from core.database import DatabaseClient
from core.security import sanitize_input, validate_user_id
from core.analytics import analytics
from models.user import InteractionUpdate, LearningStyle, Pace

# ─── Logging Setup ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("aegis")

# ─── Lifespan ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Aegis Learning Assistant starting up...")
    yield
    logger.info("Aegis Learning Assistant shutting down...")

# ─── App Init ────────────────────────────────────────────────────
app = FastAPI(
    title="Aegis — Agentic Intelligent Learning Assistant",
    description="Personalized, LLM-powered learning with adaptive agents",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Singletons ──────────────────────────────────────────────────
db = DatabaseClient()
assessment_agent = AssessmentAgent()
feedback_agent = FeedbackAgent()
adaptation_agent = AdaptationAgent(db)
content_agent = ContentGeneratorAgent()

# ─── Request Models ──────────────────────────────────────────────
class UserQuery(BaseModel):
    user_id: str
    query: str

class QuizRequest(BaseModel):
    user_id: str
    concept: Optional[str] = None  # Auto-detect from profile if not provided

class QuizAnswer(BaseModel):
    user_id: str
    concept: str
    question: str
    user_answer: str
    correct_answer: str

class ProfileUpdate(BaseModel):
    user_id: str
    learning_style: Optional[LearningStyle] = None
    pace: Optional[Pace] = None

# ─── Middleware: Request Logging ─────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {request.method} {request.url.path} [{response.status_code}]")
    return response

# ─── Health Check ────────────────────────────────────────────────
@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": "Aegis Learning Assistant",
        "version": "3.0.0",
        "status": "healthy",
        "components": {
            "firestore": "connected" if db.db else "mock",
            "llm": "configured" if os.getenv("GOOGLE_API_KEY") else "mock",
        },
    }

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}

# ─── Core: Ask Endpoint ─────────────────────────────────────────
@app.post("/ask")
async def ask_question(request: UserQuery) -> Dict[str, Any]:
    """Main learning interaction — orchestrates all agents."""
    if not validate_user_id(request.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    profile = await db.get_user_profile(request.user_id)
    orchestrator = LearningOrchestrator(profile, db)
    response = await orchestrator.decide_next_step(request.query)

    # Save updated profile (state may have changed)
    await db.save_user_profile(profile)

    # Save interaction
    await db.save_interaction(request.user_id, {
        "type": "ask",
        "query": request.query[:500],
        "response_type": response.get("type"),
    })

    return response

# ─── Quiz: Generate ──────────────────────────────────────────────
@app.post("/quiz")
async def generate_quiz(request: QuizRequest) -> Dict[str, Any]:
    """Generate a personalized quiz for the user."""
    if not validate_user_id(request.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    profile = await db.get_user_profile(request.user_id)
    concept = request.concept or profile.current_topic

    if not concept:
        raise HTTPException(
            status_code=400,
            detail="No concept specified and no active topic. Start learning first!",
        )

    quiz = await assessment_agent.generate_quiz(concept, profile)

    # Store quiz in session
    db.update_session(request.user_id, "current_quiz", quiz)

    await analytics.track_event("quiz_started", request.user_id, {
        "concept": concept,
        "difficulty": quiz["difficulty"],
    })

    return quiz

# ─── Quiz: Submit Answer ─────────────────────────────────────────
@app.post("/feedback")
async def submit_answer(answer: QuizAnswer) -> Dict[str, Any]:
    """Evaluate a quiz answer and update the knowledge graph."""
    if not validate_user_id(answer.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    profile = await db.get_user_profile(answer.user_id)

    # Evaluate with FeedbackAgent
    evaluation = await feedback_agent.evaluate_answer(
        question=answer.question,
        user_answer=answer.user_answer,
        correct_answer=answer.correct_answer,
        concept=answer.concept,
        user_profile=profile,
    )

    # Update knowledge graph with AdaptationAgent
    update = InteractionUpdate(
        user_id=answer.user_id,
        concept=answer.concept,
        is_correct=evaluation.get("is_correct", False),
        response_time_ms=10000,  # Default; frontend can provide actual timing
    )
    profile = adaptation_agent.update_knowledge_graph(profile, update)

    # Track misconceptions
    misconceptions = evaluation.get("misconceptions", [])
    if misconceptions:
        profile = adaptation_agent.update_misconceptions(
            profile, answer.concept, misconceptions
        )

    # Save updated profile
    await db.save_user_profile(profile)

    # Track analytics
    await analytics.track_quiz(
        answer.user_id, answer.concept, evaluation.get("score", 0.0)
    )

    return {
        **evaluation,
        "updated_knowledge": profile.knowledge_graph.concepts,
        "weak_areas": profile.weak_areas,
        "current_state": profile.current_state.value,
    }

# ─── Profile: Get ────────────────────────────────────────────────
@app.get("/profile/{user_id}")
async def get_profile(user_id: str) -> Dict[str, Any]:
    """Get user profile with full knowledge graph."""
    if not validate_user_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    profile = await db.get_user_profile(user_id)
    return {
        "user_id": profile.user_id,
        "learning_style": profile.learning_style.value,
        "pace": profile.pace.value,
        "current_state": profile.current_state.value,
        "current_topic": profile.current_topic,
        "knowledge_graph": profile.knowledge_graph.concepts,
        "weak_areas": profile.weak_areas,
        "misconceptions": profile.misconceptions,
        "history_count": len(profile.history),
    }

# ─── Profile: Update Preferences ─────────────────────────────────
@app.put("/profile")
async def update_profile(update: ProfileUpdate) -> Dict[str, Any]:
    """Update user learning preferences."""
    if not validate_user_id(update.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    profile = await db.get_user_profile(update.user_id)

    if update.learning_style:
        profile.learning_style = update.learning_style
    if update.pace:
        profile.pace = update.pace

    await db.save_user_profile(profile)

    await analytics.track_event("profile_updated", update.user_id, {
        "learning_style": profile.learning_style.value,
        "pace": profile.pace.value,
    })

    return {"status": "updated", "profile": {
        "learning_style": profile.learning_style.value,
        "pace": profile.pace.value,
    }}

# ─── Content: Generate ───────────────────────────────────────────
@app.post("/content")
async def generate_content(request: UserQuery) -> Dict[str, Any]:
    """Generate personalized educational content."""
    if not validate_user_id(request.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    profile = await db.get_user_profile(request.user_id)
    content = await content_agent.generate_content(request.query, profile)
    return content

# ─── Progress: Update ────────────────────────────────────────────
@app.post("/update-progress")
async def update_progress(update: InteractionUpdate) -> Dict[str, Any]:
    """Directly update knowledge graph (legacy endpoint)."""
    if not validate_user_id(update.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    profile = await db.get_user_profile(update.user_id)
    profile = adaptation_agent.update_knowledge_graph(profile, update)
    await db.save_user_profile(profile)

    return {
        "status": "success",
        "concept": update.concept,
        "new_score": profile.knowledge_graph.concepts.get(update.concept),
        "current_state": profile.current_state.value,
    }

# ─── Error Handler ───────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "An internal error occurred. Please try again."},
    )

# ─── Entry Point ─────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
