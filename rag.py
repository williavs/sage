import logging
import os
from typing import Any, Dict, List, TypedDict, Union
from io import BytesIO
import tempfile
import fitz  # PyMuPDF import

from googleapiclient.discovery import build
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.pydantic_v1 import BaseModel
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import END, StateGraph


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, documents: Dict[str, bytes], credentials: Dict[str, str]):
        """Initialize the VectorStoreManager with documents and credentials."""
        self.documents = {}
        self.vectorstore = None
        self.embeddings = OpenAIEmbeddings(api_key=credentials["OPENAI_API_KEY"])
        
        # Store documents
        for filename, content in documents.items():
            if isinstance(content, bytes):
                self.documents[filename] = content
                logger.info(f"Stored document: {filename}")
            else:
                logger.error(f"Invalid content type for {filename}: {type(content)}")
        
        logger.info(f"VectorStoreManager initialized with {len(self.documents)} documents")

    def process_pdf_content(self, content: bytes, filename: str) -> List[Document]:
        """Process PDF content into Documents using PyMuPDF."""
        try:
            # Create document from bytes
            pdf_document = fitz.open(stream=content, filetype="pdf")
            total_pages = len(pdf_document)
            logger.info(f"Processing PDF {filename} with {total_pages} pages")
            
            documents = []
            for page_num in range(total_pages):
                try:
                    # Get the page
                    page = pdf_document[page_num]
                    # Extract text from the page
                    text = page.get_text("text")
                    
                    if text.strip():  # Only create document if text is not empty
                        doc = Document(
                            page_content=text,
                            metadata={
                                "source": filename,
                                "page": page_num + 1,
                                "total_pages": total_pages
                            }
                        )
                        documents.append(doc)
                        logger.info(f"Successfully processed page {page_num + 1} of {filename}")
                    else:
                        logger.warning(f"Empty text on page {page_num + 1} of {filename}")
                        
                except Exception as e:
                    logger.error(f"Error processing page {page_num + 1} of {filename}: {str(e)}")
                    continue
            
            pdf_document.close()
            return documents
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {str(e)}")
            return []

    def reset(self):
        self.vectorstore = None
        logger.info("VectorStore reset")

    def process_text_content(self, content: bytes, filename: str) -> Document:
        """Process text content into a Document."""
        try:
            text = content.decode('utf-8')
            return Document(
                page_content=text,
                metadata={"source": filename}
            )
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding {filename}: {e}")
            return None

    def load_documents(self) -> List[Document]:
        """Load all documents from memory into Document objects."""
        all_documents = []
        
        if not self.documents:
            logger.warning("No documents to process")
            return all_documents
            
        for filename, content in self.documents.items():
            logger.info(f"Processing document: {filename}")
            
            if not isinstance(content, bytes):
                logger.error(f"Invalid content type for {filename}: {type(content)}")
                continue
                
            try:
                # Process based on file extension
                if filename.lower().endswith('.pdf'):
                    # Handle PDFs with PyMuPDF
                    pdf_docs = self.process_pdf_content(content, filename)
                    if pdf_docs:
                        all_documents.extend(pdf_docs)
                        logger.info(f"Successfully processed PDF: {filename} ({len(pdf_docs)} pages)")
                    else:
                        logger.warning(f"Failed to process PDF: {filename}")
                
                elif filename.lower().endswith(('.txt', '.csv')):
                    # Handle text files directly
                    doc = self.process_text_content(content, filename)
                    if doc:
                        all_documents.append(doc)
                        logger.info(f"Successfully processed text file: {filename}")
                    else:
                        logger.warning(f"Failed to process text file: {filename}")
                
                else:
                    logger.warning(f"Unsupported file type: {filename}")
                    
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                continue
        
        num_docs = len(all_documents)
        if num_docs > 0:
            logger.info(f"Successfully loaded {num_docs} documents")
        else:
            logger.warning("No documents were successfully loaded")
            
        return all_documents

    def create_vectorstore(self) -> bool:
        """Create a vector store from the loaded documents."""
        try:
            docs = self.load_documents()
            if not docs:
                logger.warning("No documents were loaded")
                return False

            logger.info("Splitting documents into chunks...")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(docs)
            logger.info(f"Created {len(splits)} chunks from {len(docs)} documents")

            logger.info("Creating vector store...")
            self.vectorstore = FAISS.from_documents(splits, self.embeddings)
            logger.info("Vector store created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            return False

    def search_local_documents(self, query: str) -> List[Document]:
        """Search the vector store for relevant documents."""
        if self.vectorstore:
            # Use hybrid search approach
            results = []
            
            # Get more results with MMR for diversity
            mmr_results = self.vectorstore.max_marginal_relevance_search(
                query,
                k=20,  # Get more chunks
                fetch_k=40,  # Consider more candidates
                lambda_mult=0.5  # Increase diversity
            )
            results.extend(mmr_results)
            
            # Also get similarity results
            similarity_results = self.vectorstore.similarity_search(
                query,
                k=10,
                score_threshold=0.5  # Lower threshold to get more matches
            )
            
            # Combine results, removing duplicates
            seen_contents = {doc.page_content for doc in results}
            for doc in similarity_results:
                if doc.page_content not in seen_contents:
                    results.append(doc)
                    seen_contents.add(doc.page_content)
            
            # Log retrieved content
            logger.info(f"Retrieved {len(results)} total documents")
            for doc in results:
                logger.info(f"Source: {doc.metadata.get('source')}, Page: {doc.metadata.get('page')}")
                logger.info(f"Content preview: {doc.page_content[:200]}...")
            
            return results
        return []


class VerboseHandler(BaseCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        logger.info(f"RAGSystem: Starting tool: {serialized['name']}")
        logger.info(f"RAGSystem: Tool input: {input_str}")

    def on_tool_end(self, output, **kwargs):
        logger.info(f"RAGSystem: Tool output: {output}")

    def on_chain_start(self, serialized, inputs, **kwargs):
        logger.info(f"RAGSystem: Starting chain: {serialized['name']}")
        logger.info(f"RAGSystem: Chain input: {inputs}")

    def on_chain_end(self, outputs, **kwargs):
        logger.info(f"RAGSystem: Chain output: {outputs}")


class DocumentWithGrade(BaseModel):
    content: str
    grade: str


class GraphState(TypedDict):
    query: str
    documents: List[Document]
    graded_documents: List[DocumentWithGrade]
    rewritten_query: str
    web_results: List[dict]
    answer: str


class RAGSystem:
    def __init__(self, documents: Dict[str, bytes], credentials: Dict[str, str]):
        self.documents = documents
        self.credentials = credentials
        self.vectorstore_manager = VectorStoreManager(documents, credentials)
        self.llm = ChatOpenAI(model_name="gpt-4", api_key=credentials["OPENAI_API_KEY"])
        self.workflow = None
        self._initialized = False
        self._default_prompt = """<persona>
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
        self._current_prompt = self._default_prompt

    def update_prompt(self, new_prompt: str) -> None:
        """Update the assistant's prompt template."""
        logger.info("Updating assistant prompt template")
        self._current_prompt = new_prompt

    def reset_prompt(self) -> None:
        """Reset the prompt to the default Patrick personality."""
        logger.info("Resetting assistant prompt to default")
        self._current_prompt = self._default_prompt

    def initialize_system(self) -> bool:
        """Initialize the RAG system with documents."""
        try:
            logger.info(f"Initializing RAG system with documents from: {self.documents}")
            if self.vectorstore_manager.create_vectorstore():
                logger.info("Successfully created vector store")
                self.workflow = self.create_workflow()
                self._initialized = True
                return True
            else:
                logger.warning("No documents were processed into the vector store")
                self._initialized = False
                return False
        except Exception as e:
            logger.error(f"Error initializing RAG system: {str(e)}")
            self._initialized = False
            return False

    def is_initialized(self) -> bool:
        """Check if the RAG system is initialized."""
        return (self._initialized and 
                self.vectorstore_manager and 
                self.vectorstore_manager.vectorstore is not None)

    def google_search(self, search_term: str, num_results: int = 3) -> list:
        service = build("customsearch", "v1", developerKey=self.credentials["GOOGLE_API_KEY"])
        res = service.cse().list(q=search_term, cx=self.credentials["GOOGLE_CSE_ID"], num=num_results).execute()
        items = res.get("items", [])
        return [{"title": item["title"], "snippet": item["snippet"], "link": item["link"]} for item in items]

    def retrieve_documents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Bridge between vectorstore and LangGraph workflow.
        
        Uses our working vectorstore_manager to retrieve documents and integrate
        with the LangGraph workflow.
        """
        try:
            query = state["query"]
            logger.info(f"Retrieving documents for query: {query}")
            
            # Use our working vectorstore search
            docs = self.vectorstore_manager.search_local_documents(query)
            
            if docs:
                # Log the actual content being retrieved
                for doc in docs:
                    logger.info(f"Retrieved document content: {doc.page_content[:100]}...")
                logger.info(f"Found {len(docs)} relevant documents")
            else:
                logger.info("No relevant documents found")
            
            return {
                "query": query,
                "documents": docs,
                "web_results": []  # Initialize for potential web search
            }
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return {
                "query": state["query"],
                "documents": [],
                "web_results": []
            }

    def grade_documents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Grade the relevance of documents to the query."""
        question = state["query"]
        documents = state.get("documents", [])
        
        if not documents:
            return {
                "query": question,
                "documents": [],
                "web_search_needed": "Yes"
            }

        # Keep all documents by default, only filter out completely irrelevant ones
        filtered_docs = []
        for doc in documents:
            # Extract key terms from document
            doc_text = doc.page_content.lower()
            query_terms = set(question.lower().split())
            
            # Check if document contains any query terms or is from first few pages
            is_relevant = (
                doc.metadata.get("page", 0) <= 5 or  # Keep intro pages
                any(term in doc_text for term in query_terms) or  # Contains query terms
                "spiritual" in doc_text or "machine" in doc_text or  # Topic-specific terms
                "consciousness" in doc_text or "intelligence" in doc_text  # Related concepts
            )
            
            if is_relevant:
                filtered_docs.append(doc)
                logger.info(f"Keeping relevant document from page {doc.metadata.get('page')}")
            else:
                logger.info(f"Filtering out document from page {doc.metadata.get('page')}")

        web_search_needed = "Yes" if len(filtered_docs) < 5 else "No"
        
        return {
            "query": question,
            "documents": filtered_docs,
            "web_search_needed": web_search_needed
        }

    def rewrite_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state["query"]
        rewritten_query = self.llm.predict(
            f"Rewrite this query for web search to find the most relevant information: {query}"
        )
        return {"query": query, "rewritten_query": rewritten_query}

    def web_search(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("rewritten_query", state["query"])
        try:
            search_results = self.google_search(query)
        except Exception as e:
            logger.error(f"Web search error: {e}")
            search_results = []
        return {"query": state["query"], "web_results": search_results}

    def generate_answer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state["query"]
        documents = state.get("documents", [])
        web_results = state.get("web_results", [])

        if not isinstance(documents, list):
            documents = []
        if not isinstance(web_results, list):
            web_results = []

        # Enhanced context preparation with metadata and better organization
        doc_contexts = []
        seen_pages = set()  # Track unique pages to avoid duplicates
        
        # Group documents by source
        docs_by_source = {}
        for doc in documents:
            metadata = doc.metadata
            source = metadata.get("source", "Unknown")
            if source not in docs_by_source:
                docs_by_source[source] = []
            docs_by_source[source].append(doc)

        # Process each source's documents
        for source, docs in docs_by_source.items():
            source_contexts = []
            for doc in sorted(docs, key=lambda x: x.metadata.get("page", 0)):
                page = doc.metadata.get("page", "N/A")
                page_key = f"{source}-{page}"
                if page_key not in seen_pages:  # Avoid duplicate pages
                    seen_pages.add(page_key)
                    source_contexts.append(f"[Page {page}]: {doc.page_content.strip()}")
            
            if source_contexts:
                doc_contexts.append(f"Source: {source}\n" + "\n\n".join(source_contexts))

        # Join all contexts with clear separation
        doc_context = "\n\n---\n\n".join(doc_contexts) if doc_contexts else "No relevant documents found."
        
        # Enhanced web results formatting
        web_context = ""
        if web_results:
            web_contexts = []
            for i, result in enumerate(web_results, 1):
                web_contexts.append(
                    f"[Result {i}]\n"
                    f"Title: {result['title']}\n"
                    f"Content: {result['snippet']}\n"
                    f"URL: {result.get('link', 'N/A')}"
                )
            web_context = "\n\n".join(web_contexts)
        else:
            web_context = "No web results available."

        # Log the contexts being used
        logger.info(f"Document context length: {len(doc_context)}")
        logger.info(f"Number of unique pages: {len(seen_pages)}")
        logger.info(f"Web context length: {len(web_context)}")

        prompt = f"""{self._current_prompt}

<input>
Question: {query}

Document Context:
{doc_context}

Web Results:
{web_context}
</input>

<CURRENT_CURSOR_POSITION>
Please provide your response:</prompt>"""

        answer = self.llm.predict(prompt)
        return {
            "query": query,
            "documents": documents,
            "web_results": web_results,
            "answer": answer
        }

    def decide_next_step(self, state: Dict[str, Any]) -> str:
        """Decide whether to perform web search based on document relevance and query type."""
        web_search_needed = state.get("web_search_needed", "No")
        documents = state.get("documents", [])
        query = state.get("query", "").lower()

        # Always do web search if:
        # 1. No relevant documents found
        # 2. Explicitly marked as needed by document grading
        # 3. Query suggests current/comparative information needed
        # 4. Less than 3 relevant documents found
        should_web_search = (
            not documents or
            web_search_needed == "Yes" or
            len(documents) < 3 or
            any(keyword in query for keyword in [
                "latest", "recent", "current", "new",
                "compare", "vs", "versus", "difference",
                "review", "today", "now", "update"
            ])
        )

        if should_web_search:
            logger.info("Deciding to perform web search due to insufficient document context")
            return "rewrite"
        
        logger.info("Document context sufficient, proceeding to generate response")
        return "generate"

    def create_workflow(self):
        workflow = StateGraph(GraphState)

        workflow.add_node("retrieve", self.retrieve_documents)
        workflow.add_node("grade", self.grade_documents)
        workflow.add_node("rewrite", self.rewrite_query)
        workflow.add_node("web_search", self.web_search)
        workflow.add_node("generate", self.generate_answer)

        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "grade")
        workflow.add_conditional_edges("grade", self.decide_next_step, {"rewrite": "rewrite", "generate": "generate"})
        workflow.add_edge("rewrite", "web_search")
        workflow.add_edge("web_search", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    def reset_system(self):
        self.vectorstore_manager.reset()
        self.workflow = None

    def process_query(self, query: str) -> str:
        if not self.is_initialized():
            logger.warning("RAG system not initialized. Please upload documents first.")
            return "The knowledge base is not initialized. Please upload documents first."
        try:
            logger.info(f"RAGSystem: Received query: {query}")
            response = self.workflow.invoke({"query": query})
            logger.info(f"RAGSystem: Generated response: {response}")
            return response.get("answer", "Sorry, I couldn't generate an answer.")
        except Exception as e:
            logger.error(f"RAGSystem: An error occurred: {e}")
            return f"I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists." 