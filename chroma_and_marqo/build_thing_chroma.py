import os
import time
import csv
import gc
import re
import multiprocessing
import fitz  # PyMuPDF
import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_store")  # New-style setup

from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Force safer multiprocessing start (Mac-specific)
multiprocessing.set_start_method('spawn', force=True)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# Init
first_start = time.time()
model = SentenceTransformer('all-MiniLM-L6-v2')
pdf_folder = "./pdf_folder"
document_list = []
id_list = []
pdf_character_counts = {}
log_file = "build_times.csv"

# Smart text chunking with formatting fixes
def extract_text_chunks(pdf_path):
    chunk_list = []
    id_local_list = []
    total_chars = 0
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            blocks = page.get_text("blocks")
            block_texts = [b[4] for b in blocks if b[4].strip()]
            text = "\n".join(block_texts)
            total_chars += len(text)

            # Formatting fixes
            text = text.replace("\u2022", "\n\u2022").replace("\u25CF", "\n\u25CF").replace("●", "\n●")
            text = re.sub(r'\.([^\s])', r'. \1', text)
            text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
            text = re.sub(r'(?<!\n)\n(?!\n)', '\n', text)

            # Chunk
            chunks = splitter.split_text(text)
            for idx, chunk in enumerate(chunks):
                chunk_list.append(chunk.strip())
                id_local_list.append(f"{os.path.basename(pdf_path)}_p{page_num+1}_c{idx+1}")

    pdf_character_counts[os.path.basename(pdf_path)] = total_chars
    return chunk_list, id_local_list

# Chunking loop
chunking_start_time = time.time()
num_pdfs = 0

for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        num_pdfs += 1
        path = os.path.join(pdf_folder, filename)
        chunks, ids = extract_text_chunks(path)
        document_list.extend(chunks)
        id_list.extend(ids)
        print(f"Extracted {len(chunks)} chunks from: {filename}")

chunking_end_time = time.time()
chunking_duration = chunking_end_time - chunking_start_time

# Character count
total_characters = sum(pdf_character_counts.values())
print(f"\n⏱️ Chunking time: {chunking_duration:.2f} seconds")
print(f"📝 Total characters: {total_characters}")

# Write chunks to file
os.makedirs("index_files", exist_ok=True)
with open("index_files/all_chunks_dump.txt", "w", encoding="utf-8") as f:
    for i, chunk in enumerate(document_list):
        cleaned = re.sub(r'(?<=●)', '\n', chunk.strip())
        cleaned = re.sub(r'(?<=[.!?])\s+', '\n', cleaned)
        cleaned = re.sub(r'(?<!\n)\n(?!\n)', '\n', cleaned)
        f.write(f"--- Chunk {i+1} | ID: {id_list[i]} ---\n\n{cleaned}\n\n\n")
print("✅ Saved formatted chunks to: index_files/all_chunks_dump.txt")

# Build ChromaDB (in-process)

build_start = time.time()


# Optional: Clear previous collection if needed
try:
    chroma_client.delete_collection(name="my_collection")
except:
    pass

collection = chroma_client.get_or_create_collection(name="my_collection")
collection.add(documents=document_list, ids=id_list)




build_time = time.time() - build_start
total_time = time.time() - first_start

print(f"⚙️ Build time: {build_time:.2f} sec")
print(f"🧭 Total time: {total_time:.2f} sec")

# CSV logging
header = ["Total PDFs", "Total Characters", "Chunking Time (s)", "Build Time (s)", "Total Time (s)"]
log_data = [num_pdfs, total_characters, round(chunking_duration, 2), round(build_time, 2), round(total_time, 2)]
file_exists = os.path.isfile(log_file)
with open(log_file, mode="a", newline="") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(header)
    writer.writerow(log_data)
print(f"📊 Log saved to: {log_file}")

# Clean-up
del document_list
del id_list
gc.collect()
