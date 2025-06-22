from .connection import DatabaseConnection


def create_tables(db_connection: DatabaseConnection):
    """Create all database tables."""
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS user (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS word (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            lemma      TEXT NOT NULL UNIQUE,
            language   TEXT NOT NULL DEFAULT 'nl'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS definition (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id      INTEGER NOT NULL,
            definition   TEXT NOT NULL,
            example      TEXT NOT NULL,
            english_translation TEXT NOT NULL,
            categories   JSON NOT NULL,
            provider_raw JSON NOT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(word_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS vocabulary_deck (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            name        TEXT NOT NULL,
            description TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS vocabulary_deck_word (
            deck_id INTEGER,
            word_id INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (deck_id, word_id),
            FOREIGN KEY (deck_id) REFERENCES vocabulary_deck (id),
            FOREIGN KEY (word_id) REFERENCES word (id)
        )
        """
    ]
    
    # Create indexes for better performance
    index_statements = [
        # Word table indexes
        "CREATE INDEX IF NOT EXISTS idx_word_lemma ON word(lemma)",
        "CREATE INDEX IF NOT EXISTS idx_word_language ON word(language)",
        "CREATE INDEX IF NOT EXISTS idx_word_lemma_language ON word(lemma, language)",
        
        # Definition table indexes
        "CREATE INDEX IF NOT EXISTS idx_definition_word_id ON definition(word_id)",
        "CREATE INDEX IF NOT EXISTS idx_definition_created_at ON definition(created_at)",
        
        # Vocabulary deck indexes
        "CREATE INDEX IF NOT EXISTS idx_vocabulary_deck_user_id ON vocabulary_deck(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_vocabulary_deck_created_at ON vocabulary_deck(created_at)",
        
        # Vocabulary deck word indexes
        "CREATE INDEX IF NOT EXISTS idx_vocabulary_deck_word_deck_id ON vocabulary_deck_word(deck_id)",
        "CREATE INDEX IF NOT EXISTS idx_vocabulary_deck_word_word_id ON vocabulary_deck_word(word_id)",
        "CREATE INDEX IF NOT EXISTS idx_vocabulary_deck_word_added_at ON vocabulary_deck_word(added_at)",
        
        # User table indexes
        "CREATE INDEX IF NOT EXISTS idx_user_email ON user(email)",
        "CREATE INDEX IF NOT EXISTS idx_user_created_at ON user(created_at)"
    ]
    
    with db_connection.get_cursor() as cursor:
        # Create tables
        for statement in ddl_statements:
            cursor.execute(statement)
        
        # Create indexes
        for statement in index_statements:
            cursor.execute(statement)


def drop_tables(db_connection: DatabaseConnection):
    """Drop all database tables (for testing/reset)."""
    tables = [
        'vocabulary_deck_word',
        'vocabulary_deck',
        'definition',
        'word',
        'user'
    ]
    
    with db_connection.get_cursor() as cursor:
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")


def drop_indexes(db_connection: DatabaseConnection):
    """Drop all indexes (for testing/reset)."""
    indexes = [
        'idx_word_lemma',
        'idx_word_language',
        'idx_word_lemma_language',
        'idx_definition_word_id',
        'idx_definition_created_at',
        'idx_vocabulary_deck_user_id',
        'idx_vocabulary_deck_created_at',
        'idx_vocabulary_deck_word_deck_id',
        'idx_vocabulary_deck_word_word_id',
        'idx_vocabulary_deck_word_added_at',
        'idx_user_email',
        'idx_user_created_at'
    ]
    
    with db_connection.get_cursor() as cursor:
        for index in indexes:
            cursor.execute(f"DROP INDEX IF EXISTS {index}")


def reset_database(db_connection: DatabaseConnection):
    """Reset the database by dropping and recreating all tables and indexes."""
    drop_indexes(db_connection)
    drop_tables(db_connection)
    create_tables(db_connection)


def get_database_info(db_connection: DatabaseConnection):
    """Get information about database tables and indexes."""
    with db_connection.get_cursor() as cursor:
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get index information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Get table sizes
        table_sizes = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_sizes[table] = count
        
        return {
            'tables': tables,
            'indexes': indexes,
            'table_sizes': table_sizes
        }


if __name__ == "__main__":
    # Initialize database when run directly
    db_connection = DatabaseConnection()
    create_tables(db_connection)
    
    # Show database info
    info = get_database_info(db_connection)
    print("Database tables created successfully!")
    print(f"Tables: {info['tables']}")
    print(f"Indexes: {info['indexes']}")
    print(f"Table sizes: {info['table_sizes']}") 