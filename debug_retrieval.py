import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_core.documents import Document

# Set up environment (mock if needed or rely on .env loading which we need to do manually here if running standalone)
import dotenv
dotenv.load_dotenv()

FAISS_PATH = "./data/faiss_index"

def debug_retrieval():
    print(f"Checking FAISS index at {FAISS_PATH}...")
    if not os.path.exists(FAISS_PATH):
        print("ERROR: FAISS index directory does not exist.")
        return

    # Check for index file
    if not os.path.exists(os.path.join(FAISS_PATH, "index.faiss")):
         print("ERROR: index.faiss not found.")
         return

    print("Loading vector store...")
    
    # Init embeddings (copy logic from rag_service roughly)
    api_base = os.getenv("OPENAI_API_BASE")
    if api_base and "azure" in api_base:
         print("Using Azure Embeddings configuration...")
         if "OPENAI_API_BASE" in os.environ: del os.environ["OPENAI_API_BASE"]
         embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002"),
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=api_base,
            api_key=os.getenv("OPENAI_API_KEY")
        )
         os.environ["OPENAI_API_BASE"] = api_base
    else:
        print("Using Standard OpenAI Embeddings...")
        embeddings = OpenAIEmbeddings()

    try:
        vector_store = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        print(f"Vector store loaded. Index count: {vector_store.index.ntotal}")
        
        # Determine available metadatas if possible (FAISS doesn't easily enumerate, but we can search broad)
        print("Testing retrieval for 'Food Delivery'...")
        # Search for generic term
        docs = vector_store.similarity_search("order food", k=5, filter={"app": "Food Delivery"})
        print(f"Found {len(docs)} documents for 'Food Delivery'.")
        for i, doc in enumerate(docs):
            print(f"--- Doc {i+1} ---")
            print(f"Source: {doc.metadata.get('source')}")
            print(f"App: {doc.metadata.get('app')}")
            print(f"Content Preview: {doc.page_content[:100]}...")
            
    except Exception as e:
        print(f"Error loading/querying FAISS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_retrieval()
