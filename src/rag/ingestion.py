"""
Document ingestion pipeline for RAG system.
Handles PDF processing, chunking, and vector storage.
"""

import asyncio
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import pypdf

from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.config.settings import settings
from src.rag.retriever import RAGRetriever
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class DocumentIngestion:
    """Document ingestion pipeline."""
    
    def __init__(self):
        self.retriever: Optional[RAGRetriever] = None
        self.text_splitter: Optional[RecursiveCharacterTextSplitter] = None
    
    async def initialize(self) -> None:
        """Initialize ingestion components."""
        try:
            logger.info("Initializing document ingestion")
            
            # Initialize retriever
            self.retriever = RAGRetriever()
            await self.retriever.initialize()
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            # Load default documents
            await self._load_default_documents()
            
            logger.info("Document ingestion initialized")
            
        except Exception as e:
            logger.error("Failed to initialize ingestion", error=str(e), exc_info=True)
            raise
    
    async def ingest_document(
        self,
        content: bytes,
        filename: str,
        document_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Ingest a document into the vector store.
        
        Args:
            content: Document content as bytes
            filename: Original filename
            document_type: Type of document
            
        Returns:
            Ingestion result
        """
        try:
            logger.info("Ingesting document", filename=filename, type=document_type)
            
            # Ensure retriever is initialized
            if not self.retriever or not self.retriever.vector_store:
                logger.warning("Retriever not initialized, reinitializing...")
                await self.initialize()
                
            if not self.retriever or not self.retriever.vector_store:
                raise Exception("Failed to initialize retriever")
            
            # Extract text based on file type
            if filename.endswith(".pdf"):
                text = await self._extract_pdf_text(content)
            elif filename.endswith(".txt") or filename.endswith(".md"):
                text = content.decode("utf-8")
            else:
                raise ValueError(f"Unsupported file type: {filename}")
            
            if not text.strip():
                raise ValueError("Extracted text is empty")
            
            # Split into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create document objects
            documents = []
            doc_id = self._generate_doc_id(filename, text)
            
            for i, chunk in enumerate(chunks):
                documents.append({
                    "content": chunk,
                    "metadata": {
                        "source": filename,
                        "document_id": doc_id,
                        "document_type": document_type,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })
            
            # Add to vector store with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await self.retriever.add_documents(documents)
                    
                    if result["success"]:
                        logger.info(
                            "Document ingested successfully",
                            filename=filename,
                            chunks=len(chunks)
                        )
                        
                        return {
                            "success": True,
                            "filename": filename,
                            "chunks_created": len(chunks),
                            "document_id": doc_id
                        }
                    else:
                        error_msg = result.get("error", "Unknown error")
                        if "session" in error_msg.lower() and attempt < max_retries - 1:
                            logger.warning(f"Session error, refreshing embeddings client (attempt {attempt + 1}/{max_retries})")
                            await self.retriever.refresh_embeddings()
                            await asyncio.sleep(1)
                            continue
                        raise Exception(error_msg)
                        
                except Exception as e:
                    if "session" in str(e).lower() and attempt < max_retries - 1:
                        logger.warning(f"Session error, refreshing embeddings client (attempt {attempt + 1}/{max_retries})")
                        await self.retriever.refresh_embeddings()
                        await asyncio.sleep(1)  # Brief delay before retry
                        continue
                    raise
            
            raise Exception("Failed to add documents after retries")
            
        except Exception as e:
            logger.error("Document ingestion failed", filename=filename, error=str(e), exc_info=True)
            raise
    
    async def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            import io
            
            pdf_file = io.BytesIO(content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            text_parts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error("PDF text extraction failed", error=str(e))
            raise ValueError(f"Failed to extract PDF text: {str(e)}")
    
    def _generate_doc_id(self, filename: str, content: str) -> str:
        """Generate unique document ID."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"doc_{filename}_{content_hash}"
    
    async def _load_default_documents(self) -> None:
        """Load default documents from data directory."""
        try:
            # Try multiple possible data directory locations
            possible_dirs = [
                Path("src/data"),           # Development environment
                Path("/app/src/data"),      # Docker environment
                Path("data/documents"),     # Alternative location
                Path("data")                # Fallback
            ]
            
            data_dir = None
            for dir_path in possible_dirs:
                if dir_path.exists():
                    data_dir = dir_path
                    logger.info(f"Found data directory at: {dir_path}")
                    break
            
            if not data_dir:
                logger.warning("Data directory not found in any expected location, skipping default documents")
                return
            
            # Load .txt files from the data directory
            loaded_count = 0
            for file_path in data_dir.glob("*.txt"):
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    
                    # Determine document type from filename
                    filename = file_path.name.lower()
                    if "faq" in filename:
                        doc_type = "faq"
                    elif "polic" in filename:
                        doc_type = "policy"
                    elif "product" in filename:
                        doc_type = "product_info"
                    else:
                        doc_type = "general"
                    
                    await self.ingest_document(
                        content=content,
                        filename=file_path.name,
                        document_type=doc_type
                    )
                    
                    loaded_count += 1
                    logger.info(f"Loaded default document: {file_path.name} as type: {doc_type}")
                    
                except Exception as e:
                    logger.error("Failed to load default document", file=file_path.name, error=str(e))
            
            logger.info(f"Default documents loaded successfully (count: {loaded_count})")
            
        except Exception as e:
            logger.error("Failed to load default documents", error=str(e))
    
    async def ingest_directory(self, directory: Path, document_type: str = "general") -> Dict[str, Any]:
        """Ingest all documents from a directory."""
        try:
            results = {
                "success": 0,
                "failed": 0,
                "total": 0
            }
            
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.suffix in settings.allowed_file_types:
                    results["total"] += 1
                    
                    try:
                        with open(file_path, "rb") as f:
                            content = f.read()
                        
                        await self.ingest_document(
                            content=content,
                            filename=file_path.name,
                            document_type=document_type
                        )
                        
                        results["success"] += 1
                        
                    except Exception as e:
                        logger.error("Failed to ingest file", file=file_path.name, error=str(e))
                        results["failed"] += 1
            
            return results
            
        except Exception as e:
            logger.error("Directory ingestion failed", error=str(e))
            raise
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up document ingestion")
        if self.retriever:
            await self.retriever.cleanup()