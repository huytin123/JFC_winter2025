from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')
sentences = ["Hello world", "FAISS test", "Segfault debug"]
embeddings = model.encode(sentences)

d = embeddings.shape[1]  # dimension
index = faiss.IndexFlatL2(d)
index.add(np.array(embeddings).astype('float32'))

D, I = index.search(np.array(embeddings).astype('float32'), k=2)
print("Distances:\n", D)
print("Indices:\n", I)
print("Test completed successfully!")
