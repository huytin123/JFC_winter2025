import wx
import wx.xrc
import wx.dataview

class MyFrame1(wx.Frame):

    def __init__(self, parent):
        

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title="Smart Document Search", pos=wx.DefaultPosition,
                          size=wx.Size(1188, 768), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetBackgroundColour("#FCFAF9")  # Soft background
        inter_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Inter")
        self.SetFont(inter_font)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        # Sidebar
        sidebarSizer = wx.BoxSizer(wx.VERTICAL)

        sidebarPanel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(280, -1))
        sidebarPanel.SetBackgroundColour("#8E6E6E")
        sidebarBox = wx.BoxSizer(wx.VERTICAL)

        self.dvc = wx.dataview.DataViewListCtrl(sidebarPanel, wx.ID_ANY, wx.DefaultPosition, wx.Size(260, 400), 0)
        self.dvc.SetBackgroundColour(wx.Colour(217, 217, 217))
        self.c1 = self.dvc.AppendTextColumn("Doc", wx.dataview.DATAVIEW_CELL_INERT, 180, wx.ALIGN_LEFT, 0)
        self.c2 = self.dvc.AppendTextColumn("✖", wx.dataview.DATAVIEW_CELL_INERT, 40, wx.ALIGN_CENTER, 0)
        sidebarBox.Add(self.dvc, 1, wx.ALL, 10)

        self.dvcBuild = wx.dataview.DataViewListCtrl(sidebarPanel, wx.ID_ANY, wx.DefaultPosition, wx.Size(260, 100), 0)
        self.dvcBuild.SetBackgroundColour(wx.Colour(217, 217, 217))
        self.c3 = self.dvcBuild.AppendTextColumn("Build", wx.dataview.DATAVIEW_CELL_INERT, 80, wx.ALIGN_LEFT, 0)
        self.c4 = self.dvcBuild.AppendTextColumn("Name", wx.dataview.DATAVIEW_CELL_INERT, 140, wx.ALIGN_LEFT, 0)
        self.c5 = self.dvcBuild.AppendTextColumn("✖", wx.dataview.DATAVIEW_CELL_INERT, 40, wx.ALIGN_CENTER, 0)
        sidebarBox.Add(self.dvcBuild, 1, wx.ALL, 10)

        self.btn_add_pdf = wx.Button(sidebarPanel, wx.ID_ANY, "➕ Add PDF", wx.DefaultPosition, wx.Size(-1, 40), 0)
        self.btn_add_folder = wx.Button(sidebarPanel, wx.ID_ANY, "➕ Add Folder", wx.DefaultPosition, wx.Size(-1, 40), 0)
        self.btn_load = wx.Button(sidebarPanel, wx.ID_ANY, "🔄 Load Build", wx.DefaultPosition, wx.Size(-1, 40), 0)
        self.btn_refresh = wx.Button(sidebarPanel, wx.ID_ANY, "⬇ Refresh", wx.DefaultPosition, wx.Size(-1, 40), 0)

        for btn in [self.btn_add_pdf, self.btn_add_folder,self.btn_load, self.btn_refresh,]:
            btn.SetBackgroundColour("#8E6E6E")
            btn.SetForegroundColour(wx.Colour(255, 255, 255))
            btn.SetFont(inter_font)
            sidebarBox.Add(btn, 0, wx.ALL | wx.EXPAND, 6)

        sidebarPanel.SetSizer(sidebarBox)
        mainSizer.Add(sidebarPanel, 0, wx.EXPAND, 5)

        # Right panel
        rightSizer = wx.BoxSizer(wx.VERTICAL)

        self.tc = wx.TextCtrl(self, wx.ID_ANY, "", wx.DefaultPosition, wx.DefaultSize,
                              wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        self.tc.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.tc.SetForegroundColour("#2B2B2B")
        self.tc.SetFont(inter_font)
        rightSizer.Add(self.tc, 1, wx.ALL | wx.EXPAND, 10)

        bottomControls = wx.BoxSizer(wx.HORIZONTAL)

        self.text_search = wx.TextCtrl(self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(600, 30), wx.TE_PROCESS_ENTER)
        self.text_search.SetHint("Ask me anything...")
        self.text_search.SetForegroundColour(wx.Colour(0, 0, 0))  # Make search text black
        bottomControls.Add(self.text_search, 0, wx.ALL, 5)


        self.btn_search = wx.Button(self, wx.ID_ANY, "Search", wx.DefaultPosition, wx.Size(140, 30), 0)
        self.btn_search.SetBackgroundColour("#7B3F61")
        self.btn_search.SetForegroundColour(wx.Colour(255, 255, 255))
        bottomControls.Add(self.btn_search, 0, wx.ALL, 5)

        bottomControls.AddStretchSpacer()

        self.btn_settings = wx.Button(self, wx.ID_ANY, "⚙", wx.DefaultPosition, wx.Size(40, 30), 0)
        self.btn_settings.SetBackgroundColour("#7B3F61")
        self.btn_settings.SetForegroundColour(wx.Colour(255, 255, 255))
        self.btn_settings.SetFont(inter_font)
        bottomControls.Add(self.btn_settings, 0, wx.ALL, 5)

        self.btn_help = wx.Button(self, wx.ID_ANY, "Help", wx.DefaultPosition, wx.Size(60, 30), 0)
        self.btn_help.SetBackgroundColour("#7B3F61")
        self.btn_help.SetForegroundColour(wx.Colour(255, 255, 255))
        self.btn_help.SetFont(inter_font)
        bottomControls.Add(self.btn_help, 0, wx.ALL, 5)

        rightSizer.Add(bottomControls, 0, wx.EXPAND, 5)

        mainSizer.Add(rightSizer, 1, wx.EXPAND, 5)

        self.SetSizer(mainSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Bind Events
        self.dvc.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.pdf_delete)
        self.dvcBuild.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.delete_build)
        self.btn_add_pdf.Bind(wx.EVT_BUTTON, self.pdf_add)
        self.btn_add_folder.Bind(wx.EVT_BUTTON, self.pdf_add)
        self.btn_load.Bind(wx.EVT_BUTTON, self.load_build)
        self.btn_refresh.Bind(wx.EVT_BUTTON, self.pdf_fetch)
        self.text_search.Bind(wx.EVT_TEXT_ENTER, self.query_search)
        self.btn_search.Bind(wx.EVT_BUTTON, self.query_search)
        self.btn_help.Bind(wx.EVT_BUTTON, self.show_help)
        self.btn_settings.Bind(wx.EVT_BUTTON, self.open_settings)

    def __del__(self):
        pass

    def pdf_delete(self, event): event.Skip()
    def delete_build(self, event): event.Skip()
    def pdf_add(self, event): event.Skip()
    def load_build(self, event): event.Skip()
    def pdf_fetch(self, event): event.Skip()
    def query_search(self, event): event.Skip()
    def show_help(self, event): event.Skip()
    def open_settings(self, event): event.Skip()

