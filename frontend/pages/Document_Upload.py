# -*- coding: utf-8 -*-
"""
Document Ingestion Page
Upload and ingest PDF/TXT files into the RAG system
"""

import streamlit as st
import requests
from typing import Dict, Any
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
INGEST_ENDPOINT = f"{API_BASE_URL}/ingest"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# Page title
st.title("📄 Document Upload & Ingestion")
st.markdown("Upload documents to enhance the chatbot's knowledge base")

# Custom CSS
st.markdown("""
<style>
    .upload-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_backend_health() -> bool:
    """Check if backend is available."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except:
        return False


def ingest_document(file, document_type: str) -> Dict[str, Any]:
    """Upload and ingest document to backend."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {"document_type": document_type}
        
        response = requests.post(
            INGEST_ENDPOINT,
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False,
                "error": f"Server returned status code {response.status_code}",
                "details": response.text
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out. Large files may take longer to process."
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


# Check backend status
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col2:
    if check_backend_health():
        st.success("✅ Backend Online")
    else:
        st.error("❌ Backend Offline")
        st.warning("Please start the backend server before uploading documents.")
        st.code("docker-compose -f docker/docker-compose.yml up", language="bash")
        st.stop()

st.markdown("---")

# Main upload section
st.subheader("📤 Upload Document")

# Document type selection
document_type = st.selectbox(
    "Select Document Type",
    options=["faq", "policy", "product_info", "general"],
    help="Choose the category for your document"
)

# Type descriptions
with st.expander("ℹ️ Document Type Descriptions"):
    st.markdown("""
    - **FAQ**: Frequently Asked Questions and answers
    - **Policy**: Trading policies, terms, and regulations
    - **Product Info**: Product descriptions and features
    - **General**: Any other relevant documents
    """)

st.markdown("---")

# File uploader
uploaded_file = st.file_uploader(
    "📁 Choose a file to upload",
    type=["pdf", "txt", "md"],
    help="Supported formats: PDF, TXT, MD (Max size: 10MB)"
)

if uploaded_file is not None:
    # Display file info
    st.success(f"✅ File selected: {uploaded_file.name}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📄 Filename", uploaded_file.name)
    with col2:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.metric("📊 Size", f"{file_size_mb:.2f} MB")
    with col3:
        file_type = uploaded_file.type or "text/plain"
        st.metric("🏷️ Type", file_type.split("/")[-1].upper())
    
    # File preview for text files
    if uploaded_file.type in ["text/plain", "text/markdown", None]:
        with st.expander("👁️ Preview File Content"):
            try:
                content = uploaded_file.getvalue().decode("utf-8")
                preview = content[:1000] + ("..." if len(content) > 1000 else "")
                st.text_area("Content Preview (first 1000 chars)", preview, height=200, disabled=True)
            except:
                st.warning("Unable to preview file content")
    
    st.markdown("---")
    
    # Upload button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 Upload & Ingest", type="primary", use_container_width=True):
            with st.spinner("⏳ Uploading and processing document..."):
                result = ingest_document(uploaded_file, document_type)
                
                if result["success"]:
                    data = result["data"]
                    st.success("✅ Document ingested successfully!")
                    
                    # Display results
                    st.markdown("### 📊 Ingestion Results")
                    result_col1, result_col2 = st.columns(2)
                    
                    with result_col1:
                        chunks = data.get("chunks_created", 0)
                        st.metric("🔢 Chunks Created", chunks)
                    
                    with result_col2:
                        st.metric("✅ Status", "Success")
                    
                    if "message" in data:
                        st.info(f"ℹ️ {data['message']}")
                    
                    # Show details
                    with st.expander("📋 View Details"):
                        st.json(data)
                    
                    st.balloons()
                else:
                    st.error(f"❌ Error: {result['error']}")
                    if "details" in result:
                        with st.expander("🔍 Error Details"):
                            st.code(result["details"])
    
    with col2:
        if st.button("🔄 Clear Selection", use_container_width=True):
            st.rerun()

else:
    st.info("👆 Please select a file to upload")

st.markdown("---")

# Guidelines section
with st.expander("📚 Upload Guidelines & Best Practices"):
    st.markdown("""
    ### ✅ Supported File Types
    - **PDF** (.pdf) - Portable Document Format
    - **Text** (.txt) - Plain text files
    - **Markdown** (.md) - Markdown formatted files
    
    ### 📏 File Requirements
    - **Maximum file size**: 10 MB
    - **Recommended size**: Under 5 MB for faster processing
    - **Encoding**: UTF-8 recommended for text files
    
    ### 🎯 Best Practices
    
    1. **Clear Structure**
       - Use clear headings and sections
       - Organize content logically
       - Keep paragraphs concise
    
    2. **Quality Content**
       - Ensure information is accurate and current
       - Remove duplicate information
       - Use descriptive titles
    
    3. **Optimal Formatting**
       - Use bullet points for lists
       - Avoid excessive formatting
       - Include relevant keywords
    
    ### ⚙️ Processing Information
    - Documents are automatically split into chunks (1000 chars with 200 char overlap)
    - Embeddings are generated using OpenAI's text-embedding model
    - Data is stored in Pinecone vector database
    - The chatbot can then retrieve and use this information
    
    ### 💡 Pro Tip
    After uploading, test the chatbot by asking questions related to your document!
    """)

# System status
with st.expander("🔍 System Status & Health Check"):
    if st.button("🔄 Refresh Status"):
        st.rerun()
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            
            st.success(f"✅ System Status: {health_data.get('status', 'unknown').upper()}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🌍 Environment", health_data.get("environment", "N/A"))
            with col2:
                st.metric("🏷️ Version", health_data.get("version", "N/A"))
            
            # Components
            if "components" in health_data:
                st.markdown("#### Component Status")
                for component, status in health_data["components"].items():
                    icon = "✅" if status else "❌"
                    st.write(f"{icon} **{component.replace('_', ' ').title()}**: {'Active' if status else 'Inactive'}")
        else:
            st.error("❌ Unable to fetch health status")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    st.caption(f"📡 API Endpoint: {INGEST_ENDPOINT}")
