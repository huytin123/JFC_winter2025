from concurrent.futures import ThreadPoolExecutor
import platform
import signal
import subprocess
import threading
import time
from sentence_transformers import CrossEncoder
import re
import wx
from noname import MyFrame1
from typing_extensions import override
import fitz
import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from datetime import datetime
import wx.richtext  # For RichTextCtrl attributes
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.text_splitter import RecursiveCharacterTextSplitter
import configparser

import time
import sys

class MyFrame(MyFrame1):
    def __init__(self, collection_name, model_name, rerank_name, max_search):
        super().__init__(None)
        self.collection_name = collection_name
        self.model_name = model_name
        self.rerank_name = rerank_name
        self.build = []
        self.collection = []
        self.num_result = 10
        self.num_search = max_search
        self.to_be_processed = 0
        self.lock = threading.Lock()  
        self.thread_list = []
        self.executor = None
        self.load_build(None)

    # loading database into program
    @override
    def load_build(self, event):       
        with wx.DirDialog(self, "Select Directory to Create or Load Database", "./",
                    wx.DD_DEFAULT_STYLE) as folder:
            
            if folder.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = folder.GetPath()
            # Create a subdirectory with "db_" prefix
            db_pathname = os.path.join(pathname, "JFCdb_" + self.collection_name)
            
            if db_pathname in self.build:
                self.write_to_tc("Database Already Loaded\n")
                self.tc.ShowPosition(self.tc.GetLastPosition())
                return

            self.start_loading()
            
            # Ensure the db_ subdirectory exists
            os.makedirs(db_pathname, exist_ok=True)
            
            # Initialize PersistentClient with the db_ subdirectory
            chroma_client = chromadb.PersistentClient(path=db_pathname)
            
            # Create or load the collection
            collection = None
            try:            
                collection = chroma_client.get_collection(
                    name=self.collection_name
                )
                if collection.metadata is None:
                    self.write_to_tc("Collection uses old version without metadata\n")
                    return
                
                if collection.metadata["Model"] != self.model_name:
                    self.write_to_tc("Collection has been embedding with '" + collection.metadata["Model"] + "' instead of '" + self.model_name + "'\n")
                    return
                    
                
            except Exception as e:
                # checking model for updates if online
                model = None
                try:
                    model = SentenceTransformerEmbeddingFunction(model_name=self.model_name)
                except Exception as e:
                    model = SentenceTransformerEmbeddingFunction(model_name=self.model_name, local_files_only=True)
                
                collection = chroma_client.create_collection(
                    name=self.collection_name,
                    embedding_function=model,
                    metadata={"Model": self.model_name},
                    configuration={
                        "hnsw": {
                            "space": "cosine",
                        }
                    }
                )

            self.build.append(db_pathname)
            self.collection.append(collection)
            
            self.dvcBuild.AppendItem(["Database " + str(len(self.build)), db_pathname, "✗"])
            
            self.write_to_tc("Loaded or Created Database: " + str(db_pathname) + " with collection files in: " + os.path.join(db_pathname, "bin_files"))
            self.end_loading()
            self.pdf_fetch(None)

    # dialog for selecting when database is stored
    def get_collection(self):
        collection = None
        if len(self.build) > 1:
            dlg = wx.SingleChoiceDialog(self, "Choose Database", "Store PDF in Database: ", self.build)
            if dlg.ShowModal() == wx.ID_CANCEL:
                return

            collection = self.collection[dlg.GetSelection()]
        else:
            collection = self.collection[0]

        return collection

    # dialog for selecting all PDFs in folder
    def add_folders (self):
        pathnames = []
        with wx.DirDialog(self, "Select a folder",
                       style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as folderDialog:

            if folderDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            folder_path = folderDialog.GetPath()

            # collect all files within the directory
            for root, dirs, files in os.walk(folder_path):
                for filename in files:
                    if filename.lower().endswith('.pdf'):
                        full_path = os.path.join(root, filename)
                        pathnames.append(full_path)

        return pathnames

    # dialog for selecting PDFs
    def add_files (self):
        pathnames = []
        with wx.FileDialog(self, "Open PDF Files", wildcard="PDF files (*.pdf)|*.pdf",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            pathnames = fileDialog.GetPaths()
            
        return pathnames

    # multithreading for PDF processing
    def create_executors (self, pathnames, collection):
        with ThreadPoolExecutor(max_workers=1) as executor:
            self.executor = executor  

            for pathname in pathnames:
                executor.submit(self.put_pdf_collections, pathname, collection, len(pathnames))

    # writing to search area
    def write_to_tc(self, text):
        self.tc.SetInsertionPointEnd()
        attr = wx.richtext.RichTextAttr()
        attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
        attr.SetTextColour(wx.Colour("#000000"))  # Black text
        attr.SetParagraphSpacingBefore(20)
        attr.SetParagraphSpacingAfter(20)
        attr.SetLeftIndent(75, 0)
        attr.SetRightIndent(75)
        attr.SetAlignment(wx.TEXT_ALIGNMENT_LEFT)
        self.tc.BeginStyle(attr)
        self.tc.WriteText(text)
        self.tc.EndStyle()

    # inserting PDF into collection
    def put_pdf_collections(self, pathname, collection, pathnum): #in thread
        name = os.path.basename(pathname)
        docs, ids, metas = extract_text_chunks(pathname)
        if not self.isSubset(collection.get(include=["metadatas"])["ids"], ids):
            with self.lock:
                collection.add(
                    documents=docs,
                    ids=ids,
                    metadatas=metas,
                )
            
            collection_index = self.collection.index(collection)
            db_pathname = self.build[collection_index]

            wx.CallAfter(self.dvc.AppendItem, [name, "✗"])

            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            wx.CallAfter(self.tc.BeginStyle,attr)

            self.tc.SetInsertionPointEnd()

            with self.lock:
                self.to_be_processed -= 1
                
                wx.CallAfter(self.tc.WriteText, "Added: " + str(name) + "\n")
                wx.CallAfter(self.tc.WriteText,"Processed: " + str(pathnum - self.to_be_processed) + "/" + str(pathnum) + "\n")

            if self.to_be_processed ==0:
                wx.CallAfter(self.end_loading)

            wx.CallAfter(self.tc.EndStyle)
        
        else:
            with self.lock:
                self.to_be_processed -= 1
                #print("Processed:", self.to_be_processed)
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)

            wx.CallAfter(self.tc.SetInsertionPointEnd())
            wx.CallAfter(self.tc.BeginStyle,attr)
            wx.CallAfter(self.tc.WriteText,"Document " + name + " Already in Database\n")
            wx.CallAfter(self.tc.EndStyle)

    # handles adding PDF/folder button to add selected PDFs
    @override
    def pdf_add( self, event ):

        if self.to_be_processed!=0:
            self.write_to_tc("Files are still being loaded\n")
            self.tc.ShowPosition(self.tc.GetLastPosition())
            return
        
        if len(self.build) == 0:
            self.write_to_tc("Please Load a Database Before Adding PDFs\n")
            self.tc.ShowPosition(self.tc.GetLastPosition())
            return
        
        button = event.GetEventObject()
        label = button.label
        pathnames=[]
        if label == "Add PDF": 
            pathnames = self.add_files()
        else:
            pathnames = self.add_folders()

        if pathnames == None:
            return
       
        collection = self.get_collection()
        if collection == None:
            return 

        self.to_be_processed = len(pathnames)
        self.start_loading()
        thread = threading.Thread(target=self.create_executors, args=(pathnames, collection))
        #thread.daemon= True
        self.thread_list.append (thread)
        thread.start()

    # checks one array is subset of another
    def isSubset(self, a, b):
        for i in range(len(b)):
            if not b[i] in a:
                return False
        return True

    # closing threads
    @override
    def close_threads(self, event):
        if self.executor:
            self.executor.shutdown(wait=True,cancel_futures=True)

        for t in self.thread_list:
            if t.is_alive():
                t.join()
        self.Destroy()

    # handles deleting PDF from collection
    @override
    def pdf_delete(self, event):
        row = self.dvc.ItemToRow(event.GetItem())
        self.start_loading()
        if self.dvc.GetTextValue(row, 1) == "✗":
            name = self.dvc.GetTextValue(row, 0)
            self.dvc.DeleteItem(row)
            self.delete_item(name)

            self.write_to_tc("Deleted: " + str(name) + "\n")

        self.end_loading()

    def delete_item(self, name):
        for i in range(len(self.build)):
            data = self.collection[i].get(include=["metadatas"])
            delete_id = self.find_data(data, name)
            if len(delete_id) > 0:
                self.collection[i].delete(delete_id)

    # finds collection ID with specific 
    def find_data(self, data, name):
        delete_id = []
        for idx in range(len(data["ids"])):
            current_id = data['ids'][idx]
            metadata = data['metadatas'][idx]
            if metadata['Name'] == name:
                delete_id.append(current_id)
        return delete_id

    # handles refreshing menu to check PDF in collection
    @override
    def pdf_fetch(self, event):
        self.start_loading()
        names = []
        for i in range(len(self.build)):
            names.extend(self.refresh_meta(self.collection[i].get(include=["metadatas"])["metadatas"]))

        current = []
        count = self.dvc.GetItemCount()
        for row in range(count):
            current.append(self.dvc.GetTextValue(row, 0))

        for item in current:
            if item not in names:
                count = self.dvc.GetItemCount()
                delete_row = 0
                for row in range(count):
                    if item == self.dvc.GetTextValue(row, 0):
                        delete_row = row
                        
                self.dvc.DeleteItem(delete_row)
                
                self.write_to_tc("Deleted: " + str(item) + "\n")


        for item in names:
            if item not in current:
                self.dvc.AppendItem([item, "✗"])

        self.end_loading()

    # checks names of PDF in collection
    def refresh_meta(self, meta):
        names = []
        for m in meta:
            if m["Name"] not in names:
                names.append(m["Name"])
                
        self.write_to_tc("Files in Database: " + str(names) + "\n")
        self.tc.ShowPosition(self.tc.GetLastPosition())
        return names

    # merges dictionaries 
    def merge_result_dicts(self, data_dict, result_dict):
        keys_to_merge = ['documents', 'ids', 'metadatas', 'distances']
        
        for key in keys_to_merge:
            if key in data_dict and data_dict[key]:
                result_dict[key][0].extend(data_dict[key][0])
        
        return result_dict

    # handles query the program with user input
    @override
    def query_search(self, event):
        if len(self.build) == 0:
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("Please Load a Database Before Searching\n")
            self.tc.EndStyle()
            return

        if self.dvc.GetItemCount() == 0:
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("No PDFs in Database\n")
            self.tc.WriteText("Please Refresh or Added PDFs to Database\n")
            self.tc.EndStyle()
            return

        text = self.text_search.GetValue()
        if not text.strip():
            return  # Ignore empty queries

        # Reset style and ensure a clean paragraph break
        self.tc.BeginStyle(wx.richtext.RichTextAttr())  # Reset to default
        self.tc.Newline()
        timestamp = datetime.now().strftime("%I:%M %p")
        self.tc.SetInsertionPointEnd()

        attr = wx.richtext.RichTextAttr()
        attr.SetTextColour(wx.Colour("#000000"))
        attr.SetAlignment(wx.TEXT_ALIGNMENT_RIGHT)      # Align bubble to the right
        attr.SetParagraphSpacingBefore(30)

        # Outer padding (from the widget edge)
        attr.SetRightIndent(50)  # Push bubble away from right edge
        attr.SetLeftIndent(150, 0)  # Push bubble to the right overall

        query_pos = self.tc.GetInsertionPoint()
        padded_text = f"You ({timestamp}): {text}"

        self.tc.BeginStyle(attr)
        self.tc.WriteText(padded_text)
        self.tc.Newline()
        self.tc.EndStyle()


        # Clear input and force layout
        self.text_search.Clear()
        self.tc.Layout() 
        result_dict= {}
        # Continue with query handling
        first =True
        start_time = time.time()
        
        self.start_loading()
        for i in range(len(self.build)):
            if first == True:
                result_dict = self.query_collection(text, self.num_search, self.collection[i])
                first =False
            else:
                result_dict = self.merge_result_dicts ( result_dict,self.query_collection(text, self.num_search, self.collection[i]) )

        result_dict = self.rerank(result_dict, text)
        result_dict = result_dict[0: self.num_result]
        self.print_result(result_dict)

        if query_pos:
            self.tc.ShowPosition(query_pos)

    # reranks the queried results
    def rerank(self, data,question):
        try:
            cross_encoder = CrossEncoder(model_name_or_path=self.rerank_name)
        except Exception as e:
            cross_encoder = CrossEncoder(model_name_or_path=self.rerank_name, local_files_only=True, trust_remote_code=True)

        retrieved_docs = data['documents'][0]
        retrieved_metadata = data['metadatas'][0]
        retrieved_id =data['ids'][0]
        pairs = [[question, doc] for doc in retrieved_docs]
        scores = cross_encoder.predict(pairs)
        sorted_entries = sorted(
            zip(scores, retrieved_docs, retrieved_id, retrieved_metadata),
            key=lambda x: x[0],
            reverse=True
        )
        return sorted_entries

    # handles clicking on PDF url
    @override
    def on_url_click(self, event):
        filepath = event.GetString()

        if os.path.exists(filepath):
            system = platform.system()
            try:
                if system == "Darwin":  # macOS
                    subprocess.run(["open", filepath], check=True)
                elif system == "Windows":
                    os.startfile(filepath)
                elif system == "Linux":
                    subprocess.run(["xdg-open", filepath], check=True)
                else:
                    wx.MessageBox("Unsupported OS", "Error", wx.ICON_ERROR)
            except Exception as e:
                wx.MessageBox(f"Failed to open file:\n{e}", "Error", wx.ICON_ERROR)
        else:
            wx.MessageBox(f"File not found:\n{filepath}", "Error", wx.ICON_ERROR)

    # prints in search area the query results
    def print_result (self, data):
        timestamp = datetime.now().strftime("%I:%M %p")  # 12-hour format with AM/PM
        self.tc.BeginStyle(wx.richtext.RichTextAttr())
        if data and len(data) > 0:
            for i, (score, doc, current_id, metadata) in enumerate(data):
                filepath = metadata.get("Address", "")
                filename = metadata.get("Name", "")
                page = metadata.get("Page", "")
                content = doc

                self.tc.SetInsertionPointEnd()
                attr = wx.richtext.RichTextAttr()
                attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
                attr.SetTextColour(wx.Colour("#000000"))
                attr.SetParagraphSpacingBefore(10)  # Consistent spacing before
                attr.SetParagraphSpacingAfter(10)   # Consistent spacing after
                attr.SetLeftIndent(75, 0)
                attr.SetRightIndent(20)
                attr.SetAlignment(wx.TEXT_ALIGNMENT_LEFT)
                self.tc.BeginStyle(attr)

                self.tc.WriteText(f"System ({timestamp}):\n")
                # Highlight "Result #{i+1}"
                highlight_attr = wx.richtext.RichTextAttr()
                highlight_attr.SetBackgroundColour(wx.Colour("#ADD8E6"))
                highlight_attr.SetTextColour(wx.Colour("#000000"))
                self.tc.BeginStyle(highlight_attr)
                self.tc.WriteText(f"Result #{i+1}")
                self.tc.EndStyle()
                self.tc.WriteText(":\nFile: ")

                # Style hyperlink
                self.tc.BeginURL(filepath)
                self.tc.BeginTextColour(wx.BLUE)
                self.tc.BeginUnderline()
                self.tc.WriteText(filename)
                self.tc.EndUnderline()
                self.tc.EndTextColour()
                self.tc.EndURL()

                self.tc.WriteText(
                    f"\nPage: {page}\nID: {current_id}\nScore: {score}\nContent: {content}\n{'-' * 40} \n \n"
                )
                self.tc.EndStyle()

        else:
            self.tc.SetInsertionPointEnd()
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))
            attr.SetParagraphSpacingBefore(10)
            attr.SetParagraphSpacingAfter(10)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(20)
            attr.SetAlignment(wx.TEXT_ALIGNMENT_LEFT)
            self.tc.BeginStyle(attr)
            self.tc.WriteText(f"System ({timestamp}):\nNo results found.")
            self.tc.EndStyle()

        # Add a final newline with consistent spacing to separate from future content
        self.tc.BeginStyle(wx.richtext.RichTextAttr())
        self.tc.Newline()
        self.tc.EndStyle()

    # queries collection
    def query_collection(self, text, n, collection):
        data = collection.query(query_texts=text, n_results=n)
        return data

    # clears search area
    @override
    def clear_tc(self, event):
        self.tc.Clear()

    # handles deleting database from program
    @override
    def delete_build(self, event):
        row = self.dvcBuild.ItemToRow(event.GetItem())
        name = self.dvcBuild.GetTextValue(row, 1)
        build_num = self.dvcBuild.GetTextValue(row, 0)
        if self.dvcBuild.GetTextValue(row, 2) == "✗":
            self.dvcBuild.DeleteItem(row)

            self.build.pop(row)
            self.collection.pop(row)
                
            self.write_to_tc("*** Unloaded " + build_num + ": " + str(name) + " ***\n")
            self.pdf_fetch(None)

    # opens dialog for settings
    def open_settings(self, event):
        dlg = wx.NumberEntryDialog(self, "Query", "Number of Results = ", "Settings", self.num_result, 1, 100)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        result = dlg.GetValue()
        dlg.Destroy()
        self.num_result = result

    # handles help button to direct to User Manual
    def show_help(self, event):
        try: 
            os.startfile(".\\User Manual.pdf")
        except:
            self.write_to_tc("Can't Open or Find User Manual\n")
            self.tc.ShowPosition(self.tc.GetLastPosition())

    # basic loading log
    def start_loading(self):
        self.write_to_tc("Loading...\n")
        self.write_to_tc("-" * 16 + "\n")
        self.tc.ShowPosition(self.tc.GetLastPosition())

    # basic completion log
    def end_loading(self):
        self.write_to_tc("Complete\n")
        self.tc.ShowPosition(self.tc.GetLastPosition())

# chunking algorithm
def extract_text_chunks(pdf_path):
    chunk_list = []
    meta_list = []
    id_list= []
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
            chunk_index =0
            for chunk in chunks_for_page:
                chunk_index +=1
                chunk_list.append(chunk.strip())
                id_list.append(
                    os.path.abspath(pdf_path) + "::pg="+str( page_num + 1)+ "::ch="+str(chunk_index)
                )
                meta_list.append({
                    "Name": os.path.basename(pdf_path),
                    "Address": os.path.abspath(pdf_path),
                    "Page": page_num + 1,
                })

    return chunk_list, id_list, meta_list

if __name__ == '__main__':
    done = False
    
    def animate():
        symbols = ['-', '\\', '|', '/']
        i = 0
        while not done:
            sys.stdout.write('\rLoading ' + symbols[i % len(symbols)])
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
            
        sys.stdout.write('\rDone!     ')

    t = threading.Thread(target=animate)
    t.start()
    
    config = configparser.ConfigParser()

    collection_name = None
    model_name = None
    rerank_name = None
    max_search = 0
    try:
        config.read('config.ini')
        collection_name = config['Settings']['name']
        model_name = config['Settings']['model']
        rerank_name = config['Settings']['rerank']
        max_search = int(config['Settings']['search'])
    except Exception as e:
        # default settings
        print(e)
        collection_name = "my_collection"
        model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
        rerank_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
        max_search = 100

    app = wx.App(False)
    frame = MyFrame(collection_name, model_name, rerank_name, max_search)
    frame.Show()
    done = True
    app.MainLoop()
