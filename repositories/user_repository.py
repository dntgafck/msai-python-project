from typing import Optional, List
from database.connection import DatabaseConnection
from models.entities import User


class UserRepository:
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    def create(self, username: str, email: str, password_hash: str = "") -> User:
        """Create a new user."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user (email, password_hash)
                VALUES (?, ?)
                """,
                (email, password_hash)
            )
            user_id = cursor.lastrowid
            return User(id=user_id, email=email, password_hash=password_hash)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return User.from_row(row) if row else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            return User.from_row(row) if row else None
    
    def get_all(self) -> List[User]:
        """Get all users."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("SELECT * FROM user ORDER BY created_at DESC")
            return [User.from_row(row) for row in cursor.fetchall()]
    
    def update(self, user: User) -> bool:
        """Update user information."""
        if not user.id:
            raise ValueError("User must have an ID to update")
        
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE user 
                SET email = ?, password_hash = ?
                WHERE id = ?
                """,
                (user.email, user.password_hash, user.id)
            )
            return cursor.rowcount > 0
    
    def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
            return cursor.rowcount > 0
    
    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        with self.db_connection.get_cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM user WHERE email = ?",
                (email,)
            )
            return cursor.fetchone()[0] > 0 