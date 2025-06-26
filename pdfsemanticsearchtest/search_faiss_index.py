import os
import multiprocessing

# Force safer multiprocessing start
multiprocessing.set_start_method('spawn', force=True)

# Optional: limit PyTorch threading to avoid crash on Mac
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

import time

start_time = time.time()

# Load FAISS index and metadata
index = faiss.read_index("index_files/pdf_index.faiss")
with open("index_files/metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Take user query

# Query loop
while True:
    query = input("\nEnter your semantic search query (or type 'exit' to quit): ").strip()
    
    if query.lower() == 'exit':
        print("👋 Exiting search.")
        break

    # Start timing the search
    search_start_time = time.time()

    # Embed the query
    query_vector = model.encode([query])

    # Search top 5 closest chunks
    D, I = index.search(np.array(query_vector), 5)

    print(f"\nTop 5 semantic matches for: '{query}'\n")

    for idx in I[0]:
        if idx == -1:
            continue
        result = metadata[idx]
        print(f"📄 PDF: {result['pdf']} | Page: {result['page']}")
        print(f"🔎 Snippet:\n{result['text']}\n---")

    search_end_time = time.time()
    print(f"⏱️ Search time: {search_end_time - search_start_time:.2f} seconds")