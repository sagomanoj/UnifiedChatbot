import os
import shutil
import json
from typing import List, Optional, Dict
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
APPS_CONF = "./data/apps.json"

class RAGService:
    def __init__(self):
        # Initialize Embeddings
        api_base = os.getenv("OPENAI_API_BASE")
        api_key = os.getenv("OPENAI_API_KEY")
        api_version = os.getenv("OPENAI_API_VERSION")
        deployment = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002")

        if api_base and "azure" in api_base:
             print(f"DEBUG: Initializing Azure OpenAI Embeddings...")
             # Unset to avoid conflicting pydantic validation in langchain/openai sdk
             if "OPENAI_API_BASE" in os.environ:
                 del os.environ["OPENAI_API_BASE"]
                 
             self.embeddings = AzureOpenAIEmbeddings(
                azure_deployment=deployment,
                openai_api_version=api_version,
                azure_endpoint=api_base,
                api_key=api_key
            )
             
             # Restore for other uses if needed
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
                 
        self._load_apps()
        
    def _load_apps(self):
        if os.path.exists(APPS_CONF):
            try:
                with open(APPS_CONF, "r") as f:
                    self.apps = json.load(f)
            except:
                self.apps = []
        else:
            self.apps = []

    def _save_apps(self):
        with open(APPS_CONF, "w") as f:
            json.dump(self.apps, f, indent=4)

    def get_available_apps(self) -> List[str]:
        return [app["name"] for app in self.apps]
    
    def get_apps_full(self) -> List[Dict]:
        return self.apps

    def add_app(self, app_name: str):
        if any(a["name"] == app_name for a in self.apps):
            return
        self.apps.append({"name": app_name, "manual": None})
        self._save_apps()

    def delete_app(self, app_name: str):
        self.apps = [a for a in self.apps if a["name"] != app_name]
        self._save_apps()
        # In this POC, we don't actually delete chunks from FAISS because it's non-trivial.
        # But filtering in query() handles it.

    def ingest_document(self, file_path: str, app_name: str, clear_existing: bool = False) -> int:
        lower_path = file_path.lower()
        if lower_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif lower_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path)
        
        docs = loader.load()
        for doc in docs:
            doc.metadata["app"] = app_name
            doc.metadata["source"] = os.path.basename(file_path)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)

        if chunks:
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                self.vector_store.add_documents(chunks)
            
            self.vector_store.save_local(FAISS_PATH)
            
            # Update app manual link
            for app in self.apps:
                if app["name"] == app_name:
                    app["manual"] = os.path.basename(file_path)
            self._save_apps()
        
        return len(chunks)

    def ingest_existing_manuals(self):
        # We'll just rely on the existing indexes for now.
        pass

    def query(self, question: str, app_name: str) -> str:
        if self.vector_store is None:
            return "No documents have been uploaded yet."
        
        api_base = os.getenv("OPENAI_API_BASE")
        if api_base and "azure" in api_base:
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

        if app_name == "comparison":
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 10})
            template = """Analyze and compare how the following topic is handled across different application contexts based on the provided documents.
            
            Topic: {question}
            Context: {context}
            
            Instructions:
            1. Differentiate the meaning or process for this topic within each application.
            2. Comparison should be clear.
            3. If an application is not mentioned in the context, do not make up information.
            """
        else:
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 4, "filter": {"app": app_name}})
            template = """You are a helpful assistant for the {app_name} application.
            Context: {context}
            Question: {question}
            
            Instructions:
            1. Use the provided context to answer the question.
            2. If it's a greeting, respond politely.
            3. If the answer isn't in context and it's not a greeting, say you don't know.
            """

        prompt = ChatPromptTemplate.from_template(template)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough(), "app_name": lambda x: app_name}
            | prompt
            | llm
            | (lambda x: x.content)
        )

        return rag_chain.invoke(question)
