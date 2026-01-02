import os
print("Importing os...")
import sys
print("Importing sys...")

try:
    print("Importing FAISS...")
    from langchain_community.vectorstores import FAISS
    print("FAISS imported.")
except Exception as e:
    print(f"FAISS failed: {e}")

try:
    print("Importing Docx2txtLoader...")
    from langchain_community.document_loaders import Docx2txtLoader
    print("Docx2txtLoader imported.")
except Exception as e:
    print(f"Docx2txtLoader failed: {e}")

try:
    print("Importing backend.main...")
    from backend.main import app
    print("backend.main imported successfully.")
except Exception as e:
    print(f"backend.main import failed: {e}")
    import traceback
    traceback.print_exc()
