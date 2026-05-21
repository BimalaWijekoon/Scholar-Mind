"""
Document Service - Handle document operations with FULL processing pipeline
"""

from typing import List, Dict, Optional, BinaryIO, Any
from dataclasses import dataclass
from datetime import datetime
import uuid
import logging
import asyncio
from pathlib import Path

from fastapi import UploadFile

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """Document information."""
    id: str
    title: str
    filename: str
    file_type: str
    status: str
    created_at: datetime
    metadata: Dict


class DocumentService:
    """
    Service for document operations.
    
    Handles:
    - Document upload and storage
    - Document processing pipeline (parse → chunk → embed → extract entities → graph)
    - Document retrieval
    - Metadata extraction
    """
    
    def __init__(
        self,
        db=None,
        pdf_parser=None,
        web_parser=None,
        metadata_extractor=None,
        chunker=None,
        embeddings_manager=None,
        vector_store=None,
        entity_extractor=None,
        graph_service=None,
        storage_dir: str = "data/uploads",
    ):
        """
        Initialize the document service.
        
        Args:
            db: Database instance
            pdf_parser: PDF parser instance
            web_parser: Web parser instance
            metadata_extractor: Metadata extractor instance
            chunker: Document chunker instance
            embeddings_manager: Embeddings manager instance
            vector_store: Vector store instance
            entity_extractor: Entity extractor instance
            graph_service: Graph service instance
            storage_dir: Directory for file storage
        """
        self.db = db
        self.pdf_parser = pdf_parser
        self.web_parser = web_parser
        self.metadata_extractor = metadata_extractor
        self.chunker = chunker
        self.embeddings_manager = embeddings_manager
        self.vector_store = vector_store
        self.entity_extractor = entity_extractor
        self.graph_service = graph_service
        self.storage_dir = storage_dir
        
        # In-memory document store for development
        self._documents: Dict[str, DocumentInfo] = {}
        
        # Initialize components if not provided
        self._init_components()
    
    def _init_components(self):
        """Initialize processing components if not provided."""
        print("\n" + "="*60)
        print("🔧 INITIALIZING DOCUMENT PROCESSING COMPONENTS")
        print("="*60)
        
        try:
            # PDF Parser
            if not self.pdf_parser:
                print("   Loading PDF Parser (PyMuPDF)...")
                from backend.core.document_processing.pdf_parser import PDFParser
                self.pdf_parser = PDFParser()
                print("   ✅ PDF Parser ready")
        except Exception as e:
            print(f"   ❌ PDF Parser failed: {e}")
            logger.warning(f"Could not initialize PDF parser: {e}")
        
        try:
            # Document Chunker
            if not self.chunker:
                print("   Loading Document Chunker...")
                from backend.core.document_processing.chunker import DocumentChunker
                self.chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
                print("   ✅ Document Chunker ready (chunk_size=1000, overlap=200)")
        except Exception as e:
            print(f"   ❌ Document Chunker failed: {e}")
            logger.warning(f"Could not initialize chunker: {e}")
        
        try:
            # Embeddings Manager
            if not self.embeddings_manager:
                print("   Loading Embeddings Manager (all-MiniLM-L6-v2)...")
                from backend.core.nlp.embeddings import EmbeddingsManager
                self.embeddings_manager = EmbeddingsManager(model_name="all-MiniLM-L6-v2")
                print(f"   ✅ Embeddings Manager ready (dim: {self.embeddings_manager.dimension})")
        except Exception as e:
            print(f"   ❌ Embeddings Manager failed: {e}")
            logger.warning(f"Could not initialize embeddings manager: {e}")
        
        try:
            # Vector Store
            if not self.vector_store:
                print("   Loading Vector Store (ChromaDB)...")
                from backend.core.retrieval.vector_store import VectorStore, VectorDBType
                self.vector_store = VectorStore(
                    db_type=VectorDBType.CHROMA,
                    collection_name="scholarmind_docs",
                    persist_directory="./data/chroma",
                )
                print("   ✅ Vector Store ready (ChromaDB @ ./data/chroma)")
        except Exception as e:
            print(f"   ❌ Vector Store failed: {e}")
            logger.warning(f"Could not initialize vector store: {e}")
        
        try:
            # Entity Extractor
            if not self.entity_extractor:
                print("   Loading Entity Extractor (spaCy en_core_web_sm)...")
                from backend.core.nlp.entity_extractor import EntityExtractor
                self.entity_extractor = EntityExtractor(model_name="en_core_web_sm", use_scispacy=False)
                print("   ✅ Entity Extractor ready")
        except Exception as e:
            print(f"   ❌ Entity Extractor failed: {e}")
            logger.warning(f"Could not initialize entity extractor: {e}")
        
        print("="*60)
        print("🔧 COMPONENT INITIALIZATION COMPLETE")
        print("="*60 + "\n")

    async def upload_document(self, file: UploadFile) -> Dict[str, Any]:
        """
        Upload a document and process it through the full pipeline:
        1. Save file to storage
        2. Parse document (extract text)
        3. Chunk into smaller pieces
        4. Generate embeddings for each chunk
        5. Store embeddings in vector store
        6. Extract entities (NER)
        7. Update status to ready
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Document response dict
        """
        doc_id = str(uuid.uuid4())
        filename = file.filename or "untitled"
        file_type = file.content_type or "application/octet-stream"
        
        # Read file content
        content = await file.read()
        
        print(f"\n{'='*60}")
        print(f"📄 DOCUMENT UPLOAD: {filename}")
        print(f"{'='*60}")
        print(f"   ID: {doc_id}")
        print(f"   Type: {file_type}")
        print(f"   Size: {len(content)} bytes")
        
        # Save file
        file_path = await self._save_file_content(content, doc_id, filename)
        print(f"   ✅ File saved to: {file_path}")
        
        # Create document record with PROCESSING status
        now = datetime.utcnow()
        doc_info = DocumentInfo(
            id=doc_id,
            title=filename.rsplit(".", 1)[0] if "." in filename else filename,
            filename=filename,
            file_type=file_type,
            status="processing",  # Start as processing
            created_at=now,
            metadata={"file_path": file_path, "size_bytes": len(content)},
        )
        
        # Store in memory
        self._documents[doc_id] = doc_info
        
        print(f"\n🔄 PROCESSING PIPELINE STARTED...")
        
        # Run the processing pipeline
        page_count = None
        entities = []
        chunk_count = 0
        
        try:
            # Step 1: Parse document to extract text
            text_content = ""
            print(f"\n📖 Step 1: Parsing document...")
            
            if file_type == "application/pdf" or filename.lower().endswith(".pdf"):
                if self.pdf_parser:
                    print(f"   Using PDF parser (PyMuPDF)...")
                    pdf_doc = self.pdf_parser.parse(file_path)
                    text_content = pdf_doc.text
                    page_count = len(pdf_doc.pages)
                    print(f"   ✅ Extracted {len(text_content)} chars from {page_count} pages")
                else:
                    print(f"   ⚠️ PDF parser not available!")
            elif file_type.startswith("text/") or filename.lower().endswith((".txt", ".md", ".rst")):
                # Plain text file
                try:
                    text_content = content.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = content.decode("latin-1")
                print(f"   ✅ Read text file: {len(text_content)} chars")
            else:
                print(f"   ⚠️ Unsupported file type: {file_type}, trying as text...")
                try:
                    text_content = content.decode("utf-8")
                    print(f"   ✅ Read as text: {len(text_content)} chars")
                except:
                    text_content = ""
                    print(f"   ❌ Could not decode as text")
            
            # Step 2: Chunk the document
            if text_content and self.chunker:
                print(f"\n✂️ Step 2: Chunking document...")
                chunks = self.chunker.chunk(text_content, document_id=doc_id)
                chunk_count = len(chunks)
                print(f"   ✅ Created {chunk_count} chunks")
                
                # Step 3: Generate embeddings for each chunk
                if self.embeddings_manager and chunks:
                    print(f"\n🧠 Step 3: Generating embeddings...")
                    chunk_texts = [c.text if hasattr(c, 'text') else str(c) for c in chunks]
                    embeddings_array = self.embeddings_manager.embed_documents(chunk_texts)
                    # Convert numpy array to list of lists for vector store
                    embeddings = embeddings_array.tolist() if hasattr(embeddings_array, 'tolist') else list(embeddings_array)
                    print(f"   ✅ Generated {len(embeddings)} embeddings (dim: {len(embeddings[0]) if embeddings else 0})")
                    
                    # Step 4: Store in vector store
                    if self.vector_store and embeddings:
                        print(f"\n💾 Step 4: Storing in vector store (ChromaDB)...")
                        # Prepare lists for vector store
                        texts_to_store = []
                        ids_to_store = []
                        metadatas_to_store = []
                        
                        for i, chunk in enumerate(chunks):
                            chunk_text = chunk.text if hasattr(chunk, 'text') else str(chunk)
                            texts_to_store.append(chunk_text)
                            ids_to_store.append(f"{doc_id}_chunk_{i}")
                            metadatas_to_store.append({
                                "document_id": doc_id,
                                "chunk_index": i,
                                "filename": filename,
                            })
                        
                        self.vector_store.add(
                            texts=texts_to_store,
                            embeddings=embeddings,
                            metadatas=metadatas_to_store,
                            ids=ids_to_store,
                        )
                        print(f"   ✅ Stored {len(texts_to_store)} chunks in vector store")
                else:
                    print(f"   ⚠️ Embeddings manager not available, skipping...")
            else:
                if not text_content:
                    print(f"   ⚠️ No text content to chunk")
                if not self.chunker:
                    print(f"   ⚠️ Chunker not available")
            
            # Step 5: Extract entities
            relations = []
            if text_content and self.entity_extractor:
                print(f"\n🏷️ Step 5: Extracting entities (NER)...")
                # Process first 50k chars for entity extraction (to avoid memory issues)
                sample_text = text_content[:50000] if len(text_content) > 50000 else text_content
                extracted = self.entity_extractor.extract(sample_text, document_id=doc_id)
                # Use correct field names for relation extractor compatibility
                entities = [
                    {
                        "text": e.text,
                        "type": e.entity_type,
                        "entity_type": e.entity_type,  # For relation extractor
                        "start": e.start_char,
                        "end": e.end_char,
                        "start_char": e.start_char,  # For relation extractor co-occurrence
                        "end_char": e.end_char,  # For relation extractor co-occurrence
                    }
                    for e in extracted
                ]
                print(f"   ✅ Extracted {len(entities)} entities")
                if entities[:5]:
                    print(f"   Sample entities: {[e['text'] for e in entities[:5]]}")
                
                # Step 6: Extract relations between entities
                print(f"\n🔗 Step 6: Extracting relations between entities...")
                try:
                    from backend.core.nlp.relation_extractor import RelationExtractor
                    relation_extractor = RelationExtractor(model_name="en_core_web_sm")
                    extracted_relations = relation_extractor.extract(sample_text, entities)
                    relations = [
                        {
                            "source": r.source_text,
                            "source_type": r.source_type,
                            "target": r.target_text,
                            "target_type": r.target_type,
                            "type": r.relation_type,
                            "confidence": r.confidence,
                        }
                        for r in extracted_relations
                    ]
                    print(f"   ✅ Extracted {len(relations)} relations")
                    if relations[:3]:
                        print(f"   Sample relations: {[(r['source'], r['type'], r['target']) for r in relations[:3]]}")
                except Exception as e:
                    print(f"   ⚠️ Relation extraction error: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Step 7: Add entities and relations to knowledge graph
                print(f"\n📊 Step 7: Building knowledge graph...")
                try:
                    from backend.services.graph_service import GraphService
                    graph_service = GraphService()
                    added_entities = graph_service.add_entities_from_extraction(entities, doc_id)
                    added_relations = graph_service.add_relations_from_extraction(relations, doc_id)
                    print(f"   ✅ Added {added_entities} entities and {added_relations} relations to graph")
                except Exception as e:
                    print(f"   ⚠️ Could not add to graph: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                if not self.entity_extractor:
                    print(f"   ⚠️ Entity extractor not available, skipping...")
            
            # Update document status to READY
            doc_info.status = "ready"
            doc_info.metadata["chunk_count"] = chunk_count
            doc_info.metadata["entity_count"] = len(entities)
            doc_info.metadata["relation_count"] = len(relations)
            doc_info.metadata["text_length"] = len(text_content)
            if page_count:
                doc_info.metadata["page_count"] = page_count
            
            print(f"\n{'='*60}")
            print(f"✅ PROCESSING COMPLETE!")
            print(f"{'='*60}")
            print(f"   Document ID: {doc_id}")
            print(f"   Status: ready")
            print(f"   Chunks: {chunk_count}")
            print(f"   Entities: {len(entities)}")
            print(f"   Text length: {len(text_content)} chars")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ PROCESSING ERROR!")
            print(f"{'='*60}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            doc_info.status = "error"
            doc_info.metadata["error"] = str(e)
        
        return {
            "id": doc_id,
            "title": doc_info.title,
            "filename": filename,
            "file_type": file_type,
            "upload_date": now.isoformat(),
            "status": doc_info.status,
            "page_count": page_count,
            "chunk_count": chunk_count,
            "entity_count": len(entities),
            "authors": None,
            "abstract": None,
        }
    
    async def upload_from_url(self, url: str) -> Dict[str, Any]:
        """
        Upload a document from URL.
        
        Args:
            url: URL to fetch document from
            
        Returns:
            Document response dict
        """
        doc_id = str(uuid.uuid4())
        
        # Parse URL to get filename
        from urllib.parse import urlparse
        parsed = urlparse(url)
        filename = parsed.path.split("/")[-1] or "document.html"
        
        now = datetime.utcnow()
        doc_info = DocumentInfo(
            id=doc_id,
            title=filename,
            filename=filename,
            file_type="text/html",
            status="processing",
            created_at=now,
            metadata={"source_url": url},
        )
        
        self._documents[doc_id] = doc_info
        
        logger.info(f"Document from URL queued: {doc_id} - {url}")
        
        return {
            "id": doc_id,
            "title": doc_info.title,
            "filename": filename,
            "file_type": "text/html",
            "upload_date": now.isoformat(),
            "status": "processing",
            "page_count": None,
            "authors": None,
            "abstract": None,
        }
    
    async def _save_file_content(
        self,
        content: bytes,
        doc_id: str,
        filename: str,
    ) -> str:
        """Save file content to storage."""
        from pathlib import Path
        
        storage_path = Path(self.storage_dir)
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create unique filename
        ext = Path(filename).suffix
        file_path = storage_path / f"{doc_id}{ext}"
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(content)
        
        return str(file_path)
    
    async def upload(
        self,
        file: BinaryIO,
        filename: str,
        file_type: str,
        user_id: Optional[str] = None,
    ) -> DocumentInfo:
        """
        Upload and process a document.
        
        Args:
            file: File-like object
            filename: Original filename
            file_type: MIME type
            user_id: Optional user ID
            
        Returns:
            DocumentInfo with document details
        """
        doc_id = str(uuid.uuid4())
        
        # Save file
        file_path = await self._save_file(file, doc_id, filename)
        
        # Create document record
        doc_info = DocumentInfo(
            id=doc_id,
            title=filename,
            filename=filename,
            file_type=file_type,
            status="pending",
            created_at=datetime.utcnow(),
            metadata={"file_path": file_path},
        )
        
        # Save to database
        if self.db:
            await self._save_to_db(doc_info, user_id)
        
        # Queue processing
        await self.process_document(doc_id)
        
        return doc_info
    
    async def _save_file(
        self,
        file: BinaryIO,
        doc_id: str,
        filename: str,
    ) -> str:
        """Save uploaded file to storage."""
        import os
        from pathlib import Path
        
        storage_path = Path(self.storage_dir)
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create unique filename
        ext = Path(filename).suffix
        file_path = storage_path / f"{doc_id}{ext}"
        
        # Write file
        content = file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return str(file_path)
    
    async def _save_to_db(self, doc_info: DocumentInfo, user_id: Optional[str]) -> None:
        """Save document info to database."""
        # Implementation depends on database layer
        pass
    
    async def process_document(self, doc_id: str) -> Dict:
        """
        Process a document through the pipeline.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Processing result
        """
        logger.info(f"Processing document: {doc_id}")
        
        try:
            # Get document
            doc = await self.get(doc_id)
            if not doc:
                raise ValueError(f"Document not found: {doc_id}")
            
            file_path = doc.metadata.get("file_path")
            
            # Parse document
            if doc.file_type == "application/pdf":
                parsed = self.pdf_parser.parse(file_path) if self.pdf_parser else None
            else:
                # Read as text
                with open(file_path, "r", encoding="utf-8") as f:
                    parsed = type("Parsed", (), {"text": f.read(), "metadata": {}})()
            
            if not parsed:
                raise ValueError("Failed to parse document")
            
            # Extract metadata
            if self.metadata_extractor:
                metadata = self.metadata_extractor.extract(
                    parsed.text,
                    getattr(parsed, "metadata", None),
                )
                doc.metadata["extracted"] = {
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "abstract": metadata.abstract,
                }
            
            # Chunk document
            if self.chunker:
                chunks = self.chunker.chunk(parsed.text, doc_id)
                doc.metadata["chunk_count"] = len(chunks)
                
                # Generate embeddings
                if self.embeddings_manager and self.vector_store:
                    texts = [chunk.text for chunk in chunks]
                    embeddings = self.embeddings_manager.embed_documents(texts)
                    
                    # Store in vector store
                    chunk_ids = self.vector_store.add(
                        texts=texts,
                        embeddings=embeddings.tolist(),
                        metadatas=[{"document_id": doc_id, "chunk_index": i} for i in range(len(chunks))],
                    )
                    doc.metadata["chunk_ids"] = chunk_ids
            
            # Update status
            doc.status = "completed"
            
            return {
                "status": "success",
                "document_id": doc_id,
                "chunks_created": doc.metadata.get("chunk_count", 0),
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                "status": "failed",
                "document_id": doc_id,
                "error": str(e),
            }
    
    async def get(self, doc_id: str) -> Optional[DocumentInfo]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            DocumentInfo or None
        """
        # Check in-memory store first, then database
        doc = self._documents.get(doc_id)
        if doc:
            return doc
        
        # TODO: implement PostgreSQL lookup when DB is wired
        return None
    
    async def list(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[DocumentInfo]:
        """
        List documents.
        
        Args:
            user_id: Optional user filter
            skip: Number to skip
            limit: Maximum to return
            status: Optional status filter
            
        Returns:
            List of documents
        """
        # Database query would go here
        return []
    
    async def delete(self, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted
        """
        try:
            # Delete from vector store
            if self.vector_store:
                # Get chunk IDs and delete
                pass
            
            # Delete file
            doc = await self.get(doc_id)
            if doc:
                file_path = doc.metadata.get("file_path")
                if file_path:
                    import os
                    if os.path.exists(file_path):
                        os.remove(file_path)
            
            # Delete from database
            if self.db:
                pass
            
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List documents with pagination (for API route).
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            status: Optional status filter
            
        Returns:
            Paginated document list
        """
        # Get from in-memory store
        docs = list(self._documents.values())
        
        # Filter by status if provided
        if status:
            docs = [d for d in docs if d.status == status]
        
        # Sort by created_at desc
        docs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Paginate
        total = len(docs)
        start = (page - 1) * page_size
        end = start + page_size
        page_docs = docs[start:end]
        
        return {
            "documents": [
                {
                    "id": d.id,
                    "title": d.title,
                    "filename": d.filename,
                    "file_type": d.file_type,
                    "upload_date": d.created_at.isoformat(),
                    "status": d.status,
                    "page_count": d.metadata.get("page_count"),
                    "authors": d.metadata.get("extracted", {}).get("authors"),
                    "abstract": d.metadata.get("extracted", {}).get("abstract"),
                }
                for d in page_docs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID (for API route).
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document dict or None
        """
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        
        # Try to get text content
        text_content = doc.metadata.get("text_content", "")
        if not text_content and doc.metadata.get("file_path"):
            try:
                # Try to read from processed chunks
                chunks = doc.metadata.get("chunks", [])
                if chunks:
                    text_content = " ".join(chunks)
            except Exception:
                pass
        
        return {
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "upload_date": doc.created_at.isoformat(),
            "status": doc.status,
            "page_count": doc.metadata.get("page_count"),
            "authors": doc.metadata.get("extracted", {}).get("authors"),
            "abstract": doc.metadata.get("extracted", {}).get("abstract"),
            "text": text_content,
            "content": text_content,  # Alias for compatibility
        }
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document (for API route).
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted
        """
        if doc_id not in self._documents:
            return False
        
        doc = self._documents[doc_id]
        
        # Delete file
        file_path = doc.metadata.get("file_path")
        if file_path:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Remove from store
        del self._documents[doc_id]
        
        logger.info(f"Document deleted: {doc_id}")
        return True
    
    async def reprocess_document(self, doc_id: str) -> bool:
        """
        Reprocess a document (for API route).
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if reprocessing started
        """
        if doc_id not in self._documents:
            return False
        
        doc = self._documents[doc_id]
        doc.status = "processing"
        
        # TODO: Queue background processing
        # from backend.tasks.document_tasks import process_document_task
        # process_document_task.delay(doc_id)
        
        logger.info(f"Document reprocessing queued: {doc_id}")
        return True
    
    async def reprocess(self, doc_id: str) -> Dict:
        """
        Reprocess a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Processing result
        """
        # Clear existing chunks/embeddings
        # Then process again
        return await self.process_document(doc_id)
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        user_id: Optional[str] = None,
    ) -> List[DocumentInfo]:
        """
        Search documents.
        
        Args:
            query: Search query
            limit: Maximum results
            user_id: Optional user filter
            
        Returns:
            Matching documents
        """
        # Would use vector store or full-text search
        return []
