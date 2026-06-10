import json
import re
from typing import Any

import httpx

from app.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.llm_model = settings.ollama_llm_model
        self.embed_model = settings.ollama_embed_model
        self.use_mock = settings.use_mock_llm

    async def is_available(self) -> bool:
        if self.use_mock:
            return True
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def generate(self, prompt: str, system: str = "") -> str:
        if self.use_mock:
            return self._mock_generate(prompt)

        payload: dict[str, Any] = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                return response.json().get("response", "")
        except httpx.HTTPError:
            self.use_mock = True
            return self._mock_generate(prompt)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if self.use_mock:
            return [self._mock_embedding(text) for text in texts]

        embeddings: list[list[float]] = []
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                for text in texts:
                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.embed_model, "prompt": text},
                    )
                    response.raise_for_status()
                    embeddings.append(response.json()["embedding"])
            return embeddings
        except httpx.HTTPError:
            self.use_mock = True
            return [self._mock_embedding(text) for text in texts]

    def _mock_embedding(self, text: str, dim: int = 384) -> list[float]:
        seed = sum(ord(c) for c in text[:200])
        return [((seed * (i + 1)) % 1000) / 1000.0 for i in range(dim)]

    def _mock_generate(self, prompt: str) -> str:
        if "interview questions" in prompt.lower() or "generate" in prompt.lower():
            return json.dumps(
                {
                    "questions": [
                        {
                            "question": "Explain the bias-variance tradeoff and how it affects model selection.",
                            "topic": "Model Evaluation",
                            "difficulty": "medium",
                            "rationale": "Core ML concept from Mitchell; tests foundational understanding.",
                        },
                        {
                            "question": "How would you implement cross-validation for an imbalanced classification dataset?",
                            "topic": "Practical ML",
                            "difficulty": "hard",
                            "rationale": "Aligns with candidate's sklearn experience and role requirements.",
                        },
                        {
                            "question": "Describe the difference between L1 and L2 regularization.",
                            "topic": "Regularization",
                            "difficulty": "easy",
                            "rationale": "Baseline check on regularization knowledge from Hundred-Page ML Book.",
                        },
                        {
                            "question": "Walk through building a scikit-learn pipeline with preprocessing and a classifier.",
                            "topic": "MLOps Basics",
                            "difficulty": "medium",
                            "rationale": "Resume mentions Python and sklearn; practical implementation question.",
                        },
                        {
                            "question": "When would you choose a random forest over gradient boosting?",
                            "topic": "Ensemble Methods",
                            "difficulty": "medium",
                            "rationale": "Ensemble methods are central to the ML Engineer role knowledge base.",
                        },
                    ]
                }
            )

        if "evaluate" in prompt.lower() or "summary" in prompt.lower():
            return json.dumps(
                {
                    "overall_score": 72.5,
                    "strengths": [
                        "Solid grasp of model evaluation concepts",
                        "Practical sklearn pipeline experience",
                    ],
                    "weaknesses": [
                        "Limited depth on ensemble tuning strategies",
                        "Could improve explanation of regularization tradeoffs",
                    ],
                    "topic_scores": {
                        "Model Evaluation": 80.0,
                        "Practical ML": 75.0,
                        "Regularization": 65.0,
                        "MLOps Basics": 70.0,
                        "Ensemble Methods": 68.0,
                    },
                    "recommendation": "Proceed to technical round with focus on ensemble methods.",
                    "detailed_insights": "The candidate demonstrates practical ML skills aligned with their resume. Answers show working knowledge of sklearn and evaluation, but deeper theoretical grounding in regularization and boosting would strengthen their profile for a senior ML Engineer role.",
                }
            )

        return "Mock LLM response generated for development."

    @staticmethod
    def extract_json(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if fence_match:
            cleaned = fence_match.group(1)
        else:
            brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if brace_match:
                cleaned = brace_match.group(0)
        return json.loads(cleaned)


llm_client = LLMClient()
