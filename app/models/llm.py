from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer
import numpy as np
import os


class LLM:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        # HuggingFace embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # OpenAI client for chat
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # System prompt for virtual TA
        self.system_prompt = (
            "You are a helpful virtual TA for the Tools in Data Science course at IIT Madras. "
            "You only answer questions based on the course material. If the answer isn’t in the course, say so. "
            "Respond in less than 200 words, clearly and concisely. Always return a JSON with an 'answer' and 'links'."
        )

    def embed(self, text: str) -> np.ndarray:
        """Use HuggingFace model to generate normalized embeddings."""
        vec = self.embedding_model.encode(text, normalize_embeddings=True)
        return np.array(vec, dtype=np.float32)

    async def generate_response(self, question: str, excerpts: list[str]) -> dict:
        """Use OpenAI Chat API to generate a course-aligned response."""
        context = "\n\n".join(excerpts[:10])  # Limit for brevity
        user_prompt = (
            f"Course Context:\n{context}\n\n"
            f"Student Question:\n{question}\n\n"
            f"Return a JSON with:\n"
            f'{{"answer": "...", "links": [{{"url": "...", "text": "..."}}]}}'
        )

        response = await self.client.chat.completions.create(
            model="gpt-4o",  # or "gpt-3.5-turbo" as fallback
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format="json",
            temperature=0.3,
        )

        return response.choices[0].message.content