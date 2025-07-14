import wx
from noname import MyFrame1
from typing_extensions  import override
import fitz
import os
import chromadb

class MyFrame(MyFrame1):
    def __init__(self):
        super().__init__(None)
        self.build = []
        self.collection = []
        self.load_build(None)
        self.num = 3

    
    def get_collection(self):
        if self.build1 != None and self.build2 != None:
            dlg = wx.SingleChoiceDialog(self, "Choose Build", "Store PDF in Build: ", ["Build 1", "Build 2"])
            if dlg.ShowModal() == wx.ID_CANCEL:
                return

            if dlg.GetSelection == 0:
                collection = self.collection1
            else:
                collection = self.collection2
        elif self.build1 != None:
            collection = self.collection1
        else:
            collection = self.collection2

        return collection

    def add_folders (self):
        pathnames = []
        with wx.DirDialog(self, "Select a folder",
                       style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as folderDialog:

            if folderDialog.ShowModal() == wx.ID_CANCEL:
                return


            self.start_loading()
            folder_path = folderDialog.GetPath()

            #collect all files qithin the directory
            for root, dirs, files in os.walk(folder_path):
                for filename in files:
                    if filename.lower().endswith('.pdf'):
                        full_path = os.path.join(root, filename)
                        pathnames.append(full_path)

        return pathnames
    
    def add_files (self):
        pathnames = []
        with wx.FileDialog(self, "Open PDF Files", wildcard="PDF files (*.pdf)|*.pdf",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            self.start_loading()
            
            pathnames = fileDialog.GetPaths()
        return pathnames
       
#     @override
#     def pdf_add( self, event ):
#         if len(self.build) == 0:
#             self.tc.write("Please Load a Build Before Adding PDFs\n")
#             return
#         with wx.FileDialog(self, "Open PDF file", wildcard="PDF files (*.pdf)|*.pdf",
#                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE) as fileDialog:

#             if fileDialog.ShowModal() == wx.ID_CANCEL:
#                 return

#             if len(self.build) > 1:
#                 choice = []
#                 for i in range(len(self.build)):
#                     choice.append("Build " + str(i + 1))
                    
#                 dlg = wx.SingleChoiceDialog(self, "Choose Build", "Store PDF in Build: ", choice)
#                 if dlg.ShowModal() == wx.ID_CANCEL:
#                     return

                
#                 collection = self.collection[dlg.GetSelection()]
#             else:
#                 collection = self.collection[0]

    @override
    def pdf_add( self, event ):

        if self.build1 == None and self.build2 == None:
            self.tc.write("Please Load a Build Before Adding PDFs\n")
            return
        
        button = event.GetEventObject()
        label = button.GetLabel() 

        pathnames=[]
        if label == "➕ Add PDF": 
            pathnames = self.add_files()
        else:
            pathnames =self.add_folders()
        if pathnames == None:
            return 
        
        collection =self.collection1 # change
        collection = self.get_collection() #change
        if collection == None:
            return 
        
        processed = 0
        for pathname in pathnames:
            name = os.path.basename(pathname)
            docs, ids, metas = extract_text_chunks(pathname)
            if not self.isSubset(collection.get(include=["metadatas"])["ids"], ids):
                collection.add(
                    documents=docs,
                    ids=ids,
                    metadatas=metas,
                )
            
                self.dvc.AppendItem([name, "Delete"])
            
                self.tc.write("Added: " + str(name) + "\n")
                processed += 1
                self.tc.write("Processed: " + str(processed) + "/" + str(len(pathnames)) + "\n")
            else:
                self.tc.write("Document " + name + " Already in Database\n")

        self.end_loading()

    def isSubset(self, a, b):
        for i in range(len(b)):
            if not b[i] in a:
                return False

        return True

    @override
    def pdf_delete( self, event ):
        row = self.dvc.ItemToRow(event.GetItem())
        self.start_loading()
        if self.dvc.GetTextValue(row, 1) == "Delete":
            name = self.dvc.GetTextValue(row, 0)
            self.dvc.DeleteItem(row)
            self.delete_item(name)
            self.tc.write("Deleted: " + str(name) + "\n")

        self.end_loading()

    def delete_item( self, name ):
        for i in range(len(self.build)):
            data = self.collection[i].get(include=["metadatas"])
            delete_id = self.find_data(data, name)
            if len(delete_id) > 0:
                self.collection[i].delete(delete_id)

    def find_data( self, data, name ):
        delete_id = []
        for idx in range(len(data["ids"])):
            current_id = data['ids'][idx]
            metadata = data['metadatas'][idx]

            if metadata['Name'] == name:
                delete_id.append(current_id)

        return delete_id

    @override
    def pdf_fetch( self, event ):
        self.start_loading()
        self.tc.write("Refreshing...\n")
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
                self.tc.write("Deleted: " + str(item) + "\n")

        for item in names:
            if item not in current:
                self.dvc.AppendItem([item, "Delete"])
                self.tc.write("Added: " + str(item) + "\n")

        self.end_loading()

    def refresh_meta( self, meta ):
        names = []
        for m in meta:
            if m["Name"] not in names:
                names.append(m["Name"])

        self.tc.write("Files in Database: " + str(names) + "\n")
        return names
        
    @override
    def query_search( self, event ):
        if len(self.build) == 0:
            self.tc.write("Please Load a Build Before Searching\n")
            return
        
        text = self.text_search.GetValue()
        self.tc.write("Searched: " + text + "\n\n")
        for i in range(len(self.build)):
            self.query_collection(text, self.num, self.collection[i])

    def query_collection( self, text, n, collection):
        self.start_loading()
        data = collection.query(query_texts=text, n_results=n)
        self.tc.write("Finished Query\n")
        self.end_loading()
        for idx in range(len(data["ids"][0])):
            filename = data['metadatas'][0][idx]['Name']
            page = data['metadatas'][0][idx]['Page']
            para = data['metadatas'][0][idx]['Paragraph']
            content = data['documents'][0][idx]

            self.tc.write("+" * 16 + "\n")
            self.tc.write("Top #" + str(idx+1) + "\n")
            self.tc.write("+" * 16 + "\n")
            self.tc.write("File: " + str(filename) + "\n")
            self.tc.write("Page: " + str(page) + "\n")
            self.tc.write("Paragraph: " + str(para) + "\n")
            self.tc.write("+" * 16 + "\n")
            self.tc.write(str(content) + "\n\n")

    @override
    def load_build( self, event ):
        with wx.DirDialog (self, "Select Directory to Create or Load Build", "./",
                    wx.DD_DEFAULT_STYLE) as folder:
            
            if folder.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = folder.GetPath()
            if pathname in self.build:
                self.tc.write("Build Already Loaded\n")
                return

            self.start_loading()
            
            chroma_client = chromadb.PersistentClient(path=pathname)
            
            '''
            try:
                chroma_client.delete_collection(name="my_collection")
                #collection = chroma_client.get_or_create_collection(name="my_collection")
            except Exception as e:
                pass
            '''


            self.build.append(pathname)
            self.collection.append(chroma_client.get_or_create_collection(name="my_collection"))
            self.dvcBuild.AppendItem(["Build " + str(len(self.build)), pathname, "Delete"])
            
            self.tc.write("Loaded or Created Build: " + str(pathname) + "\n")
            self.end_loading()
            
            self.pdf_fetch(None)

    @override
    def delete_build( self, event ):
        row = self.dvcBuild.ItemToRow(event.GetItem())
        name = self.dvcBuild.GetTextValue(row, 1)
        build_num = self.dvcBuild.GetTextValue(row, 0)
        if self.dvcBuild.GetTextValue(row, 2) == "Delete":
            self.dvcBuild.DeleteItem(row)

            self.build.pop(row)
            self.collection.pop(row)

            self.tc.write("Unloaded " + build_num + ": " + str(name) + "\n")
            self.pdf_fetch(None)

    def open_settings( self, event ):
        dlg = wx.NumberEntryDialog(self, "Query", "Number of Results = ", "Settings", self.num, 1, 10)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return

        result = dlg.GetValue()
        dlg.Destroy()
        self.num = result

    def show_help( self, event ):
        self.tc.write("Opening User Manual: User Manual.pdf\n")
        try: 
            os.startfile(".\\User Manual.pdf")
        except:
            self.tc.write("Can't Open or Find User Manual\n")

    def start_loading( self ):
        self.tc.write("+" * 16 + "\n")
        self.tc.write(" Loading...\n")
        self.tc.write("+" * 16 + "\n")

    def end_loading( self ):
        self.tc.write("+" * 16 + "\n")
        self.tc.write(" Complete\n")
        self.tc.write("+" * 16 + "\n\n")

def extract_text_chunks(pdf_path):
    chunk_list = []
    id_list = []
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
                    id_list.append(
                        os.path.basename(pdf_path) +str( page_num + 1)+ str(para_count)
                    )
                    meta_list.append({
                        "Name": os.path.basename(pdf_path),
                        "Page": page_num + 1,
                        "Paragraph": para_count
                    })
                    
    return chunk_list, id_list, meta_list

if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame()
    frame.Show()
    app.MainLoop()
