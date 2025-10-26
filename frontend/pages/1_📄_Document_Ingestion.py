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

# Custom CSS
st.markdown("""
<style>
    .upload-box {
        border: 2px dashed #2196f3;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
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


def main():
    """Main application function."""
    
    # Sidebar for consistency
    with st.sidebar:
        st.title("Trading Chatbot")
        
        # Navigation info
        st.markdown("### 📍 Pages")
        st.info("💬 **Chat** - Use sidebar navigation\n\n📄 **Document Ingestion** - Current Page")
        
        st.markdown("---")
        
        # Quick info
        st.markdown("### ℹ️ About")
        st.caption("Upload documents to enhance the chatbot's knowledge base")
    
    # Header
    st.title("📄 Document Ingestion")
    st.markdown("Upload documents to enhance the chatbot's knowledge base")
    
    # Check backend status
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("---")
    
    with col2:
        if check_backend_health():
            st.success("Backend Online")
        else:
            st.error("Backend Offline")
            st.warning("Please start the backend server before uploading documents.")
            st.code("docker-compose -f docker/docker-compose.yml up", language="bash")
            st.stop()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📤 Upload Document", "ℹ️ Guidelines", "📊 Status"])
    
    with tab1:
        st.subheader("Upload Document")
        
        # Document type selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            document_type = st.selectbox(
                "Document Type",
                options=["faq", "policy", "product_info", "general"],
                help="Select the type of document you're uploading"
            )
        
        with col2:
            st.markdown("**Document Types:**")
            st.caption("• FAQ: Frequently Asked Questions")
            st.caption("• Policy: Trading Policies")
            st.caption("• Product Info: Product Information")
            st.caption("• General: Other Documents")
        
        st.markdown("---")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=["pdf", "txt", "md"],
            help="Supported formats: PDF, TXT, MD (Max size: 10MB)"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.markdown("**File Information:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Filename", uploaded_file.name)
            with col2:
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                st.metric("Size", f"{file_size_mb:.2f} MB")
            with col3:
                st.metric("Type", uploaded_file.type or "text/plain")
            
            # File preview for text files
            if uploaded_file.type in ["text/plain", "text/markdown", None]:
                with st.expander("📖 Preview File Content"):
                    try:
                        content = uploaded_file.getvalue().decode("utf-8")
                        preview = content[:1000] + ("..." if len(content) > 1000 else "")
                        st.text_area("Content Preview", preview, height=200)
                    except:
                        st.warning("Unable to preview file content")
            
            st.markdown("---")
            
            # Upload button
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("🚀 Ingest Document", type="primary", use_container_width=True):
                    with st.spinner("Uploading and processing document..."):
                        result = ingest_document(uploaded_file, document_type)
                        
                        if result["success"]:
                            data = result["data"]
                            st.success("✅ Document ingested successfully!")
                            
                            # Display results
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Chunks Created", data.get("chunks_created", 0))
                            with col2:
                                st.metric("Status", "Success")
                            
                            if "message" in data:
                                st.info(data["message"])
                            
                            # Show details
                            with st.expander("📋 Details"):
                                st.json(data)
                        else:
                            st.error(f"❌ Error: {result['error']}")
                            if "details" in result:
                                with st.expander("Error Details"):
                                    st.code(result["details"])
            
            with col2:
                if st.button("🔄 Clear", use_container_width=True):
                    st.rerun()
    
    with tab2:
        st.subheader("📚 Document Ingestion Guidelines")
        
        st.markdown("""
        ### Supported File Types
        - **PDF**: Portable Document Format
        - **TXT**: Plain text files
        - **MD**: Markdown files
        
        ### File Size Limits
        - Maximum file size: **10 MB**
        - Recommended: Keep files under 5 MB for faster processing
        
        ### Document Types Explained
        
        #### 🤔 FAQ (Frequently Asked Questions)
        - Common questions and answers about trading
        - Customer support documentation
        - Quick reference guides
        
        #### 📜 Policy
        - Trading policies and regulations
        - Terms and conditions
        - Compliance documents
        
        #### 📦 Product Info
        - Product descriptions and specifications
        - Feature documentation
        - Service offerings
        
        #### 📄 General
        - Any other relevant documents
        - Training materials
        - Reference documentation
        
        ### Best Practices
        
        1. **Use Clear Formatting**
           - Structure your documents with clear headings
           - Use bullet points for lists
           - Keep paragraphs concise
        
        2. **Optimize Content**
           - Remove unnecessary formatting
           - Ensure text is readable and well-organized
           - Include relevant keywords
        
        3. **File Organization**
           - Use descriptive filenames
           - Group related content in single documents
           - Keep documents focused on specific topics
        
        4. **Quality Over Quantity**
           - Upload accurate and up-to-date information
           - Review content before uploading
           - Remove duplicate information
        
        ### Processing Details
        
        - Documents are automatically chunked for optimal retrieval
        - Default chunk size: 1000 characters
        - Chunk overlap: 200 characters
        - Embeddings are generated using OpenAI's text-embedding model
        - Documents are stored in Pinecone vector database
        """)
        
        st.markdown("---")
        
        st.info("""
        **💡 Tip:** After ingesting documents, test the chatbot to ensure it can 
        retrieve and use the new information effectively.
        """)
    
    with tab3:
        st.subheader("📊 System Status")
        
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        # Backend health
        st.markdown("### Backend Services")
        
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Status", health_data.get("status", "unknown").upper())
                    st.metric("Environment", health_data.get("environment", "N/A"))
                
                with col2:
                    st.metric("Version", health_data.get("version", "N/A"))
                
                # Components status
                if "components" in health_data:
                    st.markdown("### Components Status")
                    components = health_data["components"]
                    
                    for component, status in components.items():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{component.replace('_', ' ').title()}**")
                        with col2:
                            if status:
                                st.success("✅ Active")
                            else:
                                st.error("❌ Inactive")
            else:
                st.error("Unable to fetch health status")
        except Exception as e:
            st.error(f"Error checking backend: {str(e)}")
        
        st.markdown("---")
        
        # API Information
        st.markdown("### API Endpoints")
        st.code(f"Health Check: {HEALTH_ENDPOINT}", language="text")
        st.code(f"Ingest Document: {INGEST_ENDPOINT}", language="text")
        
        st.markdown("---")
        
        # Quick info
        st.markdown("### ℹ️ Information")
        st.caption("📖 Check the Guidelines tab for detailed documentation")
        st.caption("� View the Status tab for backend health information")


if __name__ == "__main__":
    main()
