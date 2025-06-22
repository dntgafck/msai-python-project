from typing import List
from database.connection import DatabaseConnection
from models.entities import UserKnownWord


class UserKnownWordRepository:
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    def create(self, user_id: int, word_id: int) -> UserKnownWord:
        """Create a new user known word relationship."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_known_word (user_id, word_id)
                VALUES (?, ?)
                """,
                (user_id, word_id)
            )
            return UserKnownWord(user_id=user_id, word_id=word_id)
    
    def get_by_user_id(self, user_id: int) -> List[UserKnownWord]:
        """Get all known words for a user."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_known_word WHERE user_id = ?",
                (user_id,)
            )
            return [UserKnownWord.from_row(row) for row in cursor.fetchall()]
    
    def get_by_word_id(self, word_id: int) -> List[UserKnownWord]:
        """Get all users who know a specific word."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_known_word WHERE word_id = ?",
                (word_id,)
            )
            return [UserKnownWord.from_row(row) for row in cursor.fetchall()]
    
    def get_by_user_and_word(self, user_id: int, word_id: int) -> UserKnownWord:
        """Get specific user-word relationship."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_known_word WHERE user_id = ? AND word_id = ?",
                (user_id, word_id)
            )
            row = cursor.fetchone()
            return UserKnownWord.from_row(row) if row else None
    
    def get_all(self) -> List[UserKnownWord]:
        """Get all user known word relationships."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("SELECT * FROM user_known_word")
            return [UserKnownWord.from_row(row) for row in cursor.fetchall()]
    
    def delete(self, user_id: int, word_id: int) -> bool:
        """Delete user known word relationship."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM user_known_word WHERE user_id = ? AND word_id = ?",
                (user_id, word_id)
            )
            return cursor.rowcount > 0
    
    def delete_by_user_id(self, user_id: int) -> bool:
        """Delete all known words for a user."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("DELETE FROM user_known_word WHERE user_id = ?", (user_id,))
            return cursor.rowcount > 0
    
    def delete_by_word_id(self, word_id: int) -> bool:
        """Delete all user relationships for a word."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("DELETE FROM user_known_word WHERE word_id = ?", (word_id,))
            return cursor.rowcount > 0
    
    def exists(self, user_id: int, word_id: int) -> bool:
        """Check if user knows a specific word."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM user_known_word WHERE user_id = ? AND word_id = ?",
                (user_id, word_id)
            )
            return cursor.fetchone()[0] > 0
    
    def count_by_user_id(self, user_id: int) -> int:
        """Count how many words a user knows."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM user_known_word WHERE user_id = ?",
                (user_id,)
            )
            return cursor.fetchone()[0]
    
    def count_by_word_id(self, word_id: int) -> int:
        """Count how many users know a specific word."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM user_known_word WHERE word_id = ?",
                (word_id,)
            )
            return cursor.fetchone()[0]
    
    def bulk_create(self, user_known_words: List[UserKnownWord]) -> List[UserKnownWord]:
        """Create multiple user known word relationships in a single transaction."""
        with self.db_connection.get_cursor() as cursor:
            for user_known_word in user_known_words:
                cursor.execute(
                    """
                    INSERT INTO user_known_word (user_id, word_id)
                    VALUES (?, ?)
                    """,
                    (user_known_word.user_id, user_known_word.word_id)
                )
            return user_known_words 