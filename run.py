import wx
from noname import MyFrame1
from typing_extensions  import override
import fitz
import os
import chromadb

class MyFrame(MyFrame1):
    def __init__(self, collection):
        super().__init__(None)
        self.collection = collection
        self.pdf_fetch(None)
        
    @override
    def pdf_add( self, event ):
        with wx.FileDialog(self, "Open PDF file", wildcard="PDF files (*.pdf)|*.pdf",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = fileDialog.GetPath()
            
            name = fileDialog.GetFilename()
            docs, ids = extract_text_chunks(pathname)
            metas = [{"Name": name}] * len(ids)
            self.collection.add(
                documents=docs,
                ids=ids,
                metadatas=metas,
            )
            
            self.dvc.AppendItem([name, "Delete"])
            self.tc.write("Added: " + str(name) + "\n")

    @override
    def pdf_delete( self, event ):
        row = self.dvc.ItemToRow(event.GetItem())
        if self.dvc.GetTextValue(row, 1) == "Delete":
            name = self.dvc.GetTextValue(row, 0)
            self.dvc.DeleteItem(row)
            self.delete_item(name)
            self.tc.write("Deleted: " + str(name) + "\n")

    def delete_item( self, name ):
        data = self.collection.get(include=["metadatas"])
        delete_id = []
        for idx in range(len(data["ids"])):
            current_id = data['ids'][idx]
            metadata = data['metadatas'][idx]

            if metadata['Name'] == name:
                delete_id.append(current_id)

        self.collection.delete(delete_id)

    @override
    def pdf_fetch( self, event ):
        meta = self.collection.get(include=["metadatas"])["metadatas"]
        names = []
        for m in meta:
            if m["Name"] not in names:
                names.append(m["Name"])

        self.tc.write("Files in Database: " + str(names) + "\n")
        
        current = []
        count = count = self.dvc.GetItemCount()
        for row in range(count):
            current.append(self.dvc.GetTextValue(row, 0))

        for item in current:
            if item not in names:
                count = count = self.dvc.GetItemCount()
                for row in range(count):
                    self.dvc.DeleteItem(row)
                    self.tc.write("Deleted: ", item + "\n")

        for item in names:
            if item not in current:
                self.dvc.AppendItem([item, "Delete"])
                self.tc.write("Added: " + str(item) + "\n")


    @override
    def query_search( self, event ):
        text = self.text_search.GetValue()
        self.tc.write("Searched: " + text + "\n\n")
        data = collection.query(query_texts=text, n_results=3)
        for idx in range(len(data["ids"][0])):
            current_id = data['ids'][0][idx]
            filename = data['metadatas'][0][idx]['Name']
            content = data['documents'][0][idx]

            self.tc.write("Top #" + str(idx+1) + "\n")
            self.tc.write(str(filename) + "\n")
            self.tc.write(str(current_id) + "\n")
            self.tc.write(str(content) + "\n\n")

        
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

if __name__ == '__main__':
    app = wx.App(False)
    chroma_client = chromadb.PersistentClient(path="./chroma_store")

    '''
    try:
        chroma_client.delete_collection(name="my_collection")
        #collection = chroma_client.get_or_create_collection(name="my_collection")
    except Exception as e:
        pass
    '''
    
    collection = chroma_client.get_or_create_collection(name="my_collection")
    
    frame = MyFrame(collection)
    frame.Show()
    app.MainLoop()
