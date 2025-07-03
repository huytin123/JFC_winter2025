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
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter


total_start_time = time.time()

model = SentenceTransformer('all-MiniLM-L6-v2')
pdf_folder = "./pdfs"
chunks = []
metadata = []

# CSV log file path
log_file = "build_times.csv"
pdf_character_counts = {}





def extract_text_chunks(pdf_path):
    chunk_list = []
    meta_list = []
    total_chars = 0
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            blocks = page.get_text("blocks")  # Get layout-based blocks
            block_texts = [b[4] for b in blocks if b[4].strip()]
            text = "\n".join(block_texts)
            total_chars += len(text)

            # Pre-clean formatting issues
            text = text.replace("●", "\n●")  # Newline before bullets
            text = re.sub(r'\.([^\s])', r'. \1', text)  # Add space after periods
            text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  # Break camel join
            text = re.sub(r'(?<!\n)\n(?!\n)', '\n', text)  # Normalize single newlines

            # Split into chunks
            chunks_for_page = splitter.split_text(text)
            for chunk in chunks_for_page:
                chunk_list.append(chunk.strip())
                meta_list.append({
                    "pdf": os.path.basename(pdf_path),
                    "page": page_num + 1,
                    "text": chunk.strip()
                })

    pdf_character_counts[os.path.basename(pdf_path)] = total_chars
    return chunk_list, meta_list


# ⏱️ Chunking
chunking_start_time = time.time()

num_pdfs = 0
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        num_pdfs += 1
        file_path = os.path.join(pdf_folder, filename)
        c, m = extract_text_chunks(file_path)
        chunks.extend(c)
        metadata.extend(m)
        print(f"Extracted {len(c)} chunks from: {filename}")

chunking_end_time = time.time()
print(f"⏱️ Chunking time: {chunking_end_time - chunking_start_time:.2f} seconds")

total_characters = sum(pdf_character_counts.values())
print(f"📝 Total characters across all PDFs: {total_characters}")

# 📝 Save all chunks to a text file for inspection
os.makedirs("index_files", exist_ok=True)
with open("index_files/all_chunks_dump.txt", "w", encoding="utf-8") as txt_file:
    for i, chunk in enumerate(chunks):
        meta = metadata[i]
        # Clean up chunk formatting
        cleaned = chunk.strip()

        # Add newline after bullets and punctuation for readability
        cleaned = re.sub(r'(?<=●)', '\n', cleaned)
        cleaned = re.sub(r'(?<=[.!?])\s+', '\n', cleaned)
        cleaned = re.sub(r'(?<!\n)\n(?!\n)', '\n', cleaned)  # Normalize single newlines

        # Extra spacing between sections
        txt_file.write(f"--- Chunk {i+1} | PDF: {meta['pdf']} | Page: {meta['page']} ---\n\n")
        txt_file.write(cleaned + "\n\n\n")


# ⏱️ Embedding
embedding_start_time = time.time()

batch_size = 8
embeddings = []
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
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

# ⏱️ FAISS Index Build
faiss_start_time = time.time()
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
faiss_end_time = time.time()
print(f"⏱️ FAISS build time: {faiss_end_time - faiss_start_time:.2f} seconds")

# ⏱️ Saving
saving_start_time = time.time()
faiss.write_index(index, "index_files/pdf_index.faiss")

with open("index_files/metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

with open("index_files/pdf_character_counts.csv", mode='w', newline='') as char_file:
    writer = csv.writer(char_file)
    writer.writerow(["PDF_Filename", "Num_Characters"])
    for pdf_file, char_count in pdf_character_counts.items():
        writer.writerow([pdf_file, char_count])

saving_end_time = time.time()
print(f"⏱️ Saving time: {saving_end_time - saving_start_time:.2f} seconds")

total_end_time = time.time()
total_time = total_end_time - total_start_time
print(f"✅ FAISS index and metadata saved with {len(chunks)} chunks.")
print(f"⏱️ Total build time: {total_time:.2f} seconds")

# ⏱️ Log Build Time
file_exists = os.path.isfile(log_file)
with open(log_file, mode='a', newline='') as csv_file:
    writer = csv.writer(csv_file)
    if not file_exists:
        writer.writerow(["Num_PDFs", "Num_Chunks", "Total_Characters",
                         "Chunking_Time_sec", "Embedding_Time_sec",
                         "FAISS_Build_sec", "Saving_sec", "Total_Build_sec"])
    writer.writerow([
        num_pdfs,
        len(chunks),
        total_characters,
        f"{chunking_end_time - chunking_start_time:.2f}",
        f"{embedding_end_time - embedding_start_time:.2f}",
        f"{faiss_end_time - faiss_start_time:.2f}",
        f"{saving_end_time - saving_start_time:.2f}",
        f"{total_time:.2f}"
    ])
print(f"📈 Build time logged in: {log_file}")

# 🧹 Clean-up
del embeddings
del metadata
del index
gc.collect()
