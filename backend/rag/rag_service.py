import pickle
import faiss
import os
import streamlit as st
from sentence_transformers import SentenceTransformer

# Load FAISS index + docs (Cached to prevent reloading)
@st.cache_resource
def load_rag_db():
    base_path = "data/health_rag_db"
    index_path = os.path.join(base_path, "index.faiss")
    docs_path = os.path.join(base_path, "index.pkl")

    if not os.path.exists(index_path) or not os.path.exists(docs_path):
        return None, []

    index = faiss.read_index(index_path)
    with open(docs_path, "rb") as f:
        documents = pickle.load(f)
    
    return index, documents

# Load Model (Cached)
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

# Search function
def rag_search(query, top_k=3):
    index, documents = load_rag_db()
    
    if index is None or not documents:
        return []

    model = load_embedding_model()
    query_vector = model.encode([query])
    D, I = index.search(query_vector, top_k)

    results = []
    for idx in I[0]:
        if idx < len(documents):
            results.append(documents[idx])

    return results
