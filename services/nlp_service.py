import os
import spacy
from spacy.language import Language
from typing import List, Dict, Optional, Set
from collections import defaultdict
import logging


class NLPService:
    """
    Pure NLP service for extracting unfamiliar word lemmas from Dutch text.
    
    This service is a standalone component that:
    1. Loads Dutch spaCy model
    2. Filters Dutch words with custom pipeline
    3. De-duplicates and merges surface forms
    4. Returns sorted results
    
    No database dependencies - purely text processing.
    Uses spaCy's built-in Dutch stopwords for filtering.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize NLP service with Dutch spaCy model.
        
        Args:
            model_name: spaCy model name (defaults to NLP_MODEL env var or 'nl_core_news_lg')
        """
        self.model_name = model_name or os.getenv('NLP_MODEL', 'nl_core_news_lg')
        self.nlp = None
        
        # Initialize spaCy model
        self._load_model()
    
    def _load_model(self):
        """Load Dutch spaCy model and add custom pipeline component."""
        try:
            logging.info(f"Loading Dutch spaCy model: {self.model_name}")
            self.nlp = spacy.load(self.model_name)
            
            # Add custom pipeline component
            if "filter_words" not in self.nlp.pipe_names:
                self.nlp.add_pipe("filter_words", after="tagger")
            
            logging.info(f"Dutch spaCy model loaded successfully: {self.model_name}")
        except OSError:
            logging.error(f"Dutch spaCy model '{self.model_name}' not found. Please install it with:")
            logging.error(f"python -m spacy download {self.model_name}")
            raise
    
    def process_text(self, text: str, known_words: Optional[Set[str]] = None) -> List[Dict]:
        """
        Process Dutch text and return unfamiliar word lemmas.
        
        Args:
            text: Dutch text to process
            known_words: Set of known words to filter out (optional)
            
        Returns:
            List of dictionaries with lemma, surface_forms, and count
        """
        if not text.strip():
            return []
        
        if self.nlp is None:
            logging.error("NLP model not loaded")
            return []
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract unfamiliar words
        unfamiliar_words = self._extract_unfamiliar_words(doc, known_words or set())
        
        # De-duplicate and merge surface forms
        merged_words = self._merge_surface_forms(unfamiliar_words)
        
        # Convert to result format and sort
        results = self._format_results(merged_words)
        
        return results
    
    def _extract_unfamiliar_words(self, doc, known_words: Set[str]) -> Dict[str, List[str]]:
        """
        Extract unfamiliar Dutch words from spaCy document.
        
        Args:
            doc: spaCy document
            known_words: Set of known words to filter out
            
        Returns:
            Dictionary mapping lemmas to surface forms
        """
        unfamiliar_words = defaultdict(list)
        
        for token in doc:
            # Include all parts of speech (not just nouns)
            if token.pos_ in ["NOUN", "VERB", "ADJ", "ADV", "PROPN"]:
                lemma = token.lemma_.lower()
                surface_form = token.text
                
                # Skip if token is stop word (spaCy's built-in Dutch stopwords)
                if token.is_stop:
                    continue
                
                # Skip if lemma is in known words
                if lemma in known_words:
                    continue
                
                # Skip if lemma is too short (likely not meaningful)
                if len(lemma) < 2:
                    continue
                
                # Dutch word validation
                if not self._is_valid_dutch_word(lemma):
                    continue
                
                # Add to results
                unfamiliar_words[lemma].append(surface_form)
        
        return dict(unfamiliar_words)
    
    def _is_valid_dutch_word(self, word: str) -> bool:
        """
        Check if a word is a valid Dutch word.
        
        Args:
            word: Word to check
            
        Returns:
            True if valid Dutch word
        """
        # Basic Dutch word validation
        # Allow common Dutch characters and patterns
        valid_chars = set('abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ')
        
        # Check if word contains only valid characters
        if not all(c in valid_chars for c in word.lower()):
            return False
        
        # Skip very short words
        if len(word) < 2:
            return False
        
        # Skip words that look like numbers or symbols
        if word.isdigit() or not word.isalpha():
            return False
        
        return True
    
    def _merge_surface_forms(self, words: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        De-duplicate and merge surface forms for each lemma.
        
        Args:
            words: Dictionary mapping lemmas to surface forms
            
        Returns:
            Dictionary with deduplicated surface forms
        """
        merged = {}
        
        for lemma, surface_forms in words.items():
            # Remove duplicates while preserving order
            unique_forms = []
            seen = set()
            
            for form in surface_forms:
                if form not in seen:
                    unique_forms.append(form)
                    seen.add(form)
            
            merged[lemma] = unique_forms
        
        return merged
    
    def _format_results(self, words: Dict[str, List[str]]) -> List[Dict]:
        """
        Format results and sort them.
        
        Args:
            words: Dictionary mapping lemmas to surface forms
            
        Returns:
            List of dictionaries with lemma, surface_forms, and count
        """
        results = []
        
        for lemma, surface_forms in words.items():
            results.append({
                "lemma": lemma,
                "surface_forms": surface_forms,
                "count": len(surface_forms)
            })
        
        # Sort by count (descending) then alphabetically
        return sorted(results, key=lambda x: (-x["count"], x["lemma"]))


# Register custom spaCy pipeline component
@Language.component("filter_words")
def filter_words_component(doc):
    """
    Custom spaCy pipeline component for word filtering.
    This component doesn't modify the doc but provides a hook for custom processing.
    """
    return doc 