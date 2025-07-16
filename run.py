import wx
from noname import MyFrame1
from typing_extensions import override
import fitz
import os
import chromadb
from datetime import datetime
import wx.richtext  # For RichTextCtrl attributes

class MyFrame(MyFrame1):
    def __init__(self):
        super().__init__(None)
        self.build1 = None
        self.dvcBuild.AppendItem(["Build 1", "Delete"])
        self.build2 = None
        self.dvcBuild.AppendItem(["Build 2", "Delete"])
        self.load_build(None)
        self.num = 3
        
    @override
    def pdf_add(self, event):
        if self.build1 == None and self.build2 == None:
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("Please Load a Build Before Adding PDFs\n")
            self.tc.EndStyle()
            self.tc.ShowPosition(self.tc.GetLastPosition())
            return

        with wx.FileDialog(self, "Open PDF file", wildcard="PDF files (*.pdf)|*.pdf",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

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

            self.start_loading()
            
            pathnames = fileDialog.GetPaths()
            processed = 0
            for pathname in pathnames:
                name = os.path.basename(pathname)
                docs, ids = extract_text_chunks(pathname)
                metas = [{"Name": name}] * len(ids)
                if not self.isSubset(collection.get(include=["metadatas"])["ids"], ids):
                    collection.add(
                        documents=docs,
                        ids=ids,
                        metadatas=metas,
                    )
                
                    self.dvc.AppendItem([name, "Delete"])
                
                    attr = wx.richtext.RichTextAttr()
                    attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
                    attr.SetTextColour(wx.Colour("#000000"))  # Black text
                    attr.SetParagraphSpacingBefore(20)
                    attr.SetParagraphSpacingAfter(20)
                    attr.SetLeftIndent(75, 0)
                    attr.SetRightIndent(75)
                    self.tc.BeginStyle(attr)
                    self.tc.WriteText("Added: " + str(name) + "\n")
                    self.tc.EndStyle()
                    processed += 1
                    attr = wx.richtext.RichTextAttr()
                    attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
                    attr.SetTextColour(wx.Colour("#000000"))  # Black text
                    attr.SetParagraphSpacingBefore(20)
                    attr.SetParagraphSpacingAfter(20)
                    attr.SetLeftIndent(75, 0)
                    attr.SetRightIndent(75)
                    self.tc.BeginStyle(attr)
                    self.tc.WriteText("Processed: " + str(processed) + "/" + str(len(pathnames)) + "\n")
                    self.tc.EndStyle()
                else:
                    attr = wx.richtext.RichTextAttr()
                    attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
                    attr.SetTextColour(wx.Colour("#000000"))  # Black text
                    attr.SetParagraphSpacingBefore(20)
                    attr.SetParagraphSpacingAfter(20)
                    attr.SetLeftIndent(75, 0)
                    attr.SetRightIndent(75)
                    self.tc.BeginStyle(attr)
                    self.tc.WriteText("Document " + name + " Already in Database\n")
                    self.tc.EndStyle()

            self.end_loading()

    def isSubset(self, a, b):
        for i in range(len(b)):
            if not b[i] in a:
                return False
        return True

    @override
    def pdf_delete(self, event):
        row = self.dvc.ItemToRow(event.GetItem())
        self.start_loading()
        if self.dvc.GetTextValue(row, 1) == "Delete":
            name = self.dvc.GetTextValue(row, 0)
            self.dvc.DeleteItem(row)
            self.delete_item(name)
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("Deleted: " + str(name) + "\n")
            self.tc.EndStyle()

        self.end_loading()

    def delete_item(self, name):
        if self.build1 != None:
            data = self.collection1.get(include=["metadatas"])
            delete_id = self.find_data(data, name)
            if len(delete_id) > 0:
                self.collection1.delete(delete_id)
            
        if self.build2 != None:
            data = self.collection2.get(include=["metadatas"])
            delete_id = self.find_data(data, name)
            if len(delete_id) > 0:
                self.collection2.delete(delete_id)

    def find_data(self, data, name):
        delete_id = []
        for idx in range(len(data["ids"])):
            current_id = data['ids'][idx]
            metadata = data['metadatas'][idx]
            if metadata['Name'] == name:
                delete_id.append(current_id)
        return delete_id

    @override
    def pdf_fetch(self, event):
        if self.build1 == None and self.build2 == None:
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("Please Load a Build\n")
            self.tc.EndStyle()
            self.tc.ShowPosition(self.tc.GetLastPosition())
            return

        self.start_loading()
        names = []
        if self.build1 != None:
            names.extend(self.refresh_meta(self.collection1.get(include=["metadatas"])["metadatas"]))
        if self.build2 != None:
            names.extend(self.refresh_meta(self.collection2.get(include=["metadatas"])["metadatas"]))

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
                attr = wx.richtext.RichTextAttr()
                attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
                attr.SetTextColour(wx.Colour("#000000"))  # Black text
                attr.SetParagraphSpacingBefore(20)
                attr.SetParagraphSpacingAfter(20)
                attr.SetLeftIndent(75, 0)
                attr.SetRightIndent(75)
                self.tc.BeginStyle(attr)
                self.tc.WriteText("Deleted: " + str(item) + "\n")
                self.tc.EndStyle()

        for item in names:
            if item not in current:
                self.dvc.AppendItem([item, "Delete"])
                attr = wx.richtext.RichTextAttr()
                attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
                attr.SetTextColour(wx.Colour("#000000"))  # Black text
                attr.SetParagraphSpacingBefore(20)
                attr.SetParagraphSpacingAfter(20)
                attr.SetLeftIndent(75, 0)
                attr.SetRightIndent(75)
                self.tc.BeginStyle(attr)
                self.tc.WriteText("Added: " + str(item) + "\n")
                self.tc.EndStyle()

        self.end_loading()

    def refresh_meta(self, meta):
        names = []
        for m in meta:
            if m["Name"] not in names:
                names.append(m["Name"])
        attr = wx.richtext.RichTextAttr()
        attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
        attr.SetTextColour(wx.Colour("#000000"))  # Black text
        attr.SetParagraphSpacingBefore(20)
        attr.SetParagraphSpacingAfter(20)
        attr.SetLeftIndent(75, 0)
        attr.SetRightIndent(75)
        self.tc.BeginStyle(attr)
        self.tc.WriteText("Files in Database: " + str(names) + "\n")
        self.tc.EndStyle()
        self.tc.ShowPosition(self.tc.GetLastPosition())
        return names
        
    @override
    def query_search(self, event):
        if self.build1 == None and self.build2 == None:
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("Please Load a Build Before Searching\n")
            self.tc.EndStyle()
            self.tc.ShowPosition(self.tc.GetLastPosition())
            return
        
        text = self.text_search.GetValue()
        if not text.strip():
            return  # Ignore empty queries
        
        # Display user query in chat format with timestamp, right-aligned, grey background
        timestamp = datetime.now().strftime("%I:%M %p")  # 12-hour format with AM/PM (e.g., 09:49 AM)
        attr = wx.richtext.RichTextAttr()
        attr.SetBackgroundColour(wx.Colour("#C0C0C0"))  # Light grey background for user
        attr.SetTextColour(wx.Colour("#000000"))  # Black text
        attr.SetParagraphSpacingBefore(10)
        attr.SetParagraphSpacingAfter(10)
        attr.SetLeftIndent(500, 0)  # Right-aligned with large left indent
        attr.SetRightIndent(75)
        self.tc.BeginStyle(attr)
        self.tc.WriteText(f"You ({timestamp}): {text}\n")
        self.tc.EndStyle()
        
        # Clear the search input
        self.text_search.Clear()
        
        # Process query for each collection
        if self.build1 != None:
            self.query_collection(text, self.num, self.collection1)
        if self.build2 != None:
            self.query_collection(text, self.num, self.collection2)
        
        # Scroll to the bottom
        self.tc.ShowPosition(self.tc.GetLastPosition())

    def query_collection(self, text, n, collection):
        self.start_loading()
        data = collection.query(query_texts=text, n_results=n)
        
        # Combine all response lines into one chat message block
        timestamp = datetime.now().strftime("%I:%M %p")  # 12-hour format with AM/PM
        response = f"System ({timestamp}):\n"
        if data["documents"] and len(data["documents"][0]) > 0:
            for idx in range(len(data["ids"][0])):
                current_id = data['ids'][0][idx]
                filename = data['metadatas'][0][idx]['Name']
                content = data['documents'][0][idx]
                response += f"Result #{idx+1}:\nFile: {filename}\nID: {current_id}\nContent: {content}\n{'-' * 40}\n"
        else:
            response += "No results found.\n"
        
        attr = wx.richtext.RichTextAttr()
        attr.SetBackgroundColour(wx.Colour("#FFFFFF"))  # White background for system
        attr.SetTextColour(wx.Colour("#000000"))  # Black text
        attr.SetParagraphSpacingBefore(10)
        attr.SetParagraphSpacingAfter(10)
        attr.SetLeftIndent(75, 0)  # Left-aligned with small left indent
        attr.SetRightIndent(500)
        self.tc.BeginStyle(attr)
        self.tc.WriteText(response)
        self.tc.EndStyle()
        self.end_loading()
        
        # Scroll to the bottom
        self.tc.ShowPosition(self.tc.GetLastPosition())

    @override
    def load_build(self, event):
        if self.build1 != None and self.build2 != None:
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("Maximum Build Files Loaded\n")
            self.tc.EndStyle()
            self.tc.ShowPosition(self.tc.GetLastPosition())
            return
            
        with wx.DirDialog(self, "Select Directory to Create or Load Build", "./",
                    wx.DD_DEFAULT_STYLE) as folder:
            
            if folder.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = folder.GetPath()
            if pathname == self.build1 or pathname == self.build2:
                attr = wx.richtext.RichTextAttr()
                attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
                attr.SetTextColour(wx.Colour("#000000"))  # Black text
                attr.SetParagraphSpacingBefore(20)
                attr.SetParagraphSpacingAfter(20)
                attr.SetLeftIndent(75, 0)
                attr.SetRightIndent(75)
                self.tc.BeginStyle(attr)
                self.tc.WriteText("Build Already Loaded\n")
                self.tc.EndStyle()
                self.tc.ShowPosition(self.tc.GetLastPosition())
                return

            self.start_loading()
            
            chroma_client = chromadb.PersistentClient(path=pathname)
            
            if self.build1 == None:
                self.build1 = pathname
                self.collection1 = chroma_client.get_or_create_collection(name="my_collection")
                self.dvcBuild.SetTextValue(pathname, 0, 1)
            else:
                self.build2 = pathname
                self.collection2 = chroma_client.get_or_create_collection(name="my_collection")
                self.dvcBuild.SetTextValue(pathname, 1, 1)
            
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("Loaded or Created Build: " + str(pathname))
            self.tc.EndStyle()
            self.end_loading()
            
            self.pdf_fetch(None)

    @override
    def delete_build(self, event):
        row = self.dvcBuild.ItemToRow(event.GetItem())
        name = self.dvcBuild.GetTextValue(row, 1)
        if name != "None":
            self.dvcBuild.SetTextValue("None", row, 1)
            if row == 0:
                self.build1 = None
            else:
                self.build2 = None
                
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("*** Unloaded " + self.dvcBuild.GetTextValue(row, 0) + ": " + str(name) + " ***\n")
            self.tc.EndStyle()
            self.pdf_fetch(None)

    def open_settings(self, event):
        dlg = wx.NumberEntryDialog(self, "Query", "Number of Results = ", "Settings", self.num, 1, 10)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        result = dlg.GetValue()
        dlg.Destroy()
        self.num = result

    def show_help(self, event):
        try: 
            os.startfile(".\\User Manual")
        except:
            attr = wx.richtext.RichTextAttr()
            attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
            attr.SetTextColour(wx.Colour("#000000"))  # Black text
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(20)
            attr.SetLeftIndent(75, 0)
            attr.SetRightIndent(75)
            self.tc.BeginStyle(attr)
            self.tc.WriteText("Can't Open or Find User Manual\n")
            self.tc.EndStyle()
            self.tc.ShowPosition(self.tc.GetLastPosition())

    def start_loading(self):
        attr = wx.richtext.RichTextAttr()
        attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
        attr.SetTextColour(wx.Colour("#000000"))  # Black text
        attr.SetParagraphSpacingBefore(20)
        attr.SetParagraphSpacingAfter(20)
        attr.SetLeftIndent(75, 0)
        attr.SetRightIndent(75)
        self.tc.BeginStyle(attr)
        self.tc.WriteText("+" * 16 + "\n")
        self.tc.WriteText(" Loading...\n")
        self.tc.WriteText("+" * 16 + "\n")
        self.tc.EndStyle()
        self.tc.ShowPosition(self.tc.GetLastPosition())

    def end_loading(self):
        attr = wx.richtext.RichTextAttr()
        attr.SetBackgroundColour(wx.Colour("#FFFFFF"))
        attr.SetTextColour(wx.Colour("#000000"))  # Black text
        attr.SetParagraphSpacingBefore(20)
        attr.SetParagraphSpacingAfter(20)
        attr.SetLeftIndent(75, 0)
        attr.SetRightIndent(75)
        self.tc.BeginStyle(attr)
        self.tc.WriteText(" Complete\n")
        self.tc.EndStyle()
        self.tc.ShowPosition(self.tc.GetLastPosition())

def extract_text_chunks(pdf_path):
    chunk_list = []
    meta_list = []
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            para_count = 0
            for paragraph in text.split('\n\n'):
                para_count = para_count + 1
                paragraph = paragraph.strip()
                if paragraph:
                    chunk_list.append(paragraph)
                    meta_list.append(
                        os.path.basename(pdf_path) + str(page_num + 1) + str(para_count)
                    )
    return chunk_list, meta_list

if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame()
    frame.Show()
    app.MainLoop()
