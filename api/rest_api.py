#!/usr/bin/env python3
"""
REST API interface for Dutch language processing and definition generation.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from services.nlp_service import NLPService
from services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dutch Language Learning API",
    description="API for extracting unfamiliar Dutch nouns from text and generating English definitions with Dutch examples",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global service instances
nlp_service: Optional[NLPService] = None
ai_service: Optional[AIService] = None


# Pydantic models for request/response
class ProcessTextRequest(BaseModel):
    text: str = Field(..., description="Dutch text to process", min_length=1)
    known_words: Optional[List[str]] = Field(None, description="List of known Dutch words to filter out")


class GenerateDefinitionsRequest(BaseModel):
    lemmas: List[str] = Field(..., description="List of Dutch lemmas to generate definitions for", min_items=1)


class UnfamiliarNoun(BaseModel):
    lemma: str = Field(..., description="Base form of the Dutch word")
    surface_forms: List[str] = Field(..., description="All surface forms found in text")
    count: int = Field(..., description="Number of occurrences")


class Definition(BaseModel):
    lemma: str = Field(..., description="The Dutch word")
    definition: str = Field(..., description="English definition of the word")
    example: str = Field(..., description="Dutch example sentence")
    category: str = Field(..., description="Semantic category")
    source: str = Field(..., description="Source of the definition")
    english_translation: str = Field(..., description="English translation of the Dutch example")


class ProcessTextResponse(BaseModel):
    unfamiliar_nouns: List[UnfamiliarNoun] = Field(..., description="List of unfamiliar Dutch nouns")
    total_count: int = Field(..., description="Total number of unfamiliar nouns found")
    text_length: int = Field(..., description="Length of processed text")


class GenerateDefinitionsResponse(BaseModel):
    definitions: List[Definition] = Field(..., description="List of definitions")
    total_count: int = Field(..., description="Total number of definitions")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    nlp_model: str = Field(..., description="spaCy model name")
    ai_model: str = Field(..., description="OpenAI model name")


def get_nlp_service() -> NLPService:
    """Get or create NLP service instance."""
    global nlp_service
    if nlp_service is None:
        logger.info("Initializing Dutch NLP service...")
        nlp_service = NLPService()
        logger.info("Dutch NLP service initialized.")
    return nlp_service


def get_ai_service() -> AIService:
    """Get or create AI service instance."""
    global ai_service
    if ai_service is None:
        logger.info("Initializing AI service...")
        # AI service no longer needs database connection
        ai_service = AIService()
        logger.info("AI service initialized.")
    return ai_service


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    nlp_service = get_nlp_service()
    ai_service = get_ai_service()
    
    return HealthResponse(
        status="healthy",
        service="dutch-language-learning",
        nlp_model=nlp_service.model_name,
        ai_model=ai_service.model
    )


@app.post("/process", response_model=ProcessTextResponse, tags=["Processing"])
async def process_text(request: ProcessTextRequest):
    """
    Process Dutch text and return unfamiliar noun lemmas.
    
    This endpoint analyzes the provided Dutch text and identifies nouns that are:
    - Not spaCy stop words (built-in Dutch stopwords)
    - Not in the provided known words list
    - Proper nouns (NOUN part of speech)
    - At least 2 characters long
    - Valid Dutch words
    
    Results are sorted by frequency count (descending) then alphabetically.
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Get or create NLP service
        nlp_service = get_nlp_service()
        
        # Convert known words to set if provided
        known_words = set(request.known_words) if request.known_words else None
        
        # Process text
        results = nlp_service.process_text(request.text, known_words)
        
        # Convert to response format
        unfamiliar_nouns = []
        for result in results:
            unfamiliar_nouns.append(UnfamiliarNoun(
                lemma=result["lemma"],
                surface_forms=result["surface_forms"],
                count=result["count"]
            ))
        
        return ProcessTextResponse(
            unfamiliar_nouns=unfamiliar_nouns,
            total_count=len(unfamiliar_nouns),
            text_length=len(request.text)
        )
        
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/generate-definitions", response_model=GenerateDefinitionsResponse, tags=["AI"])
async def generate_definitions(request: GenerateDefinitionsRequest):
    """
    Generate definitions for a list of Dutch lemmas using AI.
    
    This endpoint generates English definitions, Dutch examples, and English translations for the provided Dutch lemmas.
    
    The service will:
    - Generate definitions for all provided lemmas
    - Batch process lemmas to minimize API costs
    - Return English definitions with Dutch examples and translations
    - Include semantic categories for each word
    """
    try:
        if not request.lemmas:
            raise HTTPException(status_code=400, detail="Lemmas list cannot be empty")
        
        # Get or create AI service
        ai_service = get_ai_service()
        
        # Generate definitions using new AI service
        definition_items = ai_service.generate_definitions(request.lemmas)
        
        # Convert to response format
        definitions = []
        for item in definition_items:
            definitions.append(Definition(
                lemma=item.lemma,
                definition=item.definition,
                example=item.example,
                category=', '.join(item.category) if item.category else 'general',
                source='openai',
                english_translation=item.english_translation
            ))
        
        return GenerateDefinitionsResponse(
            definitions=definitions,
            total_count=len(definitions)
        )
        
    except Exception as e:
        logger.error(f"Error generating definitions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Dutch Language Learning API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "process": "POST /process",
            "generate_definitions": "POST /generate-definitions",
            "health": "GET /health"
        },
        "language": "Dutch",
        "features": [
            "Extract unfamiliar Dutch nouns from text",
            "Generate English definitions for Dutch words",
            "Provide Dutch examples with English translations",
            "Include semantic categories for Dutch words"
        ]
    }


def create_app():
    """Application factory for FastAPI."""
    return app


if __name__ == '__main__':
    import uvicorn
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(
        "api.rest_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 