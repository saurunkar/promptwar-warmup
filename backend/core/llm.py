"""
Centralized LLM Client — Uses Google Generative AI (Gemini) with safety settings,
output filtering, and embedding generation.
"""
import google.generativeai as genai
import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """Singleton-style LLM client with safety filters and structured output."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = None
        self.embed_model = None

        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Gemini Pro for text generation
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=2048,
                ),
            )
            logger.info("Gemini LLM initialized successfully.")
        else:
            logger.warning("GOOGLE_API_KEY not set. Running in mock mode.")

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        """Generate text from Gemini with safety filtering."""
        if not self.model:
            return self._mock_response(prompt)

        try:
            full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
            response = self.model.generate_content(full_prompt)

            # Output filtering — check for blocked content
            if not response.candidates:
                logger.warning("LLM response was blocked by safety filters.")
                return "I'm unable to generate a response for that query. Let's try a different approach."

            return response.text
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return f"I encountered an issue generating a response. Please try again."

    async def generate_json(self, prompt: str, system_instruction: str = "") -> Optional[Dict]:
        """Generate structured JSON output from Gemini."""
        json_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no code fences, no explanation."
        text = await self.generate(json_prompt, system_instruction)

        # Try to parse JSON from the response
        try:
            # Strip markdown code fences if present
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from LLM response: {text[:200]}")
            return None

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings for semantic search."""
        if not self.api_key:
            # Return a mock embedding (768-dim zero vector)
            return [0.0] * 768

        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return [0.0] * 768

    def _mock_response(self, prompt: str) -> str:
        """Provide intelligent mock responses for testing without API key."""
        if "quiz" in prompt.lower():
            return json.dumps([
                {"question": "What is a neural network?", "options": ["A brain scan", "A computational model inspired by the brain", "A type of database", "A programming language"], "correct_answer": "A computational model inspired by the brain"},
                {"question": "What is backpropagation?", "options": ["Forward data flow", "Error correction algorithm", "A sorting method", "A network protocol"], "correct_answer": "Error correction algorithm"},
                {"question": "What is an activation function?", "options": ["A login mechanism", "A function that determines neuron output", "A database query", "A CSS property"], "correct_answer": "A function that determines neuron output"},
            ])
        elif "feedback" in prompt.lower() or "evaluate" in prompt.lower():
            return json.dumps({
                "is_correct": True,
                "score": 0.85,
                "explanation": "Good understanding! Your answer demonstrates solid grasp of the core concept.",
                "misconceptions": [],
                "suggestions": ["Try exploring edge cases", "Consider the mathematical foundations"],
            })
        else:
            return "This is a detailed explanation tailored to your learning style. Neural networks are computational models inspired by the biological neural networks in the human brain. They consist of layers of interconnected nodes (neurons) that process information using connectionist approaches to computation."


# Global singleton
llm_client = LLMClient()
