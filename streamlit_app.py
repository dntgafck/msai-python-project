#!/usr/bin/env python3
"""
Simplified Streamlit frontend for Dutch Language Learning Service.

This application provides:
1. Text processing: Enter Dutch text, get translations and examples for each word
2. Vocabulary viewer: See all stored words and their definitions
3. Vocabulary management: Create decks and export to Anki
"""

import streamlit as st
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from database.connection import DatabaseConnection
from database.schema import create_tables
from services.nlp_service import NLPService
from services.ai_service import AIService
from services.vocabulary_service import VocabularyService

from repositories.word_repository import WordRepository
from repositories.definition_repository import DefinitionRepository
from repositories.vocabulary_repository import VocabularyRepository


# Page configuration
st.set_page_config(
    page_title="Dutch Language Learning",
    page_icon="🇳🇱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .word-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .deck-card {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_services():
    """Initialize database and services."""
    try:
        logger.info("Initializing services...")
        # Initialize database
        db_connection = DatabaseConnection()
        create_tables(db_connection)
        logger.info("Database initialized successfully")
        
        # Initialize repositories
        word_repo = WordRepository(db_connection)
        definition_repo = DefinitionRepository(db_connection)
        vocabulary_repo = VocabularyRepository(db_connection)
        logger.info("Repositories initialized successfully")
        
        # Initialize services
        nlp_service = NLPService()
        logger.info("NLP service initialized successfully")
        
        # AI service no longer needs database connection
        logger.info("Initializing AI service...")
        ai_service = AIService()
        logger.info("AI service initialized successfully")
        
        # Vocabulary service
        vocab_service = VocabularyService(
            word_repository=word_repo,
            definition_repository=definition_repo,
            vocabulary_repository=vocabulary_repo,
            ai_service=ai_service
        )
        logger.info("Vocabulary service initialized successfully")
        
        return db_connection, nlp_service, ai_service, vocab_service
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        st.error(f"Error initializing services: {e}")
        return None, None, None, None


def process_text_and_generate_definitions(text: str):
    """Process Dutch text and generate definitions for all words."""
    try:
        logger.info(f"Starting text processing for text: {text[:100]}...")
        
        db_connection, nlp_service, ai_service, vocab_service = initialize_services()
        if nlp_service is None or ai_service is None:
            logger.error("Services not initialized properly")
            return None
        
        # Initialize repositories for word lookup
        word_repo = WordRepository(db_connection)
        definition_repo = DefinitionRepository(db_connection)
        
        # Process text to get Dutch nouns
        logger.info("Processing text with NLP service...")
        results = nlp_service.process_text(text)
        logger.info(f"NLP processing completed. Found {len(results) if results else 0} results")
        
        if not results:
            logger.info("No Dutch nouns found in text")
            return []
        
        # Get lemmas from results
        lemmas = [result['lemma'] for result in results]
        logger.info(f"Extracted lemmas: {lemmas}")
        
        # Check which words already exist in database
        existing_words = []
        new_words = []
        for lemma in lemmas:
            word = word_repo.get_by_lemma(lemma)
            if word:
                definition = definition_repo.get_by_word_id(word.id)
                if definition:
                    existing_words.append(lemma)
                    continue
            new_words.append(lemma)
        
        if existing_words:
            logger.info(f"Found {len(existing_words)} existing words: {existing_words}")
        if new_words:
            logger.info(f"Need to generate definitions for {len(new_words)} new words: {new_words}")
        
        # Generate definitions for all lemmas using optimized vocabulary service
        logger.info(f"Processing {len(lemmas)} lemmas with vocabulary service...")
        definitions = vocab_service.process_and_save_definitions(lemmas)
        logger.info(f"Definition processing completed. Got {len(definitions) if definitions else 0} definitions")
        
        # Convert Definition objects to dictionary format for display
        result_definitions = []
        for definition in definitions:
            # Get the word for this definition to access the lemma
            word = word_repo.get_by_id(definition.word_id)
            lemma = word.lemma if word else "unknown"
            
            result_definitions.append({
                'lemma': lemma,
                'definition': definition.definition,
                'example': definition.example,
                'english_translation': definition.english_translation,
                'category': ', '.join(definition.categories) if definition.categories else 'general',
                'source': 'database' if lemma in existing_words else 'openai',
                'existing': lemma in existing_words,
                'error': None
            })
        
        return result_definitions
    except Exception as e:
        logger.error(f"Error processing text: {e}", exc_info=True)
        st.error(f"Error processing text: {e}")
        return None


def display_word_with_definition(word_data: Dict[str, Any]):
    """Display a word with its definition and example."""
    with st.container():
        # Show source indicator
        source_icon = "💾" if word_data.get('existing', False) else "🤖"
        source_text = "From Database" if word_data.get('existing', False) else "AI Generated"
        
        st.markdown(f"""
        <div class="word-card">
            <h3>🇳🇱 {word_data['lemma'].upper()}</h3>
            <p><small>{source_icon} {source_text}</small></p>
        """, unsafe_allow_html=True)
        
        if word_data.get('error'):
            st.error(f"❌ Error: {word_data['error']}")
        else:
            st.markdown(f"""
            <p><strong>📖 Definition:</strong> {word_data['definition']}</p>
            <p><strong>💬 Example:</strong> {word_data['example']}</p>
            <p><strong>🌐 Translation:</strong> {word_data['english_translation']}</p>
            <p><strong>🏷️ Category:</strong> {word_data['category']}</p>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


def get_english_translation_from_definition(definition):
    """Extract english_translation from definition's provider_raw field."""
    try:
        if definition.provider_raw and isinstance(definition.provider_raw, dict):
            return definition.provider_raw.get('english_translation', 'Not available')
        return 'Not available'
    except:
        return 'Not available'


def main():
    """Main Streamlit application."""
    logger.info("Starting Streamlit application")
    
    # Header
    st.markdown('<h1 class="main-header">🇳🇱 Dutch Language Learning</h1>', unsafe_allow_html=True)
    
    # Initialize services
    db_connection, nlp_service, ai_service, vocab_service = initialize_services()
    if db_connection is None:
        st.error("Failed to initialize services. Please check your configuration.")
        logger.error("Failed to initialize services")
        return
    
    # Initialize repositories for deck assignment
    word_repo = WordRepository(db_connection)
    definition_repo = DefinitionRepository(db_connection)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📝 Process Text", "📚 My Words", "🗂️ Vocabulary Decks"])
    
    with tab1:
        st.markdown('<h2 class="section-header">Process Dutch Text</h2>', unsafe_allow_html=True)
        
        # Text input
        text_input = st.text_area(
            "Enter Dutch text to process:",
            height=200,
            placeholder="Enter Dutch text here...\n\nExample:\nDe computer verwerkt complexe algoritmes met ongekende snelheid.\nMachine learning modellen analyseren enorme datasets om patronen te identificeren."
        )
        
        # Deck assignment options
        st.subheader("📚 Deck Assignment")
        deck_option = st.radio(
            "Choose deck assignment option:",
            ["No deck assignment", "Add to existing deck", "Create new deck", "Auto-create deck"],
            index=0
        )
        
        selected_deck_id = None
        new_deck_name = None
        new_deck_description = None
        
        if deck_option == "Add to existing deck":
            # Get user's existing decks
            user_id = 1  # For demo purposes
            user_decks = vocab_service.get_user_decks(user_id)
            
            if user_decks:
                deck_names = [deck.name for deck in user_decks]
                selected_deck_name = st.selectbox("Select deck:", deck_names)
                selected_deck_id = next(deck.id for deck in user_decks if deck.name == selected_deck_name)
            else:
                st.info("No existing decks found. Create a deck first or choose 'Create new deck'.")
                deck_option = "Create new deck"
        
        elif deck_option == "Create new deck":
            new_deck_name = st.text_input("New deck name:", placeholder="e.g., My Dutch Vocabulary")
            new_deck_description = st.text_area("Deck description:", placeholder="Optional description...")
        
        elif deck_option == "Auto-create deck":
            st.info("🎯 A deck will be automatically created based on the words found in your text.")
            deck_prefix = st.text_input("Deck name prefix:", value="Dutch Vocabulary", placeholder="e.g., My Dutch Words")
        
        # Process button
        if st.button("🚀 Process Text & Generate Definitions", type="primary"):
            if text_input.strip():
                logger.info("User clicked process button")
                with st.spinner("Processing Dutch text and generating definitions..."):
                    # Process text and generate definitions
                    definitions = process_text_and_generate_definitions(text_input)
                    
                    if definitions:
                        logger.info(f"Successfully processed {len(definitions)} definitions")
                        st.success(f"✅ Processed {len(definitions)} Dutch words")
                        
                        # Handle deck assignment
                        if deck_option == "Add to existing deck" and selected_deck_id:
                            try:
                                # Get word IDs from definitions by looking up words by lemma
                                word_ids = []
                                for definition in definitions:
                                    word = word_repo.get_by_lemma(definition['lemma'])
                                    if word:
                                        word_ids.append(word.id)
                                
                                # Add words to selected deck
                                vocab_service.add_words_to_deck(selected_deck_id, word_ids)
                                st.success(f"✅ Added {len(word_ids)} words to deck")
                            except Exception as e:
                                st.error(f"Error adding words to deck: {e}")
                        
                        elif deck_option == "Create new deck" and new_deck_name:
                            try:
                                # Create new deck and add words
                                user_id = 1  # For demo purposes
                                deck = vocab_service.create_vocabulary_deck(user_id, new_deck_name, new_deck_description)
                                
                                # Get word IDs from definitions by looking up words by lemma
                                word_ids = []
                                for definition in definitions:
                                    word = word_repo.get_by_lemma(definition['lemma'])
                                    if word:
                                        word_ids.append(word.id)
                                
                                # Add words to new deck
                                vocab_service.add_words_to_deck(deck.id, word_ids)
                                st.success(f"✅ Created deck '{deck.name}' and added {len(word_ids)} words")
                            except Exception as e:
                                st.error(f"Error creating deck: {e}")
                        
                        elif deck_option == "Auto-create deck":
                            try:
                                # Auto-create deck based on text content
                                user_id = 1  # For demo purposes
                                definitions, deck = vocab_service.process_text_with_auto_deck(
                                    text_input, user_id, deck_prefix
                                )
                                st.success(f"✅ Created deck '{deck.name}' with {len(definitions)} words")
                            except Exception as e:
                                st.error(f"Error auto-creating deck: {e}")
                        
                        # Display results
                        for definition in definitions:
                            display_word_with_definition(definition)
                    else:
                        logger.info("No definitions returned from processing")
                        st.info("No Dutch nouns found in the text or error occurred.")
            else:
                logger.info("User clicked process button but no text provided")
                st.warning("Please enter some Dutch text to process.")
    
    with tab2:
        st.markdown('<h2 class="section-header">My Vocabulary</h2>', unsafe_allow_html=True)
        
        # View stored words
        all_words = word_repo.get_all()
        logger.info(f"Found {len(all_words)} words in database")
        
        if all_words:
            st.info(f"📚 Total words in database: {len(all_words)}")
            
            # Search functionality
            search_term = st.text_input("Search words:", placeholder="Enter search term...")
            
            if search_term:
                filtered_words = [w for w in all_words if search_term.lower() in w.lemma.lower()]
                st.write(f"Found {len(filtered_words)} matching words:")
            else:
                filtered_words = all_words[:50]  # Show first 50 words
                st.write("Showing first 50 words:")
            
            # Display words
            for word in filtered_words:
                with st.expander(f"🇳🇱 {word.lemma} ({word.language})"):
                    st.write(f"**ID:** {word.id}")
                    st.write(f"**Language:** {word.language}")
                    
                    # Show definitions
                    definitions = definition_repo.get_all()
                    word_definitions = [d for d in definitions if d.word_id == word.id]
                    
                    if word_definitions:
                        st.write("**Definitions:**")
                        for def_item in word_definitions:
                            st.write(f"- {def_item.definition} ({', '.join(def_item.categories)})")
                            st.write(f"  Example: {def_item.example}")
                            st.write(f"  Translation: {def_item.english_translation}")
                    else:
                        st.write("No definitions available")
        else:
            st.info("No words stored in database yet.")
            st.info("Process some Dutch text to start building your vocabulary!")
    
    with tab3:
        st.markdown('<h2 class="section-header">Vocabulary Decks</h2>', unsafe_allow_html=True)
        
        # For demo purposes, use user_id = 1
        user_id = 1
        
        # Create new deck section
        st.subheader("Create New Deck")
        with st.form("create_deck"):
            deck_name = st.text_input("Deck Name:", placeholder="e.g., Basic Dutch Vocabulary")
            deck_description = st.text_area("Description:", placeholder="Optional description...")
            
            if st.form_submit_button("Create Deck"):
                if deck_name.strip():
                    try:
                        deck = vocab_service.create_vocabulary_deck(user_id, deck_name, deck_description)
                        st.success(f"✅ Created deck: {deck.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating deck: {e}")
                else:
                    st.warning("Please enter a deck name")
        
        # View existing decks
        st.subheader("My Decks")
        user_decks = vocab_service.get_user_decks(user_id)
        
        if user_decks:
            for deck in user_decks:
                with st.expander(f"📚 {deck.name} ({vocab_service.get_deck_word_count(deck.id)} words)"):
                    st.write(f"**Description:** {deck.description or 'No description'}")
                    st.write(f"**Created:** {deck.created_at.strftime('%Y-%m-%d %H:%M') if deck.created_at else 'Unknown'}")
                    
                    # Show deck words
                    deck_words = vocab_service.get_deck_words(deck.id)
                    if deck_words:
                        st.write("**Words in deck:**")
                        for word in deck_words:
                            st.write(f"- {word['lemma']}: {word['definition'][:50]}...")
                        
                        # Export to Anki
                        if st.button(f"📥 Export to Anki", key=f"export_{deck.id}"):
                            try:
                                with st.spinner("Generating Anki deck..."):
                                    apkg_data = vocab_service.generate_anki_deck(deck.id, deck.name)
                                
                                # Create download button
                                st.download_button(
                                    label=f"📥 Download {deck.name}.apkg",
                                    data=apkg_data,
                                    file_name=f"{deck.name.replace(' ', '_')}.apkg",
                                    mime="application/octet-stream"
                                )
                                st.success("✅ Anki deck generated successfully!")
                            except Exception as e:
                                st.error(f"Error generating Anki deck: {e}")
                    else:
                        st.write("No words in this deck yet")
                    
                    # Delete deck
                    if st.button(f"🗑️ Delete Deck", key=f"delete_{deck.id}"):
                        if vocab_service.delete_deck(deck.id):
                            st.success("✅ Deck deleted")
                            st.rerun()
                        else:
                            st.error("Error deleting deck")
        else:
            st.info("No vocabulary decks created yet.")
            st.info("Create a deck to start organizing your vocabulary!")


if __name__ == "__main__":
    main() 