import logging
import threading
from typing import Dict

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from rag import RAGSystem, logger

class SlackBot:
    def __init__(self, rag_system, credentials):
        self.rag_system = rag_system
        self.credentials = credentials
        self.app = None
        self.handler = None
        self.thread = None
        self._running = False

    def _handle_direct_message(self, message, say):
        """Handle direct messages to the bot.
        
        Attempts to use the LangGraph workflow first, falls back to simple
        processing if needed.
        """
        try:
            logger.info(f"Received DM: {message['text']}")
            
            if not self.rag_system.is_initialized():
                logger.warning("RAG system not initialized")
                say("The knowledge base is not initialized. Please upload documents first.")
                return
            
            # Try LangGraph workflow first
            try:
                response = self.rag_system.process_query(message['text'])
                if response:
                    logger.info("Successfully used LangGraph workflow")
                    say(response)
                    return
            except Exception as e:
                logger.warning(f"LangGraph workflow failed, falling back to simple processing: {str(e)}")
            
            # Fallback to simple processing
            response = self.rag_system.process_message(message['text'])
            logger.info("Used fallback processing")
            say(response)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            say("I encountered an error processing your message. Please try again.")

    def start(self) -> bool:
        """Start the Slack bot."""
        try:
            if not self.rag_system.is_initialized():
                logger.error("Cannot start bot: RAG system not initialized")
                return False

            # Create the Bolt app
            self.app = App(token=self.credentials["SLACK_BOT_TOKEN"])
            
            # Register message handler
            @self.app.message("")
            def message_handler(message, say):
                self._handle_direct_message(message, say)
            
            # Create socket mode handler
            self.handler = SocketModeHandler(
                app=self.app,
                app_token=self.credentials["SLACK_APP_TOKEN"]
            )
            
            # Start in a separate thread
            self.thread = threading.Thread(target=self.handler.start)
            self.thread.daemon = True
            self.thread.start()
            
            self._running = True
            logger.info("Slack bot started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Slack bot: {str(e)}")
            self._running = False
            self.cleanup()
            return False

    def stop(self) -> bool:
        """Stop the Slack bot."""
        try:
            self.cleanup()
            logger.info("Slack bot stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Error stopping Slack bot: {str(e)}")
            return False

    def cleanup(self):
        """Clean up bot resources."""
        if self.handler:
            self.handler.close()
            self.handler = None
        self.app = None
        self.thread = None
        self._running = False

    def is_running(self) -> bool:
        """Check if the bot is running."""
        return self._running and self.thread and self.thread.is_alive()

    def register_listeners(self):
        """Register all event listeners."""
        
        # Handle direct messages
        @self.app.message("")
        def handle_message(message, say, ack):
            ack()
            # Ignore messages from the bot itself
            if "bot_id" in message:
                return
                
            user_query = message["text"]
            logger.info(f"Received DM: {user_query}")
            self._process_query(user_query, say, message)

        # Handle mentions
        @self.app.event("app_mention")
        def handle_mention(event, say):
            text = event["text"].split(">", 1)[1].strip()
            logger.info(f"Received mention: {text}")
            self._process_query(text, say, event)

        # Handle app home opened
        @self.app.event("app_home_opened")
        def handle_app_home_opened(event, client):
            logger.info(f"App home opened by user: {event['user']}")
            # You could update the home tab here if needed

    def _process_query(self, query: str, say, message):
        """Process a query and send response."""
        if self.rag_system.is_ready():
            try:
                response = self.rag_system.process_query(query)
                logger.info(f"Sending response: {response}")
                say(text=response, thread_ts=message.get("thread_ts", message.get("ts")))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                say(text="Sorry, I couldn't process your request. Please try again.", 
                    thread_ts=message.get("thread_ts", message.get("ts")))
        else:
            logger.warning("RAG system not initialized")
            say(text="The knowledge base is not initialized. Please upload documents first.",
                thread_ts=message.get("thread_ts", message.get("ts")))

    def is_ready(self) -> bool:
        """Check if the bot is ready to process messages."""
        return self.rag_system.is_ready() and all([
            self.credentials["SLACK_BOT_TOKEN"].startswith("xoxb-"),
            self.credentials["SLACK_APP_TOKEN"].startswith("xapp-")
        ]) 