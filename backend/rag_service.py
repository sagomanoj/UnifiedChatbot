import os
import shutil
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI, AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

# Persistence directory
FAISS_PATH = "./data/faiss_index"
MANUALS_DIR = "./data/user_manual"

class RAGService:
    def __init__(self):
        # Initialize Embeddings
        api_base = os.getenv("OPENAI_API_BASE")
        api_key = os.getenv("OPENAI_API_KEY")
        api_version = os.getenv("OPENAI_API_VERSION")
        deployment = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002")

        if api_base and "azure" in api_base:
             print(f"DEBUG: Initializing Azure OpenAI Embeddings...")
             print(f"DEBUG: Endpoint: {api_base}")
             print(f"DEBUG: Deployment: {deployment}")
             print(f"DEBUG: Version: {api_version}")

             # Unset to avoid conflicting pydantic validation in langchain/openai sdk
             if "OPENAI_API_BASE" in os.environ:
                 del os.environ["OPENAI_API_BASE"]
                 
             self.embeddings = AzureOpenAIEmbeddings(
                azure_deployment=deployment,
                openai_api_version=api_version,
                azure_endpoint=api_base,
                api_key=api_key
            )
             
             # Restore for other uses if needed (though we have variables now)
             os.environ["OPENAI_API_BASE"] = api_base
        else:
            self.embeddings = OpenAIEmbeddings()
        
        # Initialize Vector Store
        self.vector_store = None
        if os.path.exists(FAISS_PATH):
             try:
                self.vector_store = FAISS.load_local(FAISS_PATH, self.embeddings, allow_dangerous_deserialization=True)
             except Exception:
                 self.vector_store = None

    def ingest_document(self, file_path: str, app_name: str) -> int:
        """
        Ingests a document into the vector store with app-specific metadata.
        Returns the number of chunks added.
        """
        # Select loader based on extension
        lower_path = file_path.lower()
        if lower_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif lower_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path) # Default to text for others
        
        docs = loader.load()
        
        # Add metadata
        for doc in docs:
            doc.metadata["app"] = app_name
            doc.metadata["source"] = os.path.basename(file_path)

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)

        # Add to vector store
        if chunks:
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                self.vector_store.add_documents(chunks)
            
            # Save (FAISS needs explicit save)
            self.vector_store.save_local(FAISS_PATH)
        
        return len(chunks)

    def ingest_existing_manuals(self):
        """
        Scans data/user_manual for matching files and ingests them if not already present.
        """
        if not os.path.exists(MANUALS_DIR):
            return 0
            
        print("Scaning for user manuals...")
        count = 0
        for filename in os.listdir(MANUALS_DIR):
            file_path = os.path.join(MANUALS_DIR, filename)
            app_name = None
            
            # Determine App Context from Filename
            lower_name = filename.lower()
            if "food" in lower_name and "delivery" in lower_name:
                app_name = "Food Delivery"
            elif "ecommerce" in lower_name:
                app_name = "E-Commerce"
            elif "insurance" in lower_name:
                app_name = "Insurance Marketplace"
            elif "travel" in lower_name:
                app_name = "Travel Booking"
            
            if app_name:
                # Todo: Could add check to see if already ingested to avoid dupes,
                # but for POC, we will ingest. Cleaning existing index might be safer if we want fresh state.
                # For now, simplistic approach: Ingest.
                print(f"Auto-ingesting {filename} for {app_name}...")
                try:
                    self.ingest_document(file_path, app_name)
                    count += 1
                except Exception as e:
                    print(f"Failed to ingest {filename}: {e}")
        
        print(f"Auto-ingestion complete. Processed {count} manuals.")


    def query(self, question: str, app_name: str) -> str:
        """
        Queries the RAG system.
        """
        if self.vector_store is None:
            return "No documents have been uploaded yet."
        
        api_base = os.getenv("OPENAI_API_BASE")
        if api_base and "azure" in api_base:
             # Unset to avoid conflicting pydantic validation
            if "OPENAI_API_BASE" in os.environ:
                 del os.environ["OPENAI_API_BASE"]

            llm = AzureChatOpenAI(
                azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o"),
                openai_api_version=os.getenv("OPENAI_API_VERSION"),
                azure_endpoint=api_base,
                temperature=0
            )
            
            os.environ["OPENAI_API_BASE"] = api_base

        else:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # distinct prompt for comparison vs single app
        if app_name == "comparison":
            # Comparison Mode - pull more chunks to ensure we see all apps
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 10})
            
            template = """Analyze and compare how the following topic is handled across different application contexts (e.g., Food Delivery, E-Commerce, etc.) based on the provided documents.
            
            Topic: {question}
            
            Context:
            {context}
            
            Instructions:
            1. Differentiate the meaning or process for this topic within each application mentioned in the context.
            2. Comparison should be clear and highlight the specific differences.
            3. If an application is not mentioned in the context, do not make up information for it.
            """
        else:
            # Single Application Mode
            print(f"DEBUG: Querying for app '{app_name}' with question '{question}'")
            
            # Explicit similarity search to debug
            docs = self.vector_store.similarity_search(
                question, 
                k=4, 
                filter={"app": app_name}
            )
            
            print(f"DEBUG: Retrieved {len(docs)} docs")
            for i, d in enumerate(docs):
                print(f"DEBUG: Doc {i} source: {d.metadata.get('source')}")

            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": 4, 
                    "filter": {"app": app_name}
                }
            )
            
            template = """You are a helpful assistant for the {app_name} application.
            
            Context:
            {context}
            
            Question: {question}
            
            Instructions:
            1. Use the provided context to answer the question.
            2. If it's a greeting, respond politely.
            3. If the answer isn't in context and it's not a greeting, say you don't know.
            """

        prompt = ChatPromptTemplate.from_template(template)
        
        def format_docs(docs):
            res = "\n\n".join(doc.page_content for doc in docs)
            print(f"DEBUG: Formatted context length: {len(res)}")
            if len(res) > 0:
                print(f"DEBUG: Context snippet: {res[:200]}...")
            return res

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough(), "app_name": lambda x: app_name}
            | prompt
            | llm
            | (lambda x: x.content)
        )

        response = rag_chain.invoke(question)
        print(f"DEBUG: Final Response: {response}")
        return response

    def get_available_apps(self) -> List[str]:
        return ["Food Delivery", "E-Commerce", "Travel Booking", "Insurance Marketplace"]
