"""
FAQ Agent - Handles factual questions using RAG retrieval.
"""

import time
from typing import Dict, Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config.settings import settings
from src.rag.retriever import RAGRetriever
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class FAQAgent:
    """FAQ agent that uses RAG for answering factual questions."""
    
    def __init__(self):
        self.llm: Optional[ChatOpenAI] = None
        self.retriever: Optional[RAGRetriever] = None
    
    async def initialize(self) -> None:
        """Initialize FAQ agent components."""
        try:
            logger.info("Initializing FAQ agent")
            
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=0.3,  # Lower temperature for factual responses
                max_tokens=settings.llm_max_tokens,
                api_key=settings.openai_api_key
            )
            
            self.retriever = RAGRetriever()
            await self.retriever.initialize()
            
            logger.info("FAQ agent initialized")
            
        except Exception as e:
            logger.error("Failed to initialize FAQ agent", error=str(e), exc_info=True)
            raise
    
    async def process(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Process FAQ query using RAG retrieval.
        
        Args:
            query: User question
            session_id: Session identifier
            
        Returns:
            Dict with response and metadata
        """
        start_time = time.time()
        
        try:
            logger.info("Processing FAQ query", session_id=session_id)
            
            # Retrieve relevant documents
            retrieved_docs = await self.retriever.retrieve(query, top_k=settings.top_k_results)
            
            if not retrieved_docs:
                return {
                    "response": "I don't have information about that in my knowledge base. Could you rephrase or ask something else?",
                    "tools_used": ["rag_retriever"],
                    "confidence": 0.0
                }
            
            # Build context from retrieved documents
            context = "\n\n".join([
                f"Document {i+1}:\n{doc['content']}"
                for i, doc in enumerate(retrieved_docs)
            ])
            
            # Generate response
            prompt = f"""You are a helpful assistant for a financial trading platform. Use the following context to answer the user's question accurately and concisely.

Context:
{context}

User Question: {query}

Instructions:
- Answer based only on the provided context
- Be concise and accurate
- If the context doesn't contain the answer, say so
- Use a professional but friendly tone

Answer:"""
            
            messages = [SystemMessage(content=prompt)]
            response = await self.llm.ainvoke(messages)
            
            latency = (time.time() - start_time) * 1000
            
            logger.info(
                "FAQ query processed",
                session_id=session_id,
                latency_ms=latency,
                docs_retrieved=len(retrieved_docs)
            )
            
            return {
                "response": response.content,
                "tools_used": ["rag_retriever"],
                "confidence": retrieved_docs[0].get("score", 0.0) if retrieved_docs else 0.0,
                "sources": [doc.get("source", "Unknown") for doc in retrieved_docs[:3]],
                "latency_ms": latency
            }
            
        except Exception as e:
            logger.error("FAQ processing failed", error=str(e), session_id=session_id, exc_info=True)
            return {
                "response": "I encountered an error retrieving information. Please try again.",
                "tools_used": [],
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up FAQ agent")
        if self.retriever:
            await self.retriever.cleanup()