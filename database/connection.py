import sqlite3
import os
from typing import Optional
from contextlib import contextmanager
from pathlib import Path


class DatabaseConnection:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection, creating it if necessary."""
        if self._connection is None:
            # Ensure the directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            # Set row factory to return dictionaries
            self._connection.row_factory = sqlite3.Row
        
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursors."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global database connection instance
db = DatabaseConnection() 