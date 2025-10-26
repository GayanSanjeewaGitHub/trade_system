"""
Controller Agent - Main orchestrator that delegates tasks to specialized sub-agents.
Implements LangGraph state machine for complex multi-agent workflows.
"""

import time
from typing import Dict, List, Any, Optional, Annotated
from operator import add

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
 
from langgraph.prebuilt import create_react_agent
 
from langgraph.prebuilt import ToolNode
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse, get_client

from src.config.settings import settings
from src.agents.faq_agent import FAQAgent
from src.agents.advisor_agent import AdvisorAgent
from src.guardrails.validators import GuardrailValidator
from src.monitoring.logger import get_logger
from src.utils.helpers import generate_session_id

logger = get_logger(__name__)


class AgentState(Dict):
    """State object for LangGraph workflow."""
    messages: Annotated[List, add]
    current_agent: str
    user_input: str
    session_id: str
    user_id: str
    context: Dict[str, Any]
    agent_outputs: Dict[str, Any]
    tools_used: List[str]
    agent_path: List[str]
    should_continue: bool
    final_response: Optional[str]
    error: Optional[str]


class ControllerAgent:
    """
    Main controller agent that orchestrates sub-agents and tools.
    Uses LangGraph for state management and workflow orchestration.
    """
    
    def __init__(self):
        self.llm: Optional[ChatOpenAI] = None
        self.faq_agent: Optional[FAQAgent] = None
        self.advisor_agent: Optional[AdvisorAgent] = None
        self.guardrails: Optional[GuardrailValidator] = None
        self.workflow: Optional[StateGraph] = None
        self.langfuse_handler: Optional[CallbackHandler] = None
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.metrics: Dict[str, Any] = {
            "total_conversations": 0,
            "total_messages": 0,
            "tool_usage": {},
            "agent_usage": {},
            "errors": 0,
            "total_latency": 0.0
        }
    
    async def initialize(self) -> None:
        """Initialize controller agent and all sub-agents."""
        try:
            logger.info("Initializing controller agent")
            
            # Initialize LLM
            if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key":
                self.llm = ChatOpenAI(
                    model=settings.llm_model,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                    timeout=settings.llm_timeout,
                    api_key=settings.openai_api_key
                )
            else:
                logger.warning("OpenAI API key not configured, controller will have limited functionality")
                self.llm = None
            
            # Initialize Langfuse handler
            if (settings.langfuse_enabled and 
                settings.langfuse_public_key != "your-langfuse-public-key" and
                settings.langfuse_secret_key != "your-langfuse-secret-key"):
                try:
                    # Initialize Langfuse client first
                    Langfuse(
                        public_key=settings.langfuse_public_key,
                        secret_key=settings.langfuse_secret_key,
                        host=settings.langfuse_host
                    )
                    # Create handler without parameters (uses environment variables or client config)
                    self.langfuse_handler = CallbackHandler()
                    logger.info("Langfuse handler initialized")
                except Exception as langfuse_error:
                    logger.warning("Failed to initialize Langfuse handler", error=str(langfuse_error))
                    self.langfuse_handler = None
            else:
                logger.info("Langfuse not configured or disabled")
                self.langfuse_handler = None
            
            # Initialize sub-agents
            self.faq_agent = FAQAgent()
            await self.faq_agent.initialize()
            
            self.advisor_agent = AdvisorAgent()
            await self.advisor_agent.initialize()
            
            # Initialize guardrails
            self.guardrails = GuardrailValidator()
            
            # Build workflow
            self._build_workflow()
            
            logger.info("Controller agent initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize controller agent", error=str(e), exc_info=True)
            raise
    
    def _build_workflow(self) -> None:
        """Build LangGraph workflow for agent orchestration."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classify", self._classify_intent)
        workflow.add_node("faq", self._route_to_faq)
        workflow.add_node("advisor", self._route_to_advisor)
        workflow.add_node("finalize", self._finalize_response)
        
        # Add edges
        workflow.set_entry_point("classify")
        
        workflow.add_conditional_edges(
            "classify",
            self._should_route_to_agent,
            {
                "faq": "faq",
                "advisor": "advisor",
                "finalize": "finalize"
            }
        )
        
        workflow.add_edge("faq", "finalize")
        workflow.add_edge("advisor", "finalize")
        workflow.add_edge("finalize", END)
        
        self.workflow = workflow.compile()
        
        logger.info("Workflow built successfully")
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message through the agent workflow.
        
        Args:
            message: User input message
            session_id: Session identifier
            user_id: User identifier
            context: Additional context
            
        Returns:
            Dict containing response and metadata
        """
        start_time = time.time()
        
        try:
            # Validate input with guardrails
            validation_result = await self.guardrails.validate_input(message)
            if not validation_result["valid"]:
                logger.warning("Guardrail validation failed", reason=validation_result["reason"])
                return {
                    "response": validation_result["reason"],
                    "metadata": {"blocked_by_guardrails": True},
                    "tools_used": [],
                    "agent_path": []
                }
            
            # Initialize state
            initial_state = AgentState(
                messages=[HumanMessage(content=message)],
                current_agent="controller",
                user_input=message,
                session_id=session_id,
                user_id=user_id,
                context=context or {},
                agent_outputs={},
                tools_used=[],
                agent_path=["controller"],
                should_continue=True,
                final_response=None,
                error=None
            )
            
            # Execute workflow
            logger.info("Executing workflow", session_id=session_id)
            final_state = await self.workflow.ainvoke(
                initial_state,
                config={"callbacks": [self.langfuse_handler] if self.langfuse_handler else []}
            )
            
            # Update metrics
            latency = (time.time() - start_time) * 1000
            self._update_metrics(final_state, latency)
            
            # Update conversation history
            self._update_history(session_id, message, final_state.get("final_response", ""))
            
            logger.info(
                "Message processed successfully",
                session_id=session_id,
                latency_ms=latency,
                agent_path=final_state.get("agent_path", [])
            )
            
            return {
                "response": final_state.get("final_response", "I'm sorry, I couldn't process that request."),
                "metadata": {
                    "latency_ms": latency,
                    "session_id": session_id
                },
                "tools_used": final_state.get("tools_used", []),
                "agent_path": final_state.get("agent_path", [])
            }
            
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error("Error processing message", error=str(e), session_id=session_id, exc_info=True)
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "metadata": {"error": str(e)},
                "tools_used": [],
                "agent_path": []
            }
    
    async def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify user intent to route to appropriate agent."""
        try:
            user_input = state["user_input"]
            
            if not self.llm:
                # Simple keyword-based classification if no LLM available
                user_input_lower = user_input.lower()
                if any(keyword in user_input_lower for keyword in ["buy", "sell", "trade", "stock", "price", "invest", "portfolio"]):
                    intent = "ADVISOR"
                else:
                    intent = "FAQ"
                logger.info("Intent classified using keywords", intent=intent)
            else:
                classification_prompt = f"""Analyze the following user message and classify it into one of these categories:

1. FAQ: General questions about policies, fees, account management, product information
2. ADVISOR: Trading actions, stock prices, portfolio management, investment advice

User message: {user_input}

Respond with just the category name (FAQ or ADVISOR)."""
                
                messages = [SystemMessage(content=classification_prompt)]
                response = await self.llm.ainvoke(messages)
                intent = response.content.strip().upper()
            
            state["context"]["classified_intent"] = intent
            
            logger.info("Intent classified", intent=intent, session_id=state["session_id"])
            
            return state
            
        except Exception as e:
            logger.error("Intent classification failed", error=str(e))
            state["context"]["classified_intent"] = "FAQ"  # Default fallback
            return state
    
    def _should_route_to_agent(self, state: AgentState) -> str:
        """Determine which agent to route to based on classified intent."""
        intent = state["context"].get("classified_intent", "FAQ")
        
        if intent == "ADVISOR":
            return "advisor"
        elif intent == "FAQ":
            return "faq"
        else:
            return "finalize"
    
    async def _route_to_faq(self, state: AgentState) -> AgentState:
        """Route to FAQ agent."""
        try:
            logger.info("Routing to FAQ agent", session_id=state["session_id"])
            state["agent_path"].append("faq")
            
            result = await self.faq_agent.process(state["user_input"], state["session_id"])
            
            state["agent_outputs"]["faq"] = result
            state["tools_used"].extend(result.get("tools_used", []))
            state["final_response"] = result.get("response", "")
            
            self.metrics["agent_usage"]["faq"] = self.metrics["agent_usage"].get("faq", 0) + 1
            
            return state
            
        except Exception as e:
            logger.error("FAQ agent failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _route_to_advisor(self, state: AgentState) -> AgentState:
        """Route to Advisor agent."""
        try:
            logger.info("Routing to Advisor agent", session_id=state["session_id"])
            state["agent_path"].append("advisor")
            
            result = await self.advisor_agent.process(
                state["user_input"],
                state["session_id"],
                state["context"]
            )
            
            state["agent_outputs"]["advisor"] = result
            state["tools_used"].extend(result.get("tools_used", []))
            state["final_response"] = result.get("response", "")
            
            self.metrics["agent_usage"]["advisor"] = self.metrics["agent_usage"].get("advisor", 0) + 1
            
            return state
            
        except Exception as e:
            logger.error("Advisor agent failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _finalize_response(self, state: AgentState) -> AgentState:
        """Finalize and format the response."""
        try:
            if state.get("error"):
                state["final_response"] = "I encountered an error processing your request. Please try again."
            elif not state.get("final_response"):
                state["final_response"] = "I'm not sure how to help with that. Could you rephrase your question?"
            
            return state
            
        except Exception as e:
            logger.error("Response finalization failed", error=str(e))
            state["final_response"] = "An error occurred. Please try again."
            return state
    
    def _update_metrics(self, state: AgentState, latency: float) -> None:
        """Update internal metrics."""
        self.metrics["total_messages"] += 1
        self.metrics["total_latency"] += latency
        
        for tool in state.get("tools_used", []):
            self.metrics["tool_usage"][tool] = self.metrics["tool_usage"].get(tool, 0) + 1
    
    def _update_history(self, session_id: str, user_msg: str, bot_msg: str) -> None:
        """Update conversation history."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
            self.metrics["total_conversations"] += 1
        
        history = self.conversation_history[session_id]
        history.append({"role": "user", "content": user_msg, "timestamp": time.time()})
        history.append({"role": "assistant", "content": bot_msg, "timestamp": time.time()})
        
        # Trim history to max length
        if len(history) > settings.max_conversation_history:
            self.conversation_history[session_id] = history[-settings.max_conversation_history:]
    
    async def get_metrics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated metrics."""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["total_messages"]
            if self.metrics["total_messages"] > 0
            else 0.0
        )
        
        error_rate = (
            self.metrics["errors"] / self.metrics["total_messages"]
            if self.metrics["total_messages"] > 0
            else 0.0
        )
        
        return {
            "total_conversations": self.metrics["total_conversations"],
            "total_messages": self.metrics["total_messages"],
            "avg_response_time": avg_latency,
            "tool_usage": self.metrics["tool_usage"],
            "agent_usage": self.metrics["agent_usage"],
            "error_rate": error_rate
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up controller agent")
        
        if self.faq_agent:
            await self.faq_agent.cleanup()
        
        if self.advisor_agent:
            await self.advisor_agent.cleanup()
        
        logger.info("Controller agent cleanup complete")