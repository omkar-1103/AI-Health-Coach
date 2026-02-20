import os
import pickle
import faiss
import pdfplumber
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. Paths
RAG_DIR = "rag"
DB_DIR = "data/health_rag_db"
INDEX_PATH = os.path.join(DB_DIR, "index.faiss")
DOCS_PATH = os.path.join(DB_DIR, "index.pkl")

# Ensure output directory exists
os.makedirs(DB_DIR, exist_ok=True)

# 2. Extract Text from PDF
print(f"Scanning {RAG_DIR} for PDFs...")
if not os.path.exists(RAG_DIR):
    print(f"Error: Directory {RAG_DIR} not found!")
    exit(1)

pdf_files = [f for f in os.listdir(RAG_DIR) if f.lower().endswith('.pdf')]

if not pdf_files:
    print(f"Error: No PDF files found in {RAG_DIR}!")
    exit(1)

text_chunks = []

for pdf_file in pdf_files:
    pdf_path = os.path.join(RAG_DIR, pdf_file)
    print(f"Reading from {pdf_path}...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    # Add source filename and page number to context
                    chunk = f"[Source: {pdf_file} | Page {i+1}] {text}"
                    
                    # Split by 500 chars to improve retrieval granularity
                    # Typically long medical texts
                    raw_chunks = [chunk[j:j+500] for j in range(0, len(chunk), 500)]
                    text_chunks.extend(raw_chunks)
    except Exception as e:
        print(f"Error reading {pdf_file}: {e}")

print(f"Extracted {len(text_chunks)} text chunks.")

if not text_chunks:
    print("No text extracted. Exiting.")
    exit(1)

# 3. Embed
print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Generating embeddings...")
embeddings = model.encode(text_chunks)

# 4. Index
print("Building FAISS index...")
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))

# 5. Save
print(f"Saving to {DB_DIR}...")
faiss.write_index(index, INDEX_PATH)
with open(DOCS_PATH, "wb") as f:
    pickle.dump(text_chunks, f)

print("✅ RAG Index Rebuilt Successfully!")
