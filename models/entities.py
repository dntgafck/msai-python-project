from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class User:
    id: Optional[int] = None
    email: str = ""
    password_hash: str = ""
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row):
        """Create User instance from database row."""
        return cls(
            id=row['id'],
            email=row['email'],
            password_hash=row['password_hash'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )


@dataclass
class Word:
    id: Optional[int] = None
    lemma: str = ""
    language: str = "nl"
    
    @classmethod
    def from_row(cls, row):
        """Create Word instance from database row."""
        return cls(
            id=row['id'],
            lemma=row['lemma'],
            language=row['language']
        )


@dataclass
class Definition:
    id: Optional[int] = None
    word_id: int = 0
    definition: str = ""
    example: str = ""
    english_translation: str = ""
    categories: List[str] = None
    provider_raw: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        if self.provider_raw is None:
            self.provider_raw = {}
    
    @classmethod
    def from_row(cls, row):
        """Create Definition instance from database row."""
        import json
        provider_raw = json.loads(row['provider_raw']) if row['provider_raw'] else {}
        categories = json.loads(row['categories']) if row['categories'] else []
        
        return cls(
            id=row['id'],
            word_id=row['word_id'],
            definition=row['definition'],
            example=row['example'],
            english_translation=row['english_translation'],
            categories=categories,
            provider_raw=provider_raw,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )


@dataclass
class UserKnownWord:
    user_id: int = 0
    word_id: int = 0
    
    @classmethod
    def from_row(cls, row):
        """Create UserKnownWord instance from database row."""
        return cls(
            user_id=row['user_id'],
            word_id=row['word_id']
        )


@dataclass
class VocabularyDeck:
    id: Optional[int] = None
    user_id: int = 0
    name: str = ""
    description: str = ""
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row):
        """Create VocabularyDeck instance from database row."""
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            description=row['description'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )


@dataclass
class VocabularyDeckWord:
    deck_id: int = 0
    word_id: int = 0
    added_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row):
        """Create VocabularyDeckWord instance from database row."""
        return cls(
            deck_id=row['deck_id'],
            word_id=row['word_id'],
            added_at=datetime.fromisoformat(row['added_at']) if row['added_at'] else None
        ) 