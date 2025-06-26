import os
import multiprocessing

# Force safer multiprocessing start (Mac-specific)
multiprocessing.set_start_method('spawn', force=True)

# Optional: Limit PyTorch threading to avoid crash on Mac
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import fitz  # PyMuPDF
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import time
import gc
import csv

total_start_time = time.time()

model = SentenceTransformer('all-MiniLM-L6-v2')
pdf_folder = "."
chunks = []
metadata = []

# CSV log file path
log_file = "build_times.csv"

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

# Timing: Chunking
chunking_start_time = time.time()

num_pdfs = 0
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        num_pdfs += 1
        c, m = extract_text_chunks(filename)
        chunks.extend(c)
        metadata.extend(m)
        print(f"Extracted {len(c)} chunks from: {filename}")

chunking_end_time = time.time()
print(f"⏱️ Chunking time: {chunking_end_time - chunking_start_time:.2f} seconds")

# Timing: Embedding
embedding_start_time = time.time()

batch_size = 8  # Adjust batch size for memory safety
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

embedding_end_time = time.time()
print(f"⏱️ Embedding time: {embedding_end_time - embedding_start_time:.2f} seconds")

# Timing: FAISS Index Build
faiss_start_time = time.time()
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
faiss_end_time = time.time()
print(f"⏱️ FAISS build time: {faiss_end_time - faiss_start_time:.2f} seconds")

# Timing: Saving
saving_start_time = time.time()
os.makedirs("index_files", exist_ok=True)
faiss.write_index(index, "index_files/pdf_index.faiss")

with open("index_files/metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)
saving_end_time = time.time()
print(f"⏱️ Saving time: {saving_end_time - saving_start_time:.2f} seconds")

total_end_time = time.time()
total_time = total_end_time - total_start_time
print(f"✅ FAISS index and metadata saved with {len(chunks)} chunks.")
print(f"⏱️ Total build time: {total_time:.2f} seconds")

# ✅ CSV Log Writing
file_exists = os.path.isfile(log_file)
with open(log_file, mode='a', newline='') as csv_file:
    writer = csv.writer(csv_file)
    if not file_exists:
        writer.writerow(["Num_PDFs", "Num_Chunks", "Chunking_Time_sec", "Embedding_Time_sec", "FAISS_Build_sec", "Saving_sec", "Total_Build_sec"])
    writer.writerow([
        num_pdfs,
        len(chunks),
        f"{chunking_end_time - chunking_start_time:.2f}",
        f"{embedding_end_time - embedding_start_time:.2f}",
        f"{faiss_end_time - faiss_start_time:.2f}",
        f"{saving_end_time - saving_start_time:.2f}",
        f"{total_time:.2f}"
    ])
print(f"📈 Build time logged in: {log_file}")

# Clean up big variables to reduce memory load
del embeddings
del metadata
del index
gc.collect()
