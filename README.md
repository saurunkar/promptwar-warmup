# Aegis AI — Agentic Intelligent Learning Assistant

Aegis is an advanced, AI-powered learning companion designed to adapt to a user's unique learning style, pace, and knowledge mastery in real-time. Built on Google Cloud Platform and powered by Gemini 2.0, Aegis provides a deeply personalized educational experience.

## 🎯 Core Objectives

1. **Adapts to User Pace and Comprehension**: Dynamically scales the complexity of explanations based on real-time knowledge graph metrics.
2. **Personalizes Learning Paths**: Tracks concepts and automatically generates custom learning paths based on weaknesses and misconceptions.
3. **Uses LLMs for Explanation, Questioning, and Feedback**: Employs Gemini for dynamic content generation, contextual quiz creation, and deterministic answer evaluation.
4. **Continuously Updates User Knowledge Models**: Utilizes reinforcement learning mechanics to track mastery across a multidimensional knowledge graph.

## 🏗️ Architecture

Aegis uses a microservices architecture deployed entirely on Google Cloud Run.

* **Frontend**: Next.js 14, React, Tailwind-inspired Vanilla CSS, and Lucide Icons.
* **Backend**: FastAPI, Pydantic, and specialized Sub-Agents.
* **Database**: Google Cloud Firestore (Native Mode) for Profiles, Content, and Session Memory.
* **LLM Layer**: Vertex AI / Google Generative AI (Gemini 2.0 Flash/Pro).
* **Analytics & Observability**: Google Cloud Pub/Sub and Cloud Logging.
* **Security**: Google Secret Manager and custom Input/Output filtering middleware.

### Agent System

The backend is driven by a sophisticated Multi-Agent Orchestrator:
* **Orchestrator Agent**: Manages state transitions (Introduction → Deep Dive → Practice) and routes intent.
* **Assessment Agent**: Dynamically generates topic-specific quizzes based on current mastery level.
* **Feedback Agent**: Evaluates free-text answers, detects misconceptions, and provides encouraging feedback.
* **Adaptation Agent**: Updates the knowledge graph using time-weighted scoring and misconception tracking.
* **Content Agent**: Generates multi-modal content aligned with the user's preferred learning style (Visual, Textual, Mixed).

## 🚀 Quick Start (Local Development)

### Prerequisites
* Node.js 18+
* Python 3.11+
* Google Cloud SDK (`gcloud`)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Export your Gemini API Key
export GOOGLE_API_KEY="your-api-key"

# Run the API server
uvicorn main:app --reload --port 8080
```

### 2. Frontend Setup
```bash
cd frontend
npm install

# The frontend expects the backend on 8080 by default
npm run dev
```

### 3. Testing
Aegis includes a comprehensive test suite covering security, agents, models, and endpoints.
```bash
cd backend
pip install -r requirements-test.txt
pytest -v
```

## ☁️ Google Cloud Deployment

Aegis is fully containerized and deploys automatically to Cloud Run using Cloud Build.

1. Create a Google Cloud Project and enable APIs (Cloud Run, Cloud Build, Firestore, Secret Manager).
2. Store your API key in Secret Manager:
   ```bash
   echo -n "your-key" | gcloud secrets create gemini-api-key --data-file=-
   ```
3. Trigger the deployment:
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```

## 🛡️ Security & Privacy
* **Prompt Injection Protection**: Real-time regex and length-based sanitization.
* **Toxicity Filtering**: Automatic blocking of harmful, dangerous, or sexually explicit content via Gemini Safety Settings and custom middleware.
* **Secure Secrets**: API keys are injected at runtime via GCP Secret Manager.

## 📊 Evaluation Criteria Addressed
* **Code Quality**: Modular agent design, strict typing via Pydantic, and comprehensive documentation.
* **Security**: Input sanitization, output filtering, and robust IAM integration.
* **Efficiency**: Next.js standalone builds, asynchronous FastAPI architecture, and optimized Docker images.
* **Testing**: Comprehensive Pytest suite covering all critical layers.
* **Accessibility**: High-contrast UI, semantic HTML, and responsive 3-column layout.
* **Google Services**: Deep integration with Cloud Run, Firestore, Pub/Sub, Cloud Logging, Secret Manager, Cloud Build, and Artifact Registry.
