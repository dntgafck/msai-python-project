from typing import Optional, List
import json
from database.connection import DatabaseConnection
from models.entities import Definition


class DefinitionRepository:
    def __init__(self, db_connection: DatabaseConnection):
        """Initialize repository with database connection."""
        self.db_connection = db_connection
    
    def create(self, word_id: int, definition: str, example: str, 
               english_translation: str, categories: List[str], provider_raw: dict) -> Definition:
        """Create a new definition."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO definition (word_id, definition, example, english_translation, categories, provider_raw)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (word_id, definition, example, english_translation, json.dumps(categories), json.dumps(provider_raw))
            )
            definition_id = cursor.lastrowid
            
            # Return the created definition
            return Definition(
                id=definition_id,
                word_id=word_id,
                definition=definition,
                example=example,
                english_translation=english_translation,
                categories=categories,
                provider_raw=provider_raw
            )
    
    def get_by_id(self, definition_id: int) -> Optional[Definition]:
        """Get definition by ID."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM definition WHERE id = ?",
                (definition_id,)
            )
            row = cursor.fetchone()
            return Definition.from_row(row) if row else None
    
    def get_by_word_id(self, word_id: int) -> Optional[Definition]:
        """Get the definition for a word."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM definition WHERE word_id = ?",
                (word_id,)
            )
            row = cursor.fetchone()
            return Definition.from_row(row) if row else None
    
    def get_all(self) -> List[Definition]:
        """Get all definitions."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("SELECT * FROM definition ORDER BY created_at DESC")
            return [Definition.from_row(row) for row in cursor.fetchall()]
    
    def update(self, definition_id: int, definition: str, example: str, 
               english_translation: str, categories: List[str], provider_raw: dict) -> bool:
        """Update definition information."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE definition 
                SET definition = ?, example = ?, english_translation = ?, categories = ?, provider_raw = ?
                WHERE id = ?
                """,
                (definition, example, english_translation, json.dumps(categories), json.dumps(provider_raw), definition_id)
            )
            return cursor.rowcount > 0
    
    def delete(self, definition_id: int) -> bool:
        """Delete definition by ID."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("DELETE FROM definition WHERE id = ?", (definition_id,))
            return cursor.rowcount > 0
    
    def delete_by_word_id(self, word_id: int) -> bool:
        """Delete all definitions for a word."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("DELETE FROM definition WHERE word_id = ?", (word_id,))
            return cursor.rowcount > 0
    
    def exists_by_word_id(self, word_id: int) -> bool:
        """Check if definition exists by word ID."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM definition WHERE word_id = ?",
                (word_id,)
            )
            return cursor.fetchone()[0] > 0
    
    def get_or_create(self, word_id: int, definition: str, example: str, 
                     english_translation: str, categories: List[str], provider_raw: dict) -> Definition:
        """Get existing definition or create new one."""
        existing = self.get_by_word_id(word_id)
        if existing:
            return existing
        
        return self.create(
            word_id=word_id,
            definition=definition,
            example=example,
            english_translation=english_translation,
            categories=categories,
            provider_raw=provider_raw
        ) 