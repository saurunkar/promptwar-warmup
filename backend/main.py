from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from agents.orchestrator import LearningOrchestrator
from core.database import DatabaseClient
from models.user import InteractionUpdate

app = FastAPI(title="Agentic Learning Assistant API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserQuery(BaseModel):
    user_id: str
    query: str

db = DatabaseClient()

@app.get("/")
async def root():
    return {"message": "Welcome to the Agentic Learning Assistant API"}

@app.post("/ask")
async def ask_question(request: UserQuery):
    profile = await db.get_user_profile(request.user_id)
    orchestrator = LearningOrchestrator(profile)
    response = await orchestrator.decide_next_step(request.query)
    return response

@app.post("/update-progress")
async def update_progress(update: InteractionUpdate):
    profile = await db.get_user_profile(update.user_id)
    from agents.sub_agents import AdaptationAgent
    adapter = AdaptationAgent(db)
    updated_profile = adapter.update_knowledge_graph(profile, update)
    await db.save_user_profile(updated_profile)
    return {"status": "success", "new_score": updated_profile.knowledge_graph.concepts.get(update.concept)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
