import json
import numpy as np
from fastapi import APIRouter, HTTPException

from app.core.config import Settings
from app.core.templates import TemplateManager
from app.models.faiss_index import FAISSIndex
from app.models.schemas import ChatRequest, ChatResponse
from app.models.llm import LLM
from app.models.ocr import OCR

chat_router = APIRouter(redirect_slashes=False)

# Initialize service components
ocr_handler = OCR()
template_builder = TemplateManager()
language_model = LLM()

# Set up FAISS vector search
vector_store = FAISSIndex(
    index_path=Settings.INDEX_FILE,
    meta_path=Settings.METADATA_FILE,
    embed_dim=Settings.VECTOR_DIMENSION,
    similarity_threshold=Settings.MATCH_THRESHOLD,
)

@chat_router.post("", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    additional_matches = None

    # Step 1: Extract OCR content if image is provided
    if request.image:
        try:
            extracted_text = ocr_handler.extract_text(request.image)
            combined_input = f"{request.question}\n\nOCR result:\n{extracted_text}"

            # Convert the input into an embedding vector
            embedded_query = await language_model.embed(combined_input)
            embedded_query = np.array(embedded_query, dtype=np.float32)

            # Optional: get additional context from OCR
            additional_matches = vector_store.search(embedded_query, k=15)
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"OCR processing failed: {err}")
    else:
        combined_input = request.question

    if not combined_input:
        raise HTTPException(status_code=400, detail="Query is required.")

    # Step 2: Embed the main (or OCR-augmented) query
    embedded_query = await language_model.embed(combined_input)
    embedded_query = np.array(embedded_query, dtype=np.float32)

    # Step 3: Retrieve relevant content via FAISS
    primary_matches = vector_store.search(embedded_query, k=15)
    if additional_matches:
        primary_matches.extend(additional_matches)

    if not primary_matches:
        return ChatResponse(
            answer="I don't have enough context to answer that question.",
            links=[],
        )

    # Step 4: Construct the prompt using matched excerpts
    selected_texts = vector_store.generate_excerpts(primary_matches)
    prompt_text = template_builder.build_prompt(selected_texts, combined_input)

    # Step 5: Request a response from the language model
    try:
        llm_output = await language_model.generate_response(
            prompt_text, response_format=Settings.OUTPUT_STRUCTURE
        )

        if llm_output.refusal:
            return ChatResponse(
                answer="I don't have enough context to answer that question.",
                links=[],
            )

        parsed = json.loads(llm_output.content.strip())
        return ChatResponse(answer=parsed["answer"], links=parsed["links"])

    except Exception as err:
        raise HTTPException(status_code=500, detail=f"LLM response failed: {err}")

def include_router(app):
    app.include_router(chat_router)