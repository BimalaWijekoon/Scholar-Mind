"""
Database Models - SQLAlchemy models for the application
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Float,
    ForeignKey, Boolean, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from backend.db.database import Base


def _utcnow():
    """Timezone-aware UTC datetime (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """Document model for storing uploaded documents."""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000))
    file_type = Column(String(50))
    file_size = Column(Integer)
    
    # Content
    content = Column(Text)
    abstract = Column(Text)
    
    # Metadata fields (split out — 'metadata' is reserved by SQLAlchemy)
    authors = Column(ARRAY(String))
    publication_date = Column(DateTime)
    doi = Column(String(200))
    keywords = Column(ARRAY(String))
    source_url = Column(String(2000))
    
    # Processing
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    processed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Embeddings
    embedding_id = Column(String(200))
    chunk_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    # Owner
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    entities = relationship("Entity", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title})>"


class DocumentChunk(Base):
    """Document chunk model for storing text chunks."""
    
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Content
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    page_number = Column(Integer)
    
    # Embedding
    embedding_id = Column(String(200))
    
    # Extra data (renamed from 'metadata' — reserved by SQLAlchemy Declarative API)
    extra_data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=_utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class Entity(Base):
    """Entity model for storing extracted entities."""
    
    __tablename__ = "entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity info
    text = Column(String(500), nullable=False)
    entity_type = Column(String(100), nullable=False)
    normalized_text = Column(String(500))
    
    # Source
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    start_char = Column(Integer)
    end_char = Column(Integer)
    
    # Confidence and linking
    confidence = Column(Float, default=1.0)
    linked_id = Column(String(200))    # External KB ID
    linked_source = Column(String(100))  # e.g., "wikidata", "umls"
    
    # Extra data (renamed from 'metadata' — reserved by SQLAlchemy Declarative API)
    extra_data = Column(JSON, default=dict)
    
    # Graph
    neo4j_id = Column(String(200))
    
    # Timestamps
    created_at = Column(DateTime, default=_utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="entities")
    
    def __repr__(self):
        return f"<Entity(id={self.id}, text={self.text}, type={self.entity_type})>"


class Relation(Base):
    """Relation model for storing entity relationships."""
    
    __tablename__ = "relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entities
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    
    # Relation info
    relation_type = Column(String(100), nullable=False)
    confidence = Column(Float, default=1.0)
    
    # Context
    context = Column(Text)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Graph
    neo4j_id = Column(String(200))
    
    # Extra data (renamed from 'metadata' — reserved by SQLAlchemy Declarative API)
    extra_data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=_utcnow)
    
    # Relationships
    source_entity = relationship("Entity", foreign_keys=[source_entity_id])
    target_entity = relationship("Entity", foreign_keys=[target_entity_id])
    
    def __repr__(self):
        return f"<Relation(id={self.id}, type={self.relation_type})>"


class User(Base):
    """User model for authentication and ownership."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Auth
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255))
    
    # Profile
    name = Column(String(255))
    avatar_url = Column(String(500))
    
    # Settings
    settings = Column(JSON, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    documents = relationship("Document", backref="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class QueryHistory(Base):
    """Query history model for tracking user queries."""
    
    __tablename__ = "query_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Query info
    query = Column(Text, nullable=False)
    response = Column(Text)
    
    # Context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(String(200))
    
    # Metrics
    response_time_ms = Column(Integer)
    sources_count = Column(Integer)
    
    # Feedback
    rating = Column(Integer)
    feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=_utcnow)
    
    def __repr__(self):
        return f"<QueryHistory(id={self.id}, query={self.query[:50]}...)>"
