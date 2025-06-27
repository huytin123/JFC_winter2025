import marqo
import pprint
import time
import os
from PyPDF2 import PdfReader
import fitz
from sentence_transformers import SentenceTransformer
import random
import chromadb
import csv

first_start = time.time()
model = SentenceTransformer('all-MiniLM-L6-v2')
pdf_folder = "./pdf_folder"
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
            para_count =0
            for paragraph in text.split('\n\n'):
                para_count =para_count+1
                paragraph = paragraph.strip()
                if paragraph:
                    chunk_list.append(paragraph)
                    meta_list.append(
                        os.path.basename(pdf_path) +str( page_num + 1)+ str(para_count)
                    )
    return chunk_list, meta_list

# Timing: Chunking
chunking_start_time = time.time()
pdf_data = []
num_pdfs = 0
document_list = []
id_list = []

for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        num_pdfs += 1
        filepath = os.path.join(pdf_folder, filename)
        c, m = extract_text_chunks(filepath)
        document_list.extend(c)
        id_list.extend(m)
        print(f"Extracted {len(c)} chunks from: {filepath}")

chunking_end_time = time.time()
chunking_duration = chunking_end_time - chunking_start_time
total_characters = sum(len(doc) for doc in document_list)


print(f" Chunking time: {chunking_duration:.2f} seconds")
print(f" Total characters: {total_characters}")
print(type(document_list))
print(type(document_list[0]))

# Build
start = time.time()
chroma_client = chromadb.HttpClient(host='localhost', port=8000)

try:
    chroma_client.delete_collection(name="my_collection")
    #collection = chroma_client.get_or_create_collection(name="my_collection")
except Exception as e:
    pass
collection = chroma_client.get_or_create_collection(name="my_collection")

collection.add(
    documents=document_list,
    ids=id_list,
)

build_time = time.time() - start
total_time = time.time() - first_start

print("Build time:", build_time)
print("Total time:", total_time)

# Write log to CSV
header = ["Total Documents", "Total Characters", "Chunking Time (s)", "Build Time (s)", "Total Time (s)"]
log_data = [num_pdfs, total_characters, round(chunking_duration, 2), round(build_time, 2), round(total_time, 2)]

# Create file with header if not exist
file_exists = os.path.isfile(log_file)
with open(log_file, mode="a", newline="") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(header)
    writer.writerow(log_data)
