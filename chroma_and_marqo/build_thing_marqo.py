import marqo
import pprint
import time
import os
from PyPDF2 import PdfReader
import fitz
import os
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import random


model = SentenceTransformer('all-MiniLM-L6-v2')
pdf_folder = "."
chunks = []
metadata = []

# CSV log file path
log_file = "build_times.csv"

def extract_text_chunks(pdf_path):
    chunk_list = []
    meta_list = []

    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                for paragraph in text.split('\n\n'):
                    paragraph = paragraph.strip()
                    if paragraph:
                        chunk_list.append(paragraph)
                        meta_list.append(
                            os.path.basename(pdf_path) + str(random.randint(100000, 999999))
                        )
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

    return chunk_list, meta_list

# Timing: Chunking
chunking_start_time = time.time()
pdf_data =[]
num_pdfs = 0
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        num_pdfs += 1
        c, m = extract_text_chunks(filename)
        for content, title in zip(c, m):
            pdf_data.append({
                "Title": title,
                "Description": content
            })
        print(f"Extracted {len(c)} chunks from: {filename}")
print(pdf_data[1])
chunking_end_time = time.time()
print(f" Chunking time: {chunking_end_time - chunking_start_time:.2f} seconds")


# def extract_pdf_info(folder="."):
#     pdf_data = []

#     for filename in os.listdir(folder):
#         if filename.lower().endswith(".pdf"):
#             filepath = os.path.join(folder, filename)
#             try:
#                 reader = PdfReader(filepath)

#                 # Extract title from metadata if available
#                 title = reader.metadata.title if reader.metadata and reader.metadata.title else filename

#                 # Extract content from all pages
#                 content = ""
#                 for page in reader.pages:
#                     content += page.extract_text() or ""

#                 pdf_data.append({
#                     "Title": title,
#                     "Description": content
#                 })

#             except Exception as e:
#                 print(f"Error reading {filename}: {e}")

#     return pdf_data


def index_exists(index_name="my-first-index"):
    indexes = mq.get_indexes()["results"]
    return any(idx["indexName"] == index_name for idx in indexes)

start = time.time()
#pdf_data =extract_pdf_info()
print ("total1", time.time() -start)

mq = marqo.Client(url='http://localhost:8882')

settings = {
   
    "model":"hf/multilingual-e5-large-instruct"
}
if index_exists():
    print(mq.index("my-first-index").delete())
start = time.time()
mq.create_index("my-first-index", **settings)
print("start inputing")

mq.index("my-first-index").add_documents(pdf_data,
    tensor_fields=["Description"]
)
print ("total", time.time() -start)