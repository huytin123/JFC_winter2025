import pprint
import time
import os
from PyPDF2 import PdfReader
import fitz
from sentence_transformers import SentenceTransformer
import random
from opensearchpy import OpenSearch
import csv

first_start = time.time()
model = SentenceTransformer('all-MiniLM-L6-v2')
pdf_folder = "./pdf_folder"
chunks = []
metadata = []

# CSV log file path
log_file = "record_time.csv"

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
file_list = []
id_list = []

for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        num_pdfs += 1
        filepath = os.path.join(pdf_folder, filename)
        c, m = extract_text_chunks(filepath)
        document_list.extend(c)
        id_list.extend(m)
        file_list.extend(filename)
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
client = OpenSearch(host='localhost', port=9200)

index_name = 'python-test-index'
index_body = {
    "settings": {
        "index": {
            "knn": True,
        }
    },
    "mappings": {
        "properties": {
            "name": {"type": "text"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 384,
            },
        }
    },
}

try:
    client.indices.delete(index=index_name)
except Exception as e:
    pass

response = client.indices.create(index=index_name, body=index_body)
print('\nCreating index:')
print(response)



for i in range(len(id_list)):
    response = client.index(
        index = index_name,
        body = {"name": file_list[i],"embedding":model.encode(document_list[i])},
        id = id_list[i],
        refresh = True
    )

build_time = time.time() - start
total_time = time.time() - first_start

print("Build time:", build_time)

# Search
start = time.time()
text = "Processes of determining software quality"
mean_pooled = model.encode(text)

query = {
    "size": 3,
    "query": {"knn": {"embedding": {"vector": mean_pooled, "k": 5}}},
    "_source": False,
    "fields": ["name"]
}

response = client.search(body=query, index=index_name)
print(response["hits"]["hits"])

search_time = time.time() - start
print("Search time:", search_time + search_time)

print("Total time:", total_time + search_time)

# Write log to CSV
header = ["Total Documents", "Total Characters", "Chunking Time (s)", "Build Time (s)", "Search Time (s)", "Total Time (s)"]
log_data = [num_pdfs, total_characters, round(chunking_duration, 2), round(build_time, 2), round(search_time, 4), round(total_time, 2)]

# Create file with header if not exist
file_exists = os.path.isfile(log_file)
with open(log_file, mode="a", newline="") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(header)
    writer.writerow(log_data)
    
