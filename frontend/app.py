# -*- coding: utf-8 -*-
"""
Streamlit Chat UI for Trading Chatbot
A simple and elegant chat interface for interacting with the trading chatbot backend.
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any, List
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
METRICS_ENDPOINT = f"{API_BASE_URL}/metrics"

# Page configuration
st.set_page_config(
    page_title="Trading Chatbot",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    .chat-message.assistant {
        background-color: #f5f5f5;
        border-left: 5px solid #4caf50;
    }
    .chat-message .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #333;
    }
    .chat-message.user .message-header {
        color: #1976d2;
    }
    .chat-message.assistant .message-header {
        color: #388e3c;
    }
    .metadata {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
        font-style: italic;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if "user_id" not in st.session_state:
        st.session_state.user_id = "streamlit_user"
    if "backend_healthy" not in st.session_state:
        st.session_state.backend_healthy = False


def check_backend_health() -> Dict[str, Any]:
    """Check if backend is healthy and return status."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            st.session_state.backend_healthy = True
            return response.json()
        else:
            st.session_state.backend_healthy = False
            return {"status": "unhealthy", "error": f"Status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        st.session_state.backend_healthy = False
        return {"status": "unhealthy", "error": str(e)}


def send_message(message: str) -> Dict[str, Any]:
    """Send message to chatbot backend."""
    try:
        payload = {
            "message": message,
            "session_id": st.session_state.session_id,
            "user_id": st.session_state.user_id,
            "context": {}
        }
        
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "response": f"Error: Backend returned status code {response.status_code}",
                "metadata": {"error": True},
                "tools_used": [],
                "agent_path": []
            }
    except requests.exceptions.Timeout:
        return {
            "response": "Request timed out. The backend might be processing a complex query.",
            "metadata": {"error": True, "timeout": True},
            "tools_used": [],
            "agent_path": []
        }
    except requests.exceptions.RequestException as e:
        return {
            "response": f"Connection error: {str(e)}. Please check if the backend is running.",
            "metadata": {"error": True},
            "tools_used": [],
            "agent_path": []
        }


def get_metrics() -> Dict[str, Any]:
    """Fetch metrics from backend."""
    try:
        response = requests.get(METRICS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def display_message(role: str, content: str, metadata: Dict[str, Any] = None):
    """Display a chat message with metadata."""
    css_class = "user" if role == "user" else "assistant"
    icon = "User" if role == "user" else "Bot"
    
    message_html = f"""
    <div class="chat-message {css_class}">
        <div class="message-header">{icon}</div>
        <div>{content}</div>
    """
    
    if metadata:
        metadata_info = []
        if "latency_ms" in metadata:
            metadata_info.append(f"Response Time: {metadata['latency_ms']:.0f}ms")
        if "tools_used" in metadata and metadata["tools_used"]:
            metadata_info.append(f"Tools: {', '.join(metadata['tools_used'])}")
        if "agent_path" in metadata and metadata["agent_path"]:
            metadata_info.append(f"Path: {' -> '.join(metadata['agent_path'])}")
        
        if metadata_info:
            message_html += f'<div class="metadata">{" | ".join(metadata_info)}</div>'
    
    message_html += "</div>"
    st.markdown(message_html, unsafe_allow_html=True)


def main():
    """Main application function."""
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("Trading Chatbot")
        
        # Navigation info
        st.markdown("### 📍 Navigation")
        st.info("""
        **Current Page:** 💬 Chat
        
        **Other Pages:**
        - 📄 Document Ingestion (see sidebar)
        """)
        
        st.markdown("---")
        
        # Backend health check
        st.subheader("Backend Status")
        if st.button("Check Health", use_container_width=True):
            with st.spinner("Checking..."):
                health = check_backend_health()
        else:
            health = check_backend_health()
        
        if st.session_state.backend_healthy:
            st.success("Backend is healthy")
            if isinstance(health, dict) and "components" in health:
                with st.expander("Component Details"):
                    for component, status in health["components"].items():
                        icon = "OK" if status else "X"
                        st.write(f"{icon} {component}")
        else:
            st.error("Backend is unavailable")
            if isinstance(health, dict) and "error" in health:
                st.caption(f"Error: {health['error']}")
        
        st.markdown("---")
        
        # Session info
        st.subheader("Session Info")
        st.caption(f"**Session ID:** {st.session_state.session_id}")
        st.caption(f"**User ID:** {st.session_state.user_id}")
        st.caption(f"**Messages:** {len(st.session_state.messages)}")
        
        # Metrics
        if st.button("View Metrics", use_container_width=True):
            metrics = get_metrics()
            if metrics:
                with st.expander("System Metrics", expanded=True):
                    if "total_messages" in metrics:
                        st.metric("Total Messages", metrics["total_messages"])
                    if "avg_response_time" in metrics:
                        st.metric("Avg Response Time", f"{metrics['avg_response_time']:.0f}ms")
                    if "error_rate" in metrics:
                        st.metric("Error Rate", f"{metrics['error_rate']*100:.1f}%")
        
        st.markdown("---")
        
        # Controls
        st.subheader("Controls")
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        if st.button("New Session", use_container_width=True):
            st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.caption("Built with Streamlit")
        st.caption(f"API: {API_BASE_URL}")
    
    # Main chat interface
    st.title("💬 Trading Chatbot Assistant")
    
    # Prominent info about document ingestion
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("📄 **To upload documents:** Click '📄 Document Ingestion' in the sidebar ← (left side)")
    
    if not st.session_state.backend_healthy:
        st.warning("Backend is not available. Please ensure the backend server is running on " + API_BASE_URL)
        st.info("Start the backend with: `docker-compose -f docker/docker-compose.yml up`")
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.info("Welcome! I'm your trading assistant. Ask me anything about trading, policies, FAQs, or get investment advice!")
        
        for msg in st.session_state.messages:
            display_message(
                role=msg["role"],
                content=msg["content"],
                metadata=msg.get("metadata")
            )
    
    # Chat input
    st.markdown("---")
    
    # Example prompts
    st.subheader("Try asking:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("What are your trading policies?", use_container_width=True):
            st.session_state.prompt_input = "What are your trading policies?"
    
    with col2:
        if st.button("How do I open an account?", use_container_width=True):
            st.session_state.prompt_input = "How do I open a trading account?"
    
    with col3:
        if st.button("Recommend stocks for me", use_container_width=True):
            st.session_state.prompt_input = "Can you recommend some stocks for a moderate risk portfolio?"
    
    # Input field
    user_input = st.chat_input(
        "Type your message here...",
        disabled=not st.session_state.backend_healthy
    )
    
    # Handle prompt button clicks
    if "prompt_input" in st.session_state:
        user_input = st.session_state.prompt_input
        del st.session_state.prompt_input
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "metadata": {}
        })
        
        # Display user message immediately
        with chat_container:
            display_message("user", user_input)
        
        # Get bot response
        with st.spinner("Thinking..."):
            response_data = send_message(user_input)
        
        # Add assistant message to chat
        assistant_message = {
            "role": "assistant",
            "content": response_data.get("response", "Sorry, I couldn't process that."),
            "metadata": {
                **response_data.get("metadata", {}),
                "tools_used": response_data.get("tools_used", []),
                "agent_path": response_data.get("agent_path", [])
            }
        }
        st.session_state.messages.append(assistant_message)
        
        # Rerun to display new messages
        st.rerun()


if __name__ == "__main__":
    main()
