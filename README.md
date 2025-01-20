# SlackSage 🧙‍♂️

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-FF4B4B.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.9-green.svg)](https://python.langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SlackSage is an AI-powered knowledge assistant that brings the power of RAG (Retrieval Augmented Generation) to your Slack workspace. Upload your documents, and SlackSage will intelligently answer questions based on your knowledge base, enhanced with real-time web search capabilities.

![SlackSage Logo](assets/logo.png)

## Features

- 📚 **Document Processing**: Handles various document formats with intelligent text extraction
- 🔍 **Advanced RAG**: Combines document knowledge with web search results
- 💬 **Natural Interaction**: Engage through natural conversations in Slack
- 🎯 **Context-Aware**: Provides accurate, relevant responses based on your specific needs
- 🔄 **Real-time Updates**: Processes documents instantly and maintains up-to-date knowledge
- 🛠️ **Customizable**: Adjust the assistant's personality and behavior through the UI

## Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/slacksage.git
   cd slacksage
   ```

2. **Install Dependencies**
   ```bash
   # Using uv (recommended)
   uv pip install -r requirements.txt
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   - Create `.streamlit/secrets.toml` with your credentials:
   ```toml
   # API Keys
   OPENAI_API_KEY = "your-key"
   
   [slack]
   bot_token = "xoxb-your-token"
   app_token = "xapp-your-token"
   
   # Google Configuration
   GOOGLE_API_KEY = "your-key"
   GOOGLE_CSE_ID = "your-id"
   ```

4. **Run the Application**
   ```bash
   streamlit run app/Home.py
   ```

## Setup Guide

### Prerequisites
- Python 3.12+
- A Slack workspace with admin access
- OpenAI API key
- (Optional) Google API key for web search

### Detailed Setup
1. **Create Slack App**
   - Visit [Slack API Dashboard](https://api.slack.com/apps)
   - Create new app from scratch
   - Enable Socket Mode
   - Configure bot permissions
   - Install to workspace

2. **Configure Bot Permissions**
   Required scopes:
   - `app_mentions:read`
   - `channels:history`
   - `chat:write`
   - `mpim:read`

3. **Enable Events**
   - Enable Event Subscriptions
   - Subscribe to bot events:
     - `app_mentions`
     - `message.channels`

For detailed setup instructions, visit the Setup Guide in the application.

## Usage

1. **Upload Documents**
   - Support for various document formats
   - Documents are processed and vectorized instantly
   - Manage documents through the UI

2. **Start the Bot**
   - Configure credentials
   - Initialize the system
   - Start the bot through the UI

3. **Interact in Slack**
   ```
   @SlackSage What are our company's vacation policies?
   ```

## Architecture

SlackSage uses a sophisticated RAG (Retrieval Augmented Generation) system:

1. **Document Processing**
   - Text extraction and chunking
   - Vector embeddings creation
   - FAISS vector store for efficient retrieval

2. **Query Processing**
   - Semantic search in vector store
   - Web search integration
   - Context merging and ranking

3. **Response Generation**
   - GPT-4 for natural language generation
   - Context-aware responses
   - Source attribution

## Development

### Project Structure
```
slacksage/
├── app/
│   ├── Home.py            # Main Streamlit interface
│   ├── rag.py            # RAG system implementation
│   ├── slack_bot.py      # Slack bot implementation
│   └── pages/            # Additional UI pages
├── assets/               # Images and static files
├── data/                # Document storage
│   ├── rag-files/       # Uploaded documents
│   └── vectorstore/     # FAISS indexes
└── requirements.txt     # Python dependencies
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## About

Built by [WillyV3](https://github.com/williavs), founder of [V3 AI](https://v3-ai.com).

### Connect
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/williavs)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/willyv3/)
[![Website](https://img.shields.io/badge/V3_AI-FF4B4B?style=for-the-badge&logo=safari&logoColor=white)](https://v3-ai.com)
[![PM Feels](https://img.shields.io/badge/PM_Feels-4A154B?style=for-the-badge&logo=slack&logoColor=white)](https://pmfeels.com) 