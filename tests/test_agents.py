"""
Tests for agent functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.controller import ControllerAgent
from src.agents.faq_agent import FAQAgent
from src.agents.advisor_agent import AdvisorAgent


@pytest.mark.asyncio
class TestControllerAgent:
    """Test cases for Controller Agent."""
    
    async def test_initialization(self):
        """Test controller agent initialization."""
        with patch('src.agents.controller.ChatOpenAI'), \
             patch('src.agents.controller.CallbackHandler'), \
             patch('src.agents.faq_agent.FAQAgent.initialize', new_callable=AsyncMock), \
             patch('src.agents.advisor_agent.AdvisorAgent.initialize', new_callable=AsyncMock):
            
            controller = ControllerAgent()
            await controller.initialize()
            
            assert controller.llm is not None
            assert controller.faq_agent is not None
            assert controller.advisor_agent is not None
            assert controller.workflow is not None
    
    async def test_process_message(self):
        """Test message processing."""
        with patch('src.agents.controller.ChatOpenAI'), \
             patch('src.agents.controller.CallbackHandler'), \
             patch('src.agents.faq_agent.FAQAgent.initialize', new_callable=AsyncMock), \
             patch('src.agents.advisor_agent.AdvisorAgent.initialize', new_callable=AsyncMock), \
             patch('src.guardrails.validators.GuardrailValidator.validate_input', 
                   new_callable=AsyncMock, return_value={"valid": True}):
            
            controller = ControllerAgent()
            await controller.initialize()
            
            # Mock workflow execution
            controller.workflow = MagicMock()
            controller.workflow.ainvoke = AsyncMock(return_value={
                "final_response": "Test response",
                "tools_used": [],
                "agent_path": ["controller"]
            })
            
            result = await controller.process_message(
                message="What are the trading fees?",
                session_id="test-session",
                user_id="test-user"
            )
            
            assert "response" in result
            assert result["response"] == "Test response"
            assert "metadata" in result
    
    async def test_guardrail_blocking(self):
        """Test that guardrails block invalid input."""
        with patch('src.agents.controller.ChatOpenAI'), \
             patch('src.agents.controller.CallbackHandler'), \
             patch('src.agents.faq_agent.FAQAgent.initialize', new_callable=AsyncMock), \
             patch('src.agents.advisor_agent.AdvisorAgent.initialize', new_callable=AsyncMock), \
             patch('src.guardrails.validators.GuardrailValidator.validate_input', 
                   new_callable=AsyncMock, 
                   return_value={"valid": False, "reason": "Blocked by guardrails"}):
            
            controller = ControllerAgent()
            await controller.initialize()
            
            result = await controller.process_message(
                message="Malicious input",
                session_id="test-session",
                user_id="test-user"
            )
            
            assert "Blocked by guardrails" in result["response"]
            assert result["metadata"]["blocked_by_guardrails"] is True


@pytest.mark.asyncio
class TestFAQAgent:
    """Test cases for FAQ Agent."""
    
    async def test_initialization(self):
        """Test FAQ agent initialization."""
        with patch('src.agents.faq_agent.ChatOpenAI'), \
             patch('src.rag.retriever.RAGRetriever.initialize', new_callable=AsyncMock):
            
            faq_agent = FAQAgent()
            await faq_agent.initialize()
            
            assert faq_agent.llm is not None
            assert faq_agent.retriever is not None
    
    async def test_process_with_results(self):
        """Test FAQ processing with retrieved documents."""
        with patch('src.agents.faq_agent.ChatOpenAI') as mock_llm, \
             patch('src.rag.retriever.RAGRetriever.initialize', new_callable=AsyncMock), \
             patch('src.rag.retriever.RAGRetriever.retrieve', new_callable=AsyncMock) as mock_retrieve:
            
            # Mock retrieved documents
            mock_retrieve.return_value = [
                {
                    "content": "Trading fees are 0.1% per transaction.",
                    "score": 0.95,
                    "source": "faq.txt"
                }
            ]
            
            # Mock LLM response
            mock_llm_instance = AsyncMock()
            mock_llm_instance.ainvoke = AsyncMock()
            mock_llm_instance.ainvoke.return_value = MagicMock(
                content="The trading fee is 0.1% per transaction."
            )
            mock_llm.return_value = mock_llm_instance
            
            faq_agent = FAQAgent()
            await faq_agent.initialize()
            faq_agent.llm = mock_llm_instance
            
            result = await faq_agent.process("What are the fees?", "test-session")
            
            assert "response" in result
            assert result["confidence"] > 0.9
            assert "rag_retriever" in result["tools_used"]
    
    async def test_process_no_results(self):
        """Test FAQ processing with no retrieved documents."""
        with patch('src.agents.faq_agent.ChatOpenAI'), \
             patch('src.rag.retriever.RAGRetriever.initialize', new_callable=AsyncMock), \
             patch('src.rag.retriever.RAGRetriever.retrieve', 
                   new_callable=AsyncMock, return_value=[]):
            
            faq_agent = FAQAgent()
            await faq_agent.initialize()
            
            result = await faq_agent.process("Unknown question", "test-session")
            
            assert "don't have information" in result["response"]
            assert result["confidence"] == 0.0


@pytest.mark.asyncio
class TestAdvisorAgent:
    """Test cases for Advisor Agent."""
    
    async def test_initialization(self):
        """Test advisor agent initialization."""
        with patch('src.agents.advisor_agent.ChatOpenAI'), \
             patch('src.tools.stock_tools.get_stock_tools', 
                   new_callable=AsyncMock, return_value=[]), \
             patch('src.tools.budget_tools.get_budget_tools', 
                   new_callable=AsyncMock, return_value=[]), \
             patch('src.tools.mcp_tools.get_mcp_tools', 
                   new_callable=AsyncMock, return_value=[]):
            
            advisor = AdvisorAgent()
            await advisor.initialize()
            
            assert advisor.llm is not None
            assert advisor.agent_executor is not None
    
    async def test_process_trading_query(self):
        """Test advisor processing trading query."""
        with patch('src.agents.advisor_agent.ChatOpenAI'), \
             patch('src.tools.stock_tools.get_stock_tools', 
                   new_callable=AsyncMock, return_value=[]), \
             patch('src.tools.budget_tools.get_budget_tools', 
                   new_callable=AsyncMock, return_value=[]), \
             patch('src.tools.mcp_tools.get_mcp_tools', 
                   new_callable=AsyncMock, return_value=[]):
            
            advisor = AdvisorAgent()
            await advisor.initialize()
            
            # Mock executor response
            advisor.agent_executor = MagicMock()
            advisor.agent_executor.ainvoke = AsyncMock(return_value={
                "output": "AAPL is currently trading at $175.50",
                "intermediate_steps": []
            })
            
            result = await advisor.process(
                "What's the price of AAPL?",
                "test-session",
                {}
            )
            
            assert "response" in result
            assert "$175.50" in result["response"] or "AAPL" in result["response"]


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('src.config.settings.settings') as mock:
        mock.openai_api_key = "test-key"
        mock.llm_model = "gpt-4"
        mock.llm_temperature = 0.7
        mock.max_agent_iterations = 10
        mock.top_k_results = 5
        mock.mcp_enabled = False
        yield mock