import os
import json
import tempfile
from typing import List, Optional, Dict, Any
from datetime import datetime
import genanki
import hashlib
from services.ai_service import AIService, DefinitionItem
from repositories.word_repository import WordRepository
from repositories.definition_repository import DefinitionRepository
from repositories.vocabulary_repository import VocabularyRepository
from models.entities import Word, Definition, VocabularyDeck, VocabularyDeckWord


class VocabularyService:
    """
    Business-level service for managing vocabulary, saving AI responses to database,
    and generating Anki cards for learning.
    """

    def __init__(self, word_repository: WordRepository, 
                 definition_repository: DefinitionRepository,
                 vocabulary_repository: VocabularyRepository,
                 ai_service: AIService):
        """
        Initialize the VocabularyService.

        :param word_repository: Repository for word operations
        :param definition_repository: Repository for definition operations
        :param vocabulary_repository: Repository for vocabulary deck operations
        :param ai_service: AI service instance for generating definitions
        """
        self.word_repository = word_repository
        self.definition_repository = definition_repository
        self.vocabulary_repository = vocabulary_repository
        self.ai_service = ai_service

    def process_and_save_definitions(self, lemmas: List[str], deck_id: Optional[int] = None) -> List[Definition]:
        """
        Process a list of Dutch lemmas, generate definitions via AI,
        and save them to the database. Optimized to avoid duplicate API calls.
        Optionally assigns words to a vocabulary deck.

        :param lemmas: List of Dutch word lemmas
        :param deck_id: Optional deck ID to assign words to after processing
        :return: List of saved Definition entities
        """
        # Separate existing and new words to optimize API usage
        existing_words = []
        new_lemmas = []
        
        for lemma in lemmas:
            # Check if word already exists with definition
            word = self.word_repository.get_by_lemma(lemma)
            if word:
                definition = self.definition_repository.get_by_word_id(word.id)
                if definition:
                    # Word exists with definition, use existing
                    existing_words.append(definition)
                    continue
            
            # Word doesn't exist or has no definition, add to new list
            new_lemmas.append(lemma)
        
        # Generate definitions only for new words
        new_definitions = []
        if new_lemmas:
            print(f"Generating definitions for {len(new_lemmas)} new words: {new_lemmas}")
            definition_items = self.ai_service.generate_definitions(new_lemmas)
            
            for item in definition_items:
                # Save word if it doesn't exist
                word = self._save_word(item.lemma)
                
                # Save definition
                definition = self._save_definition(word.id, item)
                new_definitions.append(definition)
        else:
            print("All words already exist with definitions, no API calls needed!")
        
        # Combine existing and new definitions
        all_definitions = existing_words + new_definitions
        
        # Sort by original lemma order by finding the word for each definition
        sorted_definitions = []
        
        for lemma in lemmas:
            # Find the word to get the definition
            word = self.word_repository.get_by_lemma(lemma)
            if word:
                definition = self.definition_repository.get_by_word_id(word.id)
                if definition:
                    sorted_definitions.append(definition)
        
        # Assign words to deck if specified
        if deck_id and sorted_definitions:
            word_ids = [defn.word_id for defn in sorted_definitions]
            self.add_words_to_deck(deck_id, word_ids)
            print(f"Assigned {len(word_ids)} words to deck {deck_id}")
        
        return sorted_definitions

    def _save_word(self, lemma: str) -> Word:
        """Save a word to the database, return existing if already present."""
        # Check if word already exists
        existing_word = self.word_repository.get_by_lemma(lemma)
        if existing_word:
            return existing_word
        
        # Create new word
        return self.word_repository.create(lemma, "nl")

    def _save_definition(self, word_id: int, definition_item: DefinitionItem) -> Definition:
        """Save a definition to the database."""
        # Check if definition already exists
        existing_definition = self.definition_repository.get_by_word_id(word_id)
        
        if existing_definition:
            # Update existing definition
            self.definition_repository.update(
                existing_definition.id,
                definition_item.definition,
                definition_item.example,
                definition_item.english_translation,
                definition_item.category,
                definition_item.dict()
            )
            return existing_definition
        
        # Create new definition
        return self.definition_repository.create(
            word_id=word_id,
            definition=definition_item.definition,
            example=definition_item.example,
            english_translation=definition_item.english_translation,
            categories=definition_item.category,
            provider_raw=definition_item.dict()
        )

    def create_vocabulary_deck(self, user_id: int, name: str, description: str = "") -> VocabularyDeck:
        """Create a new vocabulary deck for a user."""
        return self.vocabulary_repository.create_deck(user_id, name, description)

    def add_words_to_deck(self, deck_id: int, word_ids: List[int]) -> None:
        """Add words to a vocabulary deck."""
        for word_id in word_ids:
            self.vocabulary_repository.add_word_to_deck(deck_id, word_id)

    def get_deck_words(self, deck_id: int) -> List[Dict[str, Any]]:
        """Get all words and their definitions for a deck."""
        # Get deck word relationships
        deck_words = self.vocabulary_repository.get_deck_words(deck_id)
        
        words_with_definitions = []
        
        for deck_word in deck_words:
            # Get the word
            word = self.word_repository.get_by_id(deck_word.word_id)
            if not word:
                continue
            
            # Get the definition
            definition = self.definition_repository.get_by_word_id(word.id)
            
            words_with_definitions.append({
                'word_id': word.id,
                'lemma': word.lemma,
                'definition': definition.definition if definition else '',
                'example': definition.example if definition else '',
                'english_translation': definition.english_translation if definition else '',
                'categories': definition.categories if definition else []
            })
        
        return words_with_definitions

    def generate_anki_deck(self, deck_id: int, deck_name: str = None) -> bytes:
        """
        Generate an Anki deck (.apkg file) for the given vocabulary deck.

        :param deck_id: ID of the vocabulary deck
        :param deck_name: Optional custom name for the Anki deck
        :return: Bytes of the .apkg file
        """
        # Get deck words
        words = self.get_deck_words(deck_id)
        
        if not words:
            raise ValueError("No words found in deck")
        
        # Create Anki deck
        deck_id_hash = hashlib.md5(f"dutch_vocab_{deck_id}".encode()).hexdigest()[:10]
        deck_id_int = int(deck_id_hash, 16)
        
        # Create note model for Dutch vocabulary
        model_id = hashlib.md5("dutch_vocab_model".encode()).hexdigest()[:10]
        model_id_int = int(model_id, 16)
        
        note_model = genanki.Model(
            model_id_int,
            'Dutch Vocabulary Model',
            fields=[
                {'name': 'DutchWord'},
                {'name': 'EnglishDefinition'},
                {'name': 'DutchExample'},
                {'name': 'EnglishTranslation'},
                {'name': 'Categories'},
            ],
            templates=[
                {
                    'name': 'Dutch to English',
                    'qfmt': '''
                        <div class="dutch-word">{{DutchWord}}</div>
                        <div class="categories">{{Categories}}</div>
                    ''',
                    'afmt': '''
                        <div class="dutch-word">{{DutchWord}}</div>
                        <div class="english-definition">{{EnglishDefinition}}</div>
                        <hr>
                        <div class="example-section">
                            <div class="dutch-example">{{DutchExample}}</div>
                            <div class="english-translation">{{EnglishTranslation}}</div>
                        </div>
                        <div class="categories">{{Categories}}</div>
                    '''
                },
                {
                    'name': 'English to Dutch',
                    'qfmt': '''
                        <div class="english-definition">{{EnglishDefinition}}</div>
                        <div class="categories">{{Categories}}</div>
                    ''',
                    'afmt': '''
                        <div class="dutch-word">{{DutchWord}}</div>
                        <div class="english-definition">{{EnglishDefinition}}</div>
                        <hr>
                        <div class="example-section">
                            <div class="dutch-example">{{DutchExample}}</div>
                            <div class="english-translation">{{EnglishTranslation}}</div>
                        </div>
                        <div class="categories">{{Categories}}</div>
                    '''
                }
            ],
            css='''
                .card {
                    font-family: Arial, sans-serif;
                    font-size: 18px;
                    text-align: center;
                    color: #333;
                    background-color: #f9f9f9;
                    padding: 20px;
                }
                .dutch-word {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 10px;
                }
                .english-definition {
                    font-size: 20px;
                    color: #34495e;
                    margin-bottom: 15px;
                }
                .example-section {
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                }
                .dutch-example {
                    font-style: italic;
                    color: #7f8c8d;
                    margin-bottom: 5px;
                }
                .english-translation {
                    color: #95a5a6;
                    font-size: 16px;
                }
                .categories {
                    font-size: 14px;
                    color: #95a5a6;
                    font-style: italic;
                }
            '''
        )
        
        # Create deck
        deck = genanki.Deck(deck_id_int, deck_name or f"Dutch Vocabulary Deck {deck_id}")
        
        # Add notes to deck
        for word in words:
            # Create note for Dutch to English
            note = genanki.Note(
                model=note_model,
                fields=[
                    word['lemma'],
                    word['definition'],
                    word['example'],
                    word['english_translation'],
                    ', '.join(word['categories'])
                ]
            )
            deck.add_note(note)
        
        # Generate .apkg file
        package = genanki.Package(deck)
        
        # Create temporary file to store the package
        with tempfile.NamedTemporaryFile(suffix='.apkg', delete=False) as temp_file:
            package.write_to_file(temp_file.name)
            with open(temp_file.name, 'rb') as f:
                apkg_data = f.read()
            
            # Clean up temporary file
            os.unlink(temp_file.name)
        
        return apkg_data

    def get_user_decks(self, user_id: int) -> List[VocabularyDeck]:
        """Get all vocabulary decks for a user."""
        return self.vocabulary_repository.get_user_decks(user_id)

    def get_all_words_with_definitions(self) -> List[Dict[str, Any]]:
        """Get all words with their definitions from the database."""
        all_words = self.word_repository.get_all()
        words_with_definitions = []
        
        for word in all_words:
            definition = self.definition_repository.get_by_word_id(word.id)
            
            words_with_definitions.append({
                'word_id': word.id,
                'lemma': word.lemma,
                'definition': definition.definition if definition else '',
                'example': definition.example if definition else '',
                'english_translation': definition.english_translation if definition else '',
                'categories': definition.categories if definition else [],
                'created_at': definition.created_at if definition else None
            })
        
        return words_with_definitions

    def delete_deck(self, deck_id: int) -> bool:
        """Delete a vocabulary deck."""
        return self.vocabulary_repository.delete_deck(deck_id)

    def get_deck_word_count(self, deck_id: int) -> int:
        """Get the number of words in a deck."""
        return self.vocabulary_repository.get_deck_word_count(deck_id)

    def is_word_in_deck(self, deck_id: int, word_id: int) -> bool:
        """Check if a word is in a deck."""
        return self.vocabulary_repository.is_word_in_deck(deck_id, word_id)

    def process_and_save_definitions_with_deck(self, lemmas: List[str], user_id: int, deck_name: str = None, deck_description: str = "") -> tuple[List[Definition], VocabularyDeck]:
        """
        Process a list of Dutch lemmas, generate definitions via AI,
        save them to the database, and create/assign to a deck.

        :param lemmas: List of Dutch word lemmas
        :param user_id: User ID for the deck
        :param deck_name: Name for the deck (if None, auto-generates)
        :param deck_description: Description for the deck
        :return: Tuple of (List of saved Definition entities, VocabularyDeck)
        """
        # Create deck if name is provided
        deck = None
        if deck_name:
            deck = self.create_vocabulary_deck(user_id, deck_name, deck_description)
            print(f"Created new deck: {deck.name} (ID: {deck.id})")
        
        # Process definitions
        definitions = self.process_and_save_definitions(lemmas, deck.id if deck else None)
        
        return definitions, deck

    def process_text_with_auto_deck(self, text: str, user_id: int, deck_name_prefix: str = "Dutch Vocabulary") -> tuple[List[Definition], VocabularyDeck]:
        """
        Process Dutch text, extract words, generate definitions, and create a deck automatically.
        The deck name will be auto-generated based on the content.

        :param text: Dutch text to process
        :param user_id: User ID for the deck
        :param deck_name_prefix: Prefix for the auto-generated deck name
        :return: Tuple of (List of saved Definition entities, VocabularyDeck)
        """
        from services.nlp_service import NLPService
        
        # Extract Dutch words from text
        nlp_service = NLPService()
        results = nlp_service.process_text(text)
        
        if not results:
            raise ValueError("No Dutch words found in text")
        
        # Get lemmas
        lemmas = [result['lemma'] for result in results]
        
        # Generate deck name based on content
        if len(lemmas) <= 3:
            deck_name = f"{deck_name_prefix}: {', '.join(lemmas)}"
        else:
            deck_name = f"{deck_name_prefix}: {lemmas[0]}, {lemmas[1]}, ... ({len(lemmas)} words)"
        
        # Create deck description
        deck_description = f"Auto-generated deck from text processing. Contains {len(lemmas)} Dutch words."
        
        # Process and create deck
        return self.process_and_save_definitions_with_deck(lemmas, user_id, deck_name, deck_description) 