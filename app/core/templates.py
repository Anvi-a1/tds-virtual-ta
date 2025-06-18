import json
from typing import List, Dict, Tuple


class PromptBuilder:
    def __init__(self):
        self.base_instruction = (
            "You are a knowledgeable virtual teaching assistant. "
            "Always refer to the provided excerpts and cite using only the included links. "
            "Do not fabricate information. Use only the following excerpts for your answer:\n\n"
        )

    def construct_prompt(
        self, sources: List[Tuple[str, Dict]], query: str
    ) -> str:
        prompt_content = self.base_instruction

        for idx, (snippet, metadata) in enumerate(sources, start=1):
            prompt_content += (
                f"Excerpt [{idx}] (source: {metadata['source']} | chunk_id: {metadata.get('chunk_id')}):\n"
                f"{snippet}\n\n"
            )

        prompt_content += (
            "QUESTION:\n"
            f"{query}\n\n"
            "Respond strictly in the following JSON format:\n"
            '{"answer": "...", "links": [{"url": "...", "text": "..."}]}'
        )

        return prompt_content

    def extract_json(self, raw_response: str) -> Dict:
        try:
            return json.loads(raw_response.strip())
        except json.JSONDecodeError as err:
            raise ValueError(f"❌ Unable to parse response as JSON: {err}")

