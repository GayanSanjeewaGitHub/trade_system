"""
RAG Retriever - Handles semantic search and document retrieval.
"""

import asyncio
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores import FAISS

from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class RAGRetriever:
    """RAG retriever using Pinecone vector database with FAISS fallback."""
    
    def __init__(self):
        self.pc: Optional[Pinecone] = None
        self.index = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.vector_store: Optional[PineconeVectorStore] = None
        self.use_faiss_fallback: bool = False
        self._embeddings_initialized: bool = False
    
    def _create_embeddings(self) -> OpenAIEmbeddings:
        """Create a new embeddings instance with optimal settings."""
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            max_retries=5,
            request_timeout=180,
            show_progress_bar=False,
            chunk_size=200,
            tiktoken_enabled=True,
            tiktoken_model_name=None,
        )
    
    async def initialize(self) -> None:
        """Initialize Pinecone connection and embeddings with FAISS fallback."""
        try:
            logger.info("Initializing RAG retriever")
            
            # Check if we have valid API keys
            if not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key":
                logger.warning("OpenAI API key not configured, RAG retriever will be disabled")
                return
            
            # Initialize embeddings using helper method
            self.embeddings = self._create_embeddings()
            self._embeddings_initialized = True
            
            # Try to initialize Pinecone
            if not settings.pinecone_api_key or settings.pinecone_api_key == "your-pinecone-api-key" or settings.pinecone_api_key == "YOUR_ACTUAL_PINECONE_API_KEY_HERE":
                logger.warning("Pinecone API key not configured, using FAISS in-memory fallback")
                self.use_faiss_fallback = True
                await self._initialize_faiss()
                return
            
            try:
                # Initialize Pinecone
                self.pc = Pinecone(api_key=settings.pinecone_api_key)
                
                # Create or get index
                index_name = settings.pinecone_index_name
                
                existing_indexes = [idx.name for idx in self.pc.list_indexes()]
                if index_name not in existing_indexes:
                    logger.info("Creating new Pinecone index", index_name=index_name)
                    
                    self.pc.create_index(
                        name=index_name,
                        dimension=settings.pinecone_dimension,
                        metric=settings.pinecone_metric,
                        spec=ServerlessSpec(
                            cloud=settings.pinecone_cloud,
                            region=settings.pinecone_region
                        )
                    )
                
                self.index = self.pc.Index(index_name)
                
                # Initialize vector store
                self.vector_store = PineconeVectorStore(
                    index=self.index,
                    embedding=self.embeddings,
                    text_key="content"
                )
                
                logger.info("RAG retriever initialized successfully with Pinecone")
                
            except Exception as pinecone_error:
                logger.warning(
                    "Failed to connect to Pinecone, falling back to FAISS in-memory store",
                    error=str(pinecone_error)
                )
                self.use_faiss_fallback = True
                await self._initialize_faiss()
            
        except Exception as e:
            logger.error("Failed to initialize retriever", error=str(e), exc_info=True)
            raise
    
    async def _initialize_faiss(self) -> None:
        """Initialize FAISS in-memory vector store as fallback."""
        try:
            logger.info("Initializing FAISS in-memory vector store")
            
            # Create an empty FAISS store (run in thread pool to avoid blocking)
            # We'll initialize it with a dummy document first
            dummy_texts = ["Initialization document"]
            dummy_metadatas = [{"type": "system", "purpose": "initialization"}]
            
            self.vector_store = await asyncio.to_thread(
                FAISS.from_texts,
                texts=dummy_texts,
                embedding=self.embeddings,
                metadatas=dummy_metadatas
            )
            
            logger.info("FAISS vector store initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize FAISS", error=str(e), exc_info=True)
            raise
            
        except Exception as e:
            logger.warning("Failed to initialize RAG retriever, continuing without it", error=str(e))
            # Don't raise the exception, just log and continue
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of relevant documents with scores
        """
        try:
            if not self.vector_store:
                logger.warning("Vector store not initialized, returning empty results")
                return []
                
            logger.info("Retrieving documents", query_length=len(query), top_k=top_k)
            
            # Search in vector store (use sync method for FAISS, async for Pinecone)
            if self.use_faiss_fallback:
                # Run synchronous FAISS operation in thread pool to avoid blocking
                results = await asyncio.to_thread(
                    self.vector_store.similarity_search_with_score,
                    query=query,
                    k=top_k,
                    filter=filter_dict
                )
            else:
                results = await self.vector_store.asimilarity_search_with_score(
                    query=query,
                    k=top_k,
                    filter=filter_dict
                )
            
            # Format results
            formatted_results = []
            all_scores = []
            for doc, score in results:
                all_scores.append(float(score))
                # Include all results, let the agent decide relevance
                # Only filter out extremely low scores (< 0.3 for cosine similarity)
                if score >= 0.3:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score),
                        "source": doc.metadata.get("source", "Unknown")
                    })
            
            logger.info(
                "Documents retrieved",
                count=len(formatted_results),
                total_found=len(results),
                avg_score=sum(r["score"] for r in formatted_results) / len(formatted_results) if formatted_results else 0,
                all_scores=all_scores[:5]  # Log first 5 scores for debugging
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error("Document retrieval failed", error=str(e), exc_info=True)
            return []
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add documents to vector store.
        
        Args:
            documents: List of documents with content and metadata
            
        Returns:
            Result dict with success status
        """
        try:
            if not self.vector_store:
                logger.warning("Vector store not initialized, cannot add documents")
                return {
                    "success": False,
                    "error": "Vector store not initialized"
                }
                
            logger.info("Adding documents to vector store", count=len(documents))
            
            texts = [doc["content"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # Add to vector store (use sync method for FAISS, async for Pinecone)
            if self.use_faiss_fallback:
                # Run synchronous FAISS operation in thread pool to avoid blocking
                await asyncio.to_thread(
                    self.vector_store.add_texts,
                    texts=texts,
                    metadatas=metadatas
                )
                ids = [f"faiss_{i}" for i in range(len(texts))]
            else:
                ids = await self.vector_store.aadd_texts(
                    texts=texts,
                    metadatas=metadatas
                )
            
            logger.info("Documents added successfully", ids_count=len(ids))
            
            return {
                "success": True,
                "ids": ids,
                "count": len(ids)
            }
            
        except Exception as e:
            logger.error("Failed to add documents", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_documents(self, ids: List[str]) -> Dict[str, Any]:
        """Delete documents by IDs."""
        try:
            if self.use_faiss_fallback:
                logger.warning("FAISS fallback mode: delete operation not supported")
                return {
                    "success": False,
                    "error": "Delete operation not supported in FAISS fallback mode"
                }
            
            if not self.index:
                logger.warning("Pinecone index not initialized, cannot delete documents")
                return {
                    "success": False,
                    "error": "Pinecone index not initialized"
                }
                
            logger.info("Deleting documents", count=len(ids))
            
            self.index.delete(ids=ids)
            
            logger.info("Documents deleted successfully")
            
            return {"success": True, "deleted_count": len(ids)}
            
        except Exception as e:
            logger.error("Failed to delete documents", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            if self.use_faiss_fallback:
                if self.vector_store:
                    return {
                        "mode": "FAISS (in-memory)",
                        "total_vectors": self.vector_store.index.ntotal,
                        "dimension": 1536,
                        "index_fullness": 0.0
                    }
                return {"mode": "FAISS", "status": "not initialized"}
            
            if not self.index:
                logger.warning("Pinecone index not initialized, cannot get stats")
                return {}
                
            stats = self.index.describe_index_stats()
            
            return {
                "mode": "Pinecone",
                "total_vectors": stats.get("total_vector_count", 0),
                "dimension": stats.get("dimension", 0),
                "index_fullness": stats.get("index_fullness", 0.0)
            }
            
        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {}
    
    async def refresh_embeddings(self) -> None:
        """Refresh the embeddings client to resolve session issues."""
        try:
            logger.info("Refreshing embeddings client")
            old_embeddings = self.embeddings
            
            # Create new embeddings instance
            self.embeddings = self._create_embeddings()
            
            # Update vector store with new embeddings if using Pinecone
            if not self.use_faiss_fallback and self.index:
                self.vector_store = PineconeVectorStore(
                    index=self.index,
                    embedding=self.embeddings,
                    text_key="content"
                )
                logger.info("Vector store updated with new embeddings client")
            
            # Clean up old embeddings (if it has a close method)
            if old_embeddings and hasattr(old_embeddings, 'client') and hasattr(old_embeddings.client, 'close'):
                try:
                    old_embeddings.client.close()
                except:
                    pass
                    
        except Exception as e:
            logger.error("Failed to refresh embeddings", error=str(e))
            raise
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up RAG retriever")
        
        # Close embeddings client if it exists
        if self.embeddings and hasattr(self.embeddings, 'client'):
            try:
                if hasattr(self.embeddings.client, 'close'):
                    self.embeddings.client.close()
            except:
                pass
        
        # Pinecone connections are automatically managed