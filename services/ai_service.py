import os
import json
import logging
from typing import List, Iterable
from openai import OpenAI
from pydantic import BaseModel, Field


class DefinitionItem(BaseModel):
    """Pydantic model for a single definition item."""
    lemma: str = Field(description="The Dutch word (lemma form)")
    definition: str = Field(description="Clear, concise English definition (1-2 sentences)")
    example: str = Field(description="Dutch example sentence showing proper usage")
    english_translation: str = Field(description="English translation of the Dutch example sentence")
    category: List[str] = Field(description="Categories for the word")


definition_schema = {
    "type": "object",
    "properties": {
        "definitions": {
            "type": "array",
            "items": DefinitionItem.schema(),
        }
    },
    "required": ["definitions"],
}

class AIService:
    """
    Service for generating Dutch word definitions via OpenAI's new Python SDK,
    using function calling for structured output.
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
        batch_size: int = 20,
    ):
        """
        Initialize the AIService.

        :param api_key: OpenAI API key (optional, will fall back to OPENAI_API_KEY env var)
        :param model: ChatCompletion model to use (default: gpt-4o-mini)
        :param batch_size: Number of words to send per API call
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.batch_size = batch_size

    def _create_system_message(self) -> str:
        """Create the system message for OpenAI."""
        return (
            "You are a Dutch language learning assistant that provides definitions and examples for Dutch words.\n"
            "\n"
            "For each Dutch word, provide:\n"
            "1. A clear, concise definition in English (1-2 sentences)\n"
            "2. A Dutch example sentence showing proper usage\n"
            "3. The English translation of the example sentence\n"
            "4. A list of semantic categories (e.g., technology, science, business, nature, emotion, food, travel, sports, education, health, art, music, family, work, home, transportation, weather, time, numbers, colors)\n"
            "\n"
            "Be concise but informative. Use simple language that a general audience can understand."
        )

    def _create_user_message(self, lemmas: List[str]) -> str:
        """Create the user message for OpenAI with a batch of lemmas."""
        joined = ", ".join(lemmas)
        return (
            f"Please provide definitions for these Dutch words: {joined}\n"
            "\n"
            "Output must be returned by calling the provided function with the 'definitions' list."
        )

    def generate_definitions(self, lemmas: List[str]) -> List[DefinitionItem]:
        """
        Generate definitions for a list of Dutch words in batches, using function calling for structured output.

        :param lemmas: List of Dutch word lemmas
        :return: List of DefinitionItem parsed from the API responses
        """
        definitions: List[DefinitionItem] = []

        for batch in self._batch(lemmas, self.batch_size):
            messages = [
                {"role": "system", "content": self._create_system_message()},
                {"role": "user", "content": self._create_user_message(batch)},
            ]
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    functions=[{
                        "name": "provide_definitions",
                        "description": "Return definitions in the required JSON format",
                        "parameters": definition_schema,
                    }],
                    function_call={"name": "provide_definitions"},
                )
                func_args = response.choices[0].message.function_call.arguments
                data = json.loads(func_args)
                items = data.get("definitions", [])
            except Exception as e:
                # Fallback to manual parsing of plain assistant response
                logging.warning(
                    f"Function calling failed: {e}. Falling back to manual parsing."
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                )
                content = response.choices[0].message.content
                try:
                    items = json.loads(content)
                except json.JSONDecodeError as jde:
                    raise ValueError(
                        f"Failed to parse JSON from fallback content: {jde}\nContent was: {content}"
                    )

            for obj in items:
                definitions.append(DefinitionItem(**obj))

        return definitions

    @staticmethod
    def _batch(iterable: Iterable[str], size: int) -> Iterable[List[str]]:
        """Yield successive batches of the given size from the iterable."""
        batch: List[str] = []
        for item in iterable:
            batch.append(item)
            if len(batch) == size:
                yield batch
                batch = []
        if batch:
            yield batch
