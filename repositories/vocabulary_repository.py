from typing import List, Optional
from database.connection import DatabaseConnection
from models.entities import VocabularyDeck, VocabularyDeckWord


class VocabularyRepository:
    def __init__(self, db_connection: DatabaseConnection):
        """Initialize repository with database connection."""
        self.db_connection = db_connection
    
    def create_deck(self, user_id: int, name: str, description: str = "") -> VocabularyDeck:
        """Create a new vocabulary deck."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO vocabulary_deck (user_id, name, description) VALUES (?, ?, ?)",
                (user_id, name, description)
            )
            deck_id = cursor.lastrowid
            
            return VocabularyDeck(
                id=deck_id,
                user_id=user_id,
                name=name,
                description=description
            )
    
    def get_deck_by_id(self, deck_id: int) -> Optional[VocabularyDeck]:
        """Get deck by ID."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM vocabulary_deck WHERE id = ?",
                (deck_id,)
            )
            row = cursor.fetchone()
            return VocabularyDeck.from_row(row) if row else None
    
    def get_user_decks(self, user_id: int) -> List[VocabularyDeck]:
        """Get all decks for a user."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM vocabulary_deck WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            return [VocabularyDeck.from_row(row) for row in cursor.fetchall()]
    
    def update_deck(self, deck_id: int, name: str, description: str = "") -> bool:
        """Update deck information."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "UPDATE vocabulary_deck SET name = ?, description = ? WHERE id = ?",
                (name, description, deck_id)
            )
            return cursor.rowcount > 0
    
    def delete_deck(self, deck_id: int) -> bool:
        """Delete deck and all its words."""
        with self.db_connection.get_cursor() as cursor:
            # Delete deck words first
            cursor.execute("DELETE FROM vocabulary_deck_word WHERE deck_id = ?", (deck_id,))
            # Delete deck
            cursor.execute("DELETE FROM vocabulary_deck WHERE id = ?", (deck_id,))
            return cursor.rowcount > 0
    
    def add_word_to_deck(self, deck_id: int, word_id: int) -> bool:
        """Add a word to a deck."""
        with self.db_connection.get_cursor() as cursor:
            try:
                cursor.execute(
                    "INSERT INTO vocabulary_deck_word (deck_id, word_id) VALUES (?, ?)",
                    (deck_id, word_id)
                )
                return True
            except Exception:
                # Word already in deck
                return False
    
    def remove_word_from_deck(self, deck_id: int, word_id: int) -> bool:
        """Remove a word from a deck."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM vocabulary_deck_word WHERE deck_id = ? AND word_id = ?",
                (deck_id, word_id)
            )
            return cursor.rowcount > 0
    
    def get_deck_words(self, deck_id: int) -> List[VocabularyDeckWord]:
        """Get all words in a deck."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM vocabulary_deck_word WHERE deck_id = ? ORDER BY added_at",
                (deck_id,)
            )
            return [VocabularyDeckWord.from_row(row) for row in cursor.fetchall()]
    
    def get_deck_word_count(self, deck_id: int) -> int:
        """Get the number of words in a deck."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM vocabulary_deck_word WHERE deck_id = ?",
                (deck_id,)
            )
            return cursor.fetchone()[0]
    
    def is_word_in_deck(self, deck_id: int, word_id: int) -> bool:
        """Check if a word is in a deck."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM vocabulary_deck_word WHERE deck_id = ? AND word_id = ?",
                (deck_id, word_id)
            )
            return cursor.fetchone()[0] > 0 