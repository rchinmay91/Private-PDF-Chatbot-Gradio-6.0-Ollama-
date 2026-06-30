# Private PDF Chatbot (Offline & API-Key Free)

A 100% private, offline AI application built using **Gradio**, **LangChain**, **PyPDF**, and **Chroma DB**. It allows you to upload any PDF document and chat with it locally using **Ollama**. No cloud APIs, no data leaks.

## 🛠️ Requirements
* Python 3.9 or higher
* [Ollama](https://ollama.com) installed and running locally

## 🚀 Quick Start Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd "pdf chat ai"
   ```

2. **Install the dependencies:**
   Make sure your local environment is active, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Pull the local AI models:**
   Ensure Ollama is running in the background, then execute:
   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```

4. **Launch the application:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:7860` in your web browser to start chatting!
