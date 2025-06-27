import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import pandas as pd 
import streamlit as st
import argparse

parser = argparse.ArgumentParser(description='Set the Chroma DB path to view collections')
parser.add_argument('db')

pd.set_option('display.max_columns', 4)

def view_collections(dir):
    st.markdown("### DB Path: %s" % dir)

    client = chromadb.HttpClient(host='localhost', port=8000)#chromadb.PersistentClient(path=dir)

    # This might take a while in the first execution if Chroma wants to download
    # the embedding transformer
    print(client.list_collections())

    st.header("Collections")
    print(client.list_collections())
    for collection in client.list_collections():
        data = collection.get()  # always specify limit

# Get base fields
        ids = data.get("ids", [])
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])

        # Ensure all lists are same length
        min_len = min(len(ids), len(documents), len(metadatas))

        # Trim all to the same length
        ids = ids[:min_len]
        documents = documents[:min_len]
        metadatas = metadatas[:min_len]

        # Flatten metadata if needed
        flat_metadata = []
        for meta in metadatas:
            if isinstance(meta, dict):
                flat_metadata.append(meta)
            else:
                flat_metadata.append({"metadata": meta})
        try:
            df = pd.DataFrame(flat_metadata)
            df.insert(0, "Document", documents)
            df.insert(0, "ID", ids)

            st.markdown(f"### Collection: **{collection.name}**")
            st.dataframe(df)

        except Exception as e:
            st.error(f"Failed to show collection {collection.name}: {e}")

if __name__ == "__main__":
    try:
        args = parser.parse_args()
        print("Opening database: %s" % args.db)
        view_collections(args.db)
    except:
        pass

