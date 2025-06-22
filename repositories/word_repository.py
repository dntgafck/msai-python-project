from typing import Optional, List
from database.connection import DatabaseConnection
from models.entities import Word


class WordRepository:
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    def create(self, lemma: str, language: str = "nl") -> Word:
        """Create a new word."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO word (lemma, language)
                VALUES (?, ?)
                """,
                (lemma, language)
            )
            word_id = cursor.lastrowid
            return Word(id=word_id, lemma=lemma, language=language)
    
    def get_by_id(self, word_id: int) -> Optional[Word]:
        """Get word by ID."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM word WHERE id = ?",
                (word_id,)
            )
            row = cursor.fetchone()
            return Word.from_row(row) if row else None
    
    def get_by_word(self, lemma: str, language: str = "nl") -> Optional[Word]:
        """Get word by lemma and language."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM word WHERE lemma = ? AND language = ?",
                (lemma, language)
            )
            row = cursor.fetchone()
            return Word.from_row(row) if row else None
    
    def get_by_lemma(self, lemma: str, language: str = "nl") -> Optional[Word]:
        """Get word by lemma and language."""
        return self.get_by_word(lemma, language)
    
    def get_all(self, language: str = "nl") -> List[Word]:
        """Get all words for a language."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM word WHERE language = ? ORDER BY lemma",
                (language,)
            )
            return [Word.from_row(row) for row in cursor.fetchall()]
    
    def search_by_lemma(self, lemma_pattern: str, language: str = "nl") -> List[Word]:
        """Search words by lemma pattern."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM word WHERE lemma LIKE ? AND language = ? ORDER BY lemma",
                (f"%{lemma_pattern}%", language)
            )
            return [Word.from_row(row) for row in cursor.fetchall()]
    
    def update(self, word: Word) -> bool:
        """Update word information."""
        if not word.id:
            raise ValueError("Word must have an ID to update")
        
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE word 
                SET lemma = ?, language = ?
                WHERE id = ?
                """,
                (word.lemma, word.language, word.id)
            )
            return cursor.rowcount > 0
    
    def delete(self, word_id: int) -> bool:
        """Delete word by ID."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("DELETE FROM word WHERE id = ?", (word_id,))
            return cursor.rowcount > 0
    
    def exists_by_lemma(self, lemma: str, language: str = "nl") -> bool:
        """Check if word exists by lemma and language."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM word WHERE lemma = ? AND language = ?",
                (lemma, language)
            )
            return cursor.fetchone()[0] > 0
    
    def get_or_create(self, lemma: str, language: str = "nl") -> Word:
        """Get existing word or create new one."""
        existing = self.get_by_lemma(lemma, language)
        if existing:
            return existing
        
        return self.create(lemma, language) 