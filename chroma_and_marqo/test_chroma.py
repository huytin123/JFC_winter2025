import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
import pprint
import time
import csv
import os

# === Step 1: Read last row from build_times.csv ===
with open("build_times.csv", "r") as f:
    reader = list(csv.DictReader(f))
    last_row = reader[-1]
    total_documents = int(last_row["Total Documents"])
    total_characters = int(last_row["Total Characters"])

# === Step 2: Setup Chroma client and collection ===
chroma_client = chromadb.HttpClient(host='localhost', port=8000)
collection = chroma_client.get_collection(name="my_collection")

# === Step 3: Perform and time search queries ===
quiz = ["Processes of determining software quality"]
knn = 5

# First search
start = time.time()
collection.query(query_texts=quiz, n_results=knn)
first_search_time = time.time() - start

# Remaining 6 searches
other_times = []
for _ in range(6):
    start = time.time()
    collection.query(query_texts=quiz, n_results=knn)
    other_times.append(time.time() - start)

avg_search_time = sum(other_times) / len(other_times)

# === Step 4: Write results to record_search.csv ===
output_row = {
    "Total Documents": total_documents,
    "Total Characters": total_characters,
    "First Search Time": round(first_search_time, 4),
    "Avg of Other Search Times": round(avg_search_time, 4)
}

output_file = "record_search.csv"
file_exists = os.path.isfile(output_file)

with open(output_file, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=output_row.keys())
    if not file_exists:
        writer.writeheader()
    writer.writerow(output_row)

print("Search performance logged in record_search.csv")
