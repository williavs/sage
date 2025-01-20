import os
from typing import Dict
from pathlib import Path

import streamlit as st
import logging

from rag import RAGSystem
from slack_bot import SlackBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Must be the first Streamlit command
st.set_page_config(
    page_title="SlackSage",
    page_icon="assets/logo.png",
    layout="wide"
)

# Initialize session state
if "credentials" not in st.session_state:
    st.session_state.credentials = {}
if "credentials_valid" not in st.session_state:
    st.session_state.credentials_valid = False
if "bot_running" not in st.session_state:
    st.session_state.bot_running = False
if "rag_system" not in st.session_state:
    st.session_state.rag_system = None
if "slack_bot" not in st.session_state:
    st.session_state.slack_bot = None
if "documents" not in st.session_state:
    st.session_state.documents = {}  # Store documents in memory

# Ensure data directories exist
os.makedirs("data/rag-files", exist_ok=True)
os.makedirs("data/vectorstore", exist_ok=True)

def validate_credentials() -> bool:
    """Validate that all required credentials are present."""
    try:
        # Get OpenAI key from user input
        if not st.session_state.credentials.get("OPENAI_API_KEY"):
            st.warning("Missing OpenAI API Key")
            return False
            
        # Get Google credentials from secrets
        st.session_state.credentials["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
        st.session_state.credentials["GOOGLE_CSE_ID"] = st.secrets["GOOGLE_CSE_ID"]
        
        # Get Slack tokens from user input
        if not st.session_state.credentials.get("SLACK_BOT_TOKEN"):
            st.warning("Missing Slack Bot Token")
            return False
        if not st.session_state.credentials.get("SLACK_APP_TOKEN"):
            st.warning("Missing Slack App Token")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error loading credentials: {str(e)}")
        st.error("Error loading credentials. Please check your configuration.")
        return False

def initialize_systems():
    """Initialize RAG and Slack systems."""
    if st.session_state.credentials_valid and st.session_state.documents:
        try:
            # Initialize RAG system with in-memory documents
            st.session_state.rag_system = RAGSystem(st.session_state.documents, st.session_state.credentials)
            
            # Initialize RAG system
            if st.session_state.rag_system.initialize_system():
                logger.info("RAG system initialized successfully")
                # Initialize Slack bot with the same RAG instance
                st.session_state.slack_bot = SlackBot(st.session_state.rag_system, st.session_state.credentials)
                st.success("Systems initialized successfully!")
                return True
            else:
                logger.error("Failed to initialize RAG system")
                st.error("Failed to initialize RAG system. Please check your documents.")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing systems: {str(e)}")
            st.error("Error initializing systems. Please check your credentials and documents.")
            return False
    else:
        if not st.session_state.credentials_valid:
            logger.warning("Credentials not validated")
            st.warning("Please validate your credentials first.")
        if not st.session_state.documents:
            logger.warning("No documents available")
            st.warning("Please upload at least one document.")
        return False

def initialize_session_state():
    """Initialize session state variables."""
    if "documents" not in st.session_state:
        st.session_state.documents = {}
    if "credentials" not in st.session_state:
        st.session_state.credentials = {}
    if "rag_system" not in st.session_state:
        st.session_state.rag_system = None

def handle_document_upload():
    """Handle document upload and store in session state."""
    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "txt", "csv"], key="doc_uploader")
    
    if uploaded_file:
        try:
            # Read file content
            file_content = uploaded_file.read()
            
            # Store in session state
            st.session_state.documents[uploaded_file.name] = file_content
            
            # Log success
            logger.info(f"Successfully stored document: {uploaded_file.name}")
            st.success(f"File {uploaded_file.name} uploaded successfully!")
            
            # Initialize systems with updated documents
            if st.session_state.credentials_valid:
                initialize_systems()
            
        except Exception as e:
            logger.error(f"Error processing uploaded file: {str(e)}")
            st.error("Failed to process uploaded file. Please try again.")

def initialize_rag_system():
    """Initialize or reinitialize the RAG system with current documents."""
    if st.session_state.documents:
        try:
            st.session_state.rag_system = RAGSystem(
                documents=st.session_state.documents,
                credentials=st.session_state.credentials
            )
            
            if st.session_state.rag_system.initialize_system():
                logger.info("RAG system initialized successfully")
                st.success("RAG system initialized successfully!")
            else:
                logger.error("Failed to initialize RAG system")
                st.error("Failed to initialize RAG system. Please check your documents.")
                
        except Exception as e:
            logger.error(f"Error initializing RAG system: {str(e)}")
            st.error("Error initializing RAG system. Please check your credentials and documents.")
    else:
        logger.warning("No documents available to initialize RAG system")
        st.warning("Please upload at least one document to initialize the RAG system.")

def display_documents():
    """Display uploaded documents and provide options to manage them."""
    if st.session_state.documents:
        st.write("### Uploaded Documents")
        for filename in st.session_state.documents.keys():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {filename}")
            with col2:
                if st.button("Delete", key=f"del_{filename}"):
                    del st.session_state.documents[filename]
                    st.rerun()
        
        if st.button("Clear All Documents"):
            st.session_state.documents = {}
            st.rerun()
    else:
        st.info("No documents uploaded yet.")

def reset_bot_state():
    """Reset bot-related session state variables."""
    st.session_state.bot_running = False
    st.session_state.slack_bot = None
    st.session_state.rag_system = None
    logger.info("Bot state reset")

def start_bot():
    """Start the bot with proper initialization."""
    if initialize_systems():
        if st.session_state.slack_bot.start():
            st.session_state.bot_running = True
            logger.info("Bot started successfully")
            st.rerun()
        else:
            logger.error("Failed to start Slack bot")
            reset_bot_state()
    else:
        logger.error("Failed to initialize systems")
        reset_bot_state()

def stop_bot():
    """Stop the bot and clean up resources."""
    if st.session_state.slack_bot:
        st.session_state.slack_bot.stop()
    reset_bot_state()
    st.rerun()

def show_welcome():
    """Display the welcome section."""
    st.title("SlackSage")
    
    # Demo notice
    st.caption("🚀 Demo Version")
    
    # Welcome message
    st.markdown("""
    ### AI-Powered Knowledge Assistant for Slack
    
    Enhance your team's productivity with an intelligent Slack integration that:
    - 📚 Processes and understands your organization's documents
    - 🔍 Combines internal knowledge with relevant web data
    - 💬 Delivers accurate information through natural conversations
    - 📊 Provides data-driven insights and responses
    """)
    
    st.info("""
    **Quick Start:**
    1. Configure your API credentials
    2. Upload your documentation
    3. Connect and start using in Slack
    
    Need help setting up? Check the Setup Guide in the sidebar for step-by-step instructions.
    """)
    
    # Demo context
    st.caption("""
    This demo showcases the core capabilities of our AI-powered knowledge assistant. 
    For enterprise solutions and custom implementations, check out our services in the sidebar.
    """)

    st.image("assets/logo.png", use_container_width=True)

def show_footer():
    """Display the footer with links."""
    st.divider()
    footer_cols = st.columns([1, 4, 1])
    
    with footer_cols[1]:
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://github.com/williavs" target="_blank">
                <img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" height="28px"/>
            </a>&nbsp;
            <a href="https://www.linkedin.com/in/willyv3/" target="_blank">
                <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" height="28px"/>
            </a>&nbsp;
            <a href="https://v3-ai.com" target="_blank">
                <img src="https://img.shields.io/badge/V3_AI-FF4B4B?style=for-the-badge&logo=safari&logoColor=white" height="28px"/>
            </a>&nbsp;
            <a href="https://pmfeels.com" target="_blank">
                <img src="https://img.shields.io/badge/PM_Feels-4A154B?style=for-the-badge&logo=slack&logoColor=white" height="28px"/>
            </a>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Initialize session state (keep existing initialization code)
    initialize_session_state()
    
    # Show welcome section
    show_welcome()
    st.sidebar.image("assets/logo.png", use_container_width=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 🛠️ Need Custom Tools?
    
    This tool was built by [WillyV3](https://www.linkedin.com/in/willyv3/), founder of [V3 AI](https://v3-ai.com).
    We specialize in building custom data tools for:
    
    - 🎯 Go-to-Market Intelligence
    - 🔍 Lead Generation & Enrichment
    - 📊 Market Research Automation
    - 🤖 AI-Powered Data Processing
    - 🔄 Workflow Automation
    
    #### Featured Projects:
    - [V3 AI Platform](https://v3-ai.com) - Enterprise AI Solutions
    - [PM Feels](https://pmfeels.com) - Product Management Tools
    - [Sagedoc](https://sagedoc.me) - AI Documentation
    
    #### Let's Connect:
    [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/williavs)
    [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/willyv3/)
    """)
    
    
    # Add a divider before the main interface
    st.divider()
    
    # Keep all existing sections but wrap them in tabs for better organization
    tab1, tab2, tab3 = st.tabs(["🔑 Credentials", "📚 Documents", "🤖 Bot Control"])
    
    with tab1:
        st.header("🔑 Credentials")
        st.info("""
        Need help getting your credentials? 
        Check the 📚 Setup Guide in the sidebar for step-by-step instructions on how to:
        - Get your OpenAI API key
        - Create your Slack app
        - Configure the required permissions
        """)
        
        # OpenAI API Key
        col1, col2 = st.columns([3,1])
        with col1:
            openai_key = st.text_input(
                "OpenAI API Key", 
                value=st.session_state.credentials.get("OPENAI_API_KEY", ""),
                type="password",
                help="Your OpenAI API key (starts with 'sk-')"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
            st.markdown("[Get API Key](https://platform.openai.com/api-keys)")
        if openai_key:
            st.session_state.credentials["OPENAI_API_KEY"] = openai_key
        
        # Slack Bot Token
        slack_bot_token = st.text_input(
            "Slack Bot Token", 
            value=st.session_state.credentials.get("SLACK_BOT_TOKEN", ""),
            type="password",
            help="Your Slack Bot User OAuth Token (starts with 'xoxb-')"
        )
        if slack_bot_token:
            st.session_state.credentials["SLACK_BOT_TOKEN"] = slack_bot_token
        
        # Slack App Token
        slack_app_token = st.text_input(
            "Slack App Token", 
            value=st.session_state.credentials.get("SLACK_APP_TOKEN", ""),
            type="password",
            help="Your Slack App-Level Token (starts with 'xapp-')"
        )
        if slack_app_token:
            st.session_state.credentials["SLACK_APP_TOKEN"] = slack_app_token
        
        # Validate Button
        if st.button("Validate Credentials"):
            validation_results = validate_credentials()
            st.session_state.credentials_valid = validation_results
            
            if st.session_state.credentials_valid:
                st.success("All credentials are valid! ✅")
                initialize_systems()
            else:
                st.error("Invalid credentials. Please check the warnings and try again.")
    
    # Only show the rest if credentials are valid
    if st.session_state.credentials_valid:
        with tab2:
            st.header("📚 Document Management")
            handle_document_upload()
            display_documents()
            
        with tab3:
            st.header("🤖 Bot Control")
            
            # System Status
            st.subheader("📊 System Status")
            status_cols = st.columns(3)
            
            with status_cols[0]:
                st.metric(
                    "Credentials Status",
                    "Valid ✅" if st.session_state.credentials_valid else "Invalid ❌"
                )
            
            with status_cols[1]:
                st.metric(
                    "Bot Status",
                    "Running 🟢" if st.session_state.bot_running else "Stopped 🔴"
                )
            
            with status_cols[2]:
                st.metric(
                    "Documents",
                    len(st.session_state.documents)
                )
            
            # Advanced Settings (keep existing)
            with st.expander("🛠️ Advanced Settings - Customize Assistant Prompt"):
                if "custom_prompt" not in st.session_state:
                    st.session_state.custom_prompt = """<persona>
                    You are Patrick, a sophisticated AI assistant with the warmth of a close friend and the precision of a scholar. Your responses combine deep knowledge with genuine empathy, making complex information accessible and engaging.

                    Core Attributes:
                    - Charming and articulate, with a gift for clear explanation
                    - Deeply analytical while maintaining a warm, approachable tone
                    - Confident in your knowledge while staying humble
                    - Naturally weaves relevant information into conversational responses
                    </persona>

                    <context_processing>
                    1. Document Analysis:
                       - Carefully consider all provided document content
                       - Identify key themes and relevant details
                       - Recognize patterns across multiple documents
                       - Note the source and context of information

                    2. Web Search Integration:
                       - Extract current, factual information from web results
                       - Focus on authoritative sources
                       - Synthesize multiple perspectives
                       - Use specific details when available (dates, numbers, quotes)

                    3. Response Formation:
                       - Begin with the most relevant information
                       - Layer in supporting details naturally
                       - Maintain conversational flow
                       - Use formatting to enhance readability
                    </context_processing>

                    <output_guidelines>
                    - Start with a warm, engaging opener
                    - Present information clearly and logically
                    - Use bullet points for multiple pieces of information
                    - Include specific details while maintaining natural flow
                    - End with an invitation for further discussion
                    - Format appropriately for Slack
                    </output_guidelines>"""
                
                st.text_area(
                    "Customize Assistant Prompt",
                    value=st.session_state.custom_prompt,
                    height=400,
                    key="prompt_editor",
                    help="Customize the assistant's personality and behavior. Use XML tags to structure the prompt."
                )
                
                if st.button("Save Prompt"):
                    st.session_state.custom_prompt = st.session_state.prompt_editor
                    if st.session_state.rag_system:
                        st.session_state.rag_system.update_prompt(st.session_state.custom_prompt)
                    st.success("Prompt updated successfully! The assistant will use this personality in future responses.")
                
                if st.button("Reset to Default"):
                    st.session_state.prompt_editor = st.session_state.custom_prompt
                    if st.session_state.rag_system:
                        st.session_state.rag_system.reset_prompt()
                    st.success("Prompt reset to default Patrick personality.")
            
            # Bot Control Buttons
            control_cols = st.columns(2)
            
            with control_cols[0]:
                if not st.session_state.bot_running:
                    if st.button("Start Bot", use_container_width=True):
                        start_bot()
            
            with control_cols[1]:
                if st.session_state.bot_running:
                    if st.button("Stop Bot", use_container_width=True):
                        stop_bot()
    else:
        st.warning("Please validate your credentials to access the full functionality.")

    # Add footer at the end
    show_footer()

if __name__ == "__main__":
    main() 