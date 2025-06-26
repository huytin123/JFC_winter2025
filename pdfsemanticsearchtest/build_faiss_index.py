import os
import multiprocessing

# Force safer multiprocessing start
multiprocessing.set_start_method('spawn', force=True)

# Optional: limit PyTorch threading to avoid crash on Mac
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import os
import fitz  # PyMuPDF
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import time

start_time = time.time()


model = SentenceTransformer('all-MiniLM-L6-v2')
pdf_folder = "."
chunks = []
metadata = []

def extract_text_chunks(pdf_path):
    chunk_list = []
    meta_list = []
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            for paragraph in text.split('\n\n'):
                paragraph = paragraph.strip()
                if paragraph:
                    chunk_list.append(paragraph)
                    meta_list.append({
                        "pdf": os.path.basename(pdf_path),
                        "page": page_num + 1,
                        "text": paragraph
                    })
    return chunk_list, meta_list

# Collect chunks and metadata
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        c, m = extract_text_chunks(filename)
        chunks.extend(c)
        metadata.extend(m)
        print(f"Extracted {len(c)} chunks from: {filename}")

# Embed in batches if you have many chunks (optional)
batch_size = 8  # you can reduce this if needed (e.g., 8 or 16)
embeddings = []
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    batch_embeddings = model.encode(
        batch,
        show_progress_bar=False,
        device='cpu',
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    embeddings.append(batch_embeddings)
embeddings = np.vstack(embeddings)

# Build and save FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

os.makedirs("index_files", exist_ok=True)
faiss.write_index(index, "index_files/pdf_index.faiss")

with open("index_files/metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

print(f"✅ FAISS index and metadata saved with {len(chunks)} chunks.")

end_time = time.time()
print(f"✅ FAISS index and metadata saved with {len(chunks)} chunks.")
print(f"⏱️ Total build time: {end_time - start_time:.2f} seconds")

import gc

# Manually delete big variables
del embeddings
del metadata
del index

gc.collect()