# vector_store.py

import os
import pickle
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document # To ensure compatibility if documents are loaded

# --- Configuration for Embeddings ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Required for embeddings.")

# The embedding model used when the FAISS index was originally built
# Ensure this matches the model used during index creation (e.g., 'models/embedding-001', 'text-embedding-004')
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "models/embedding-001")

try:
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL_NAME, google_api_key=GEMINI_API_KEY)
    print(f"Initialized Google Generative AI Embeddings with model: {EMBEDDING_MODEL_NAME}")
except Exception as e:
    print(f"Error initializing Google Generative AI Embeddings: {e}")
    embeddings = None # Set to None if initialization fails


# --- File Paths for FAISS Index and Split Documents ---
# Define the path to the FAISS index relative to this file's location for robustness.
FAISS_DIR = Path(__file__).resolve().parent / "faiss_index_data"


# --- Load FAISS Vector Store ---
vector_store = None
if embeddings:
    try:
        # Check if the FAISS index directory and its core files exist using pathlib
        if FAISS_DIR.exists() and \
           (FAISS_DIR / "index.faiss").exists() and \
           (FAISS_DIR / "index.pkl").exists():
            
            vector_store = FAISS.load_local(
                folder_path=str(FAISS_DIR), # FAISS expects a string path
                embeddings=embeddings,
                allow_dangerous_deserialization=True # Necessary for loading pickle files
            )
            print(f"Successfully loaded FAISS index from {FAISS_DIR}")
        else:
            print(f"FAISS index directory '{FAISS_DIR}' not found or incomplete. "
                  "Please ensure it exists and contains 'index.faiss' (your renamed faiss_index.bin) "
                  "and 'index.pkl' (your renamed split_documents.pkl).")
            # You might want to add logic here to re-build the index if it's missing,
            # or simply rely on the fallback below.

    except Exception as e:
        print(f"Error loading FAISS index from '{FAISS_DIR}': {e}")
        vector_store = None
else:
    print("Embeddings model not initialized. Cannot load FAISS vector store.")

# Provide a fallback vector store (e.g., an empty one or raising error on use)
# if the main one fails to load.
if vector_store is None:
    print("WARNING: Vector store could not be initialized. RAG functionality will be limited.")
    # Create a dummy vector store that always returns empty results or raises an error
    class DummyVectorStore:
        def similarity_search(self, query, k=1):
            print("WARNING: Dummy Vector Store used. No real search performed.")
            return [] # Always return empty list

    vector_store = DummyVectorStore()