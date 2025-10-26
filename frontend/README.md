# Trading Chatbot - Streamlit Frontend

A simple and elegant multi-page interface for interacting with the Trading Chatbot backend.

## Features

- 💬 **Real-time chat interface** - Interactive conversation with the trading assistant
- � **Document ingestion** - Upload PDF/TXT files to enhance the knowledge base
- �🔍 **Backend health monitoring** - Real-time service status
- 📊 **Session and metrics tracking** - Performance analytics
- 🎨 **Clean and responsive UI** - Modern design with intuitive navigation
- 🔄 **Session management** - Conversation history and state management
- 📈 **Performance metrics display** - Response times and usage stats

## Pages

### 💬 Chat (Main Page)
- Send messages to the trading chatbot
- View conversation history with metadata
- See response times, tools used, and agent paths
- Example prompts for quick interactions

### 📄 Document Ingestion
- Upload PDF, TXT, or MD files
- Choose document types (FAQ, Policy, Product Info, General)
- Real-time upload progress
- File preview for text documents
- Ingestion status and chunk information

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using the main project's environment:
```bash
cd ..
pip install streamlit requests
```

## Running the Application

1. Make sure the backend is running:
```bash
cd ..
docker-compose -f docker/docker-compose.yml up
```

2. Start the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Configuration

The frontend connects to the backend at `http://localhost:8000` by default.

To change the backend URL, edit the `API_BASE_URL` variable in `app.py`:

```python
API_BASE_URL = "http://your-backend-url:port"
```

## Usage

1. **Chat Interface**: Type your questions in the input box and press Enter
2. **Example Prompts**: Click on the suggested prompts to quickly ask common questions
3. **Backend Status**: Check the sidebar for backend health status
4. **Metrics**: View system metrics and performance stats
5. **Session Management**: Clear chat or start a new session from the sidebar

## Features Overview

### Main Chat
- Send messages to the trading chatbot
- View conversation history
- See response metadata (latency, tools used, agent path)

### Sidebar Controls
- **Backend Status**: Real-time health check of backend services
- **Session Info**: Current session ID and message count
- **Metrics**: View system-wide performance metrics
- **Controls**: Clear chat history or start new session

### UI Enhancements
- Color-coded messages (blue for user, green for assistant)
- Response metadata display (latency, tools, agent path)
- Example prompts for quick interactions
- Responsive design

## Troubleshooting

### Backend Not Available
If you see "Backend is not available":
1. Ensure Docker containers are running: `docker-compose -f docker/docker-compose.yml up`
2. Check if backend is accessible at `http://localhost:8000/health`
3. Verify no firewall is blocking the connection

### Slow Responses
- Check backend logs for performance issues
- View metrics in the sidebar to see average response times
- Complex queries may take longer to process

### Connection Timeout
- Default timeout is 60 seconds
- For longer queries, the timeout can be adjusted in `app.py` in the `send_message` function

## Development

### File Structure
```
frontend/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Customization
- Modify CSS in the `st.markdown()` section for custom styling
- Adjust timeout values in the `send_message()` function
- Add new sidebar widgets in the sidebar section
- Customize example prompts in the main interface

## Tips

- Use the example prompts to get started quickly
- Check the metadata below each response to see which agents and tools were used
- Monitor the session info to track conversation length
- Use "New Session" to start fresh without clearing visual history
- Use "Clear Chat History" to remove all messages from view

## Support

For issues or questions:
1. Check backend logs: `docker-compose -f docker/docker-compose.yml logs`
2. Verify backend health endpoint: `curl http://localhost:8000/health`
3. Review Streamlit logs in the terminal where you ran `streamlit run app.py`
