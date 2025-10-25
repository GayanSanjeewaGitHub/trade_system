"""
RAG Retriever - Handles semantic search and document retrieval.
"""

from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class RAGRetriever:
    """RAG retriever using Pinecone vector database."""
    
    def __init__(self):
        self.pc: Optional[Pinecone] = None
        self.index = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.vector_store: Optional[PineconeVectorStore] = None
    
    async def initialize(self) -> None:
        """Initialize Pinecone connection and embeddings."""
        try:
            logger.info("Initializing RAG retriever")
            
            # Initialize Pinecone
            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            
            # Create or get index
            index_name = settings.pinecone_index_name
            
            if index_name not in [idx.name for idx in self.pc.list_indexes()]:
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
            
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=settings.openai_api_key
            )
            
            # Initialize vector store
            self.vector_store = PineconeVectorStore(
                index=self.index,
                embedding=self.embeddings,
                text_key="content"
            )
            
            logger.info("RAG retriever initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize RAG retriever", error=str(e), exc_info=True)
            raise
    
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
            logger.info("Retrieving documents", query_length=len(query), top_k=top_k)
            
            # Search in vector store
            results = await self.vector_store.asimilarity_search_with_score(
                query=query,
                k=top_k,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                if score >= settings.similarity_threshold:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score),
                        "source": doc.metadata.get("source", "Unknown")
                    })
            
            logger.info(
                "Documents retrieved",
                count=len(formatted_results),
                avg_score=sum(r["score"] for r in formatted_results) / len(formatted_results) if formatted_results else 0
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
            logger.info("Adding documents to vector store", count=len(documents))
            
            texts = [doc["content"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # Add to vector store
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
            stats = self.index.describe_index_stats()
            
            return {
                "total_vectors": stats.get("total_vector_count", 0),
                "dimension": stats.get("dimension", 0),
                "index_fullness": stats.get("index_fullness", 0.0)
            }
            
        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {}
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up RAG retriever")
        # Pinecone connections are automatically managed