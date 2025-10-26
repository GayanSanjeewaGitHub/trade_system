# Fix: Session Closed Error During Document Ingestion

## Problem
When ingesting documents (like `policies.txt`), the system was throwing a "Session is closed" error:
```
Exception: Session is closed
```

This error occurred in the document ingestion pipeline when trying to add documents to the vector store.

## Root Cause
The OpenAI embeddings client's HTTP session was being closed prematurely during the document ingestion process. This happened because:

1. The OpenAI client has default timeout and session management settings that were too restrictive
2. No retry logic existed to handle transient session errors
3. The embeddings client wasn't configured with appropriate timeout and chunking parameters

## Solutions Implemented

### 1. Updated OpenAI Embeddings Configuration (`retriever.py`)

**Changed:**
```python
self.embeddings = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.openai_api_key,
    max_retries=3,
    timeout=60
)
```

**To:**
```python
self.embeddings = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.openai_api_key,
    max_retries=5,                    # Increased retries
    request_timeout=120,               # Longer timeout
    show_progress_bar=False,
    chunk_size=100                     # Process in smaller batches
)
```

**Benefits:**
- More retry attempts (5 instead of 3)
- Longer request timeout (120s instead of 60s)
- Smaller chunk sizes reduce chance of timeout
- Prevents progress bar interference in production

### 2. Added Retry Logic in Document Ingestion (`ingestion.py`)

**New Features:**
- ✅ Automatic retriever re-initialization on session errors
- ✅ Retry logic with up to 3 attempts
- ✅ Intelligent error detection for session-related issues
- ✅ Brief delays between retries to allow session recovery

**Implementation:**
```python
# Add to vector store with retry logic
max_retries = 3
for attempt in range(max_retries):
    try:
        result = await self.retriever.add_documents(documents)
        
        if result["success"]:
            # Success - return result
            return {...}
        else:
            error_msg = result.get("error", "Unknown error")
            if "session" in error_msg.lower() and attempt < max_retries - 1:
                # Reinitialize on session error
                await self.retriever.initialize()
                continue
            raise Exception(error_msg)
            
    except Exception as e:
        if "session" in str(e).lower() and attempt < max_retries - 1:
            # Reinitialize and retry
            await self.retriever.initialize()
            await asyncio.sleep(1)  # Brief delay
            continue
        raise
```

### 3. Added Retriever Health Check

**Before processing:**
```python
# Ensure retriever is initialized
if not self.retriever or not self.retriever.vector_store:
    logger.warning("Retriever not initialized, reinitializing...")
    await self.initialize()
    
if not self.retriever or not self.retriever.vector_store:
    raise Exception("Failed to initialize retriever")
```

This ensures the retriever is always in a healthy state before attempting ingestion.

## Testing the Fix

### 1. Restart the Application
```bash
docker-compose down
docker-compose up --build
```

### 2. Test Document Ingestion
Upload a document through the `/ingest` endpoint:

**Using curl:**
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@policies.txt" \
  -F "document_type=policy"
```

**Expected Success Response:**
```json
{
  "success": true,
  "filename": "policies.txt",
  "chunks_created": 5,
  "message": "Document ingested successfully"
}
```

### 3. Monitor Logs
Watch for successful ingestion messages:
```
{"event": "Document ingested successfully", "filename": "policies.txt", "chunks": 5}
```

## Prevention Strategies

### 1. Environment Configuration
Ensure your `.env` has valid API keys:
```bash
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...  # Or use FAISS fallback
```

### 2. Resource Monitoring
- Monitor OpenAI API rate limits
- Check network connectivity
- Ensure adequate timeout settings

### 3. Fallback Mechanisms
The system automatically falls back to FAISS in-memory storage if Pinecone is unavailable:
```
{"event": "Pinecone API key not configured, using FAISS in-memory fallback"}
```

## Additional Improvements

### Session Management
- Longer timeout prevents premature session closure
- Automatic retry on transient failures
- Intelligent error detection and recovery

### Performance
- Smaller chunk sizes (100 instead of default) for better processing
- Better memory management
- Reduced chance of timeout on large documents

### Reliability
- Up to 3 retry attempts
- Automatic re-initialization on failure
- Health checks before processing

## Troubleshooting

### If the error persists:

**1. Check OpenAI API Status**
```bash
# Verify API key is valid
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**2. Check Logs for Specific Errors**
```bash
docker-compose logs -f trading-chatbot | grep -i error
```

**3. Verify File Format**
- Ensure file is valid `.txt`, `.pdf`, or `.md`
- Check file is not corrupted
- Verify file size is under limit (10MB by default)

**4. Test with Smaller Files First**
Start with a small test file to isolate the issue.

**5. Check Network Connectivity**
Ensure the container can reach OpenAI APIs:
```bash
docker-compose exec trading-chatbot ping api.openai.com
```

## Related Configuration

### Environment Variables
```bash
# Increase timeouts if needed
LLM_TIMEOUT=120

# Adjust chunk processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Docker Resource Limits
Ensure Docker has adequate resources:
- Memory: At least 2GB
- CPU: At least 2 cores

## Summary

The "Session is closed" error has been fixed by:
1. ✅ Configuring OpenAI embeddings with longer timeouts and more retries
2. ✅ Adding automatic retry logic with session re-initialization
3. ✅ Implementing health checks before document processing
4. ✅ Processing documents in smaller chunks
5. ✅ Adding intelligent error detection and recovery

The system should now reliably ingest documents even with transient network or session issues.
