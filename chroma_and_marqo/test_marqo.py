import marqo
import pprint
import time
mq = marqo.Client(url='http://localhost:8882')
settings = {
   
    "model":"hf/multilingual-e5-large-instruct"
}
#mq.create_index("my-first-index", **settings)

# mq.index("my-first-index").add_documents([
#     {
#         "Title": "The Travels of Marco Polo",
#         "Description": "A 13th-century travelogue describing Polo's travels"
#     }, 
#     {
#         "Title": "Extravehicular Mobility Unit (EMU)",
#         "Description": "The EMU is a spacesuit that provides environmental protection, "
#                        "mobility, life support, and communications for astronauts",
#         "_id": "article_591"
#     }],
#     tensor_fields=["Description"]
# )
start = time.time()
print ("start", time.time())
results = mq.index("my-first-index").search(
    q="What is the best outfit to wear on the moon?"
)
print ("total", time.time() -start)
pprint.pprint(results)