@echo off
cd /d "%~dp0"
echo Starting Streamlit Frontend...
start "Streamlit - Trading Chatbot" /D "%~dp0" .venv\Scripts\streamlit.exe run app.py
echo.
echo Streamlit is starting in a new window...
echo Access it at: http://localhost:8501
echo.
pause
