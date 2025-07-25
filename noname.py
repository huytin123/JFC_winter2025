import wx
import wx.xrc
import wx.dataview
import wx.richtext  # Added for RichTextCtrl

myEVT_CUSTOM_BUTTON = wx.NewEventType()
EVT_CUSTOM_BUTTON = wx.PyEventBinder(myEVT_CUSTOM_BUTTON, 1)

class CustomButtonEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        super().__init__(evtType, id)
        self.SetEventType(evtType)

# Define CustomButton class
class CustomButton(wx.Panel):
    def __init__(self, parent, label, size, bg_color=None):
        super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, size, wx.NO_BORDER)
        self.label = label
        self.bg_color = bg_color if bg_color else wx.Colour(173, 216, 230)  # Default light blue (#ADD8E6)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_LEFT_UP, self.on_release)
        self.is_pressed = False

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        # Set up rounded rectangle
        width, height = self.GetSize()
        r = 15  # Radius for rounded corners
        path = gc.CreatePath()
        path.AddRoundedRectangle(0, 0, width, height, r)

        # Fill with background color
        gc.SetBrush(wx.Brush(self.bg_color))
        gc.DrawPath(path)

        # # Add subtle 3D effect (shadow)
        # gc.SetBrush(wx.Brush(wx.Colour(200, 220, 240, 100)))  # Light shadow
        # gc.DrawRectangle(2, 2, width - 4, height - 4)

        # Draw text
        sfpro_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "SF Pro Display")
        gc.SetFont(sfpro_font, wx.Colour(0, 0, 0))  # Black text
        tw, th = gc.GetTextExtent(self.label)
        gc.DrawText(self.label, (width - tw) / 2, (height - th) / 2)

    def on_click(self, event):
        self.is_pressed = True
        self.Refresh()  # Redraw when clicked

    def on_release(self, event):
        self.is_pressed = False
        self.Refresh()

        # Fire the custom event to parent
        evt = CustomButtonEvent(myEVT_CUSTOM_BUTTON, self.GetId())
        evt.SetEventObject(self)
        wx.PostEvent(self.GetParent(), evt)

# Main Frame Class
class MyFrame1(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title="Smart PDF Search", pos=wx.DefaultPosition,
                          size=wx.Size(1188, 768), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetBackgroundColour("#FFFFFF")
        self.SetDoubleBuffered(True)
        sfpro_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "SF Pro Display")
        self.SetFont(sfpro_font)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        # Sidebar
        sidebarPanel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(280, -1))
        sidebarPanel.SetBackgroundColour("#04547C")  # Navy blue
        sidebarBox = wx.BoxSizer(wx.VERTICAL)

        self.dvc = wx.dataview.DataViewListCtrl(sidebarPanel, wx.ID_ANY, wx.DefaultPosition, wx.Size(260, 400), 0)
        self.dvc.SetBackgroundColour(wx.Colour("#04547C"))  # Soft light blue
        self.c1 = self.dvc.AppendTextColumn("Documents", wx.dataview.DATAVIEW_CELL_INERT, 220, wx.ALIGN_LEFT, 0)
        self.c2 = self.dvc.AppendTextColumn("✖", wx.dataview.DATAVIEW_CELL_INERT, 40, wx.ALIGN_CENTER, 0)
        sidebarBox.Add(self.dvc, 1, wx.ALL, 10)

        self.dvcBuild = wx.dataview.DataViewListCtrl(sidebarPanel, wx.ID_ANY, wx.DefaultPosition, wx.Size(260, 100), 0)
        self.dvcBuild.SetBackgroundColour(wx.Colour("#04547C"))
        self.c3 = self.dvcBuild.AppendTextColumn("Database", wx.dataview.DATAVIEW_CELL_INERT, 80, wx.ALIGN_LEFT, 0)
        self.c4 = self.dvcBuild.AppendTextColumn("Name", wx.dataview.DATAVIEW_CELL_INERT, 140, wx.ALIGN_LEFT, 0)
        self.c5 = self.dvcBuild.AppendTextColumn("✖", wx.dataview.DATAVIEW_CELL_INERT, 40, wx.ALIGN_CENTER, 0)
        sidebarBox.Add(self.dvcBuild, 1, wx.ALL, 10)

        # Button definitions with custom buttons
        self.btn_add = CustomButton(sidebarPanel, "Add PDF", wx.Size(150, 35))
        self.btn_add_folder = CustomButton(sidebarPanel, "Add Folder", wx.Size(150, 35))
        self.btn_load = CustomButton(sidebarPanel, "Load Database", wx.Size(150, 35))
        self.btn_refresh = CustomButton(sidebarPanel, "Refresh", wx.Size(150, 35))

        self.btn_add.SetBackgroundColour(wx.Colour("#04547C"))
        self.btn_add_folder.SetBackgroundColour(wx.Colour("#04547C"))
        self.btn_load.SetBackgroundColour(wx.Colour("#04547C"))
        self.btn_refresh.SetBackgroundColour(wx.Colour("#04547C"))
        
        # Ensure buttons are not in another sizer before adding
        for btn in [self.btn_add, self.btn_add_folder, self.btn_load, self.btn_refresh]:
            btn.Reparent(sidebarPanel)  # Re-parent to ensure clean slate
            if btn.GetContainingSizer():
                btn.GetContainingSizer().Detach(btn)  # Detach from any existing sizer
            btn.SetFont(sfpro_font)
            sidebarBox.Add(btn, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=2)  # Small border for spacing

        sidebarBox.AddSpacer(10)  

        sidebarPanel.SetSizer(sidebarBox)
        mainSizer.Add(sidebarPanel, 0, wx.EXPAND, 5)

        # Right panel
        rightSizer = wx.BoxSizer(wx.VERTICAL)

        heading_panel = wx.Panel(self)
        heading_sizer = wx.BoxSizer(wx.HORIZONTAL)

        vinsi_img = wx.Image("logo/vinsi1.png", wx.BITMAP_TYPE_PNG).Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        logo_vinsi = wx.StaticBitmap(heading_panel, bitmap=wx.Bitmap(vinsi_img))

        jfc_img = wx.Image("logo/jfc.png", wx.BITMAP_TYPE_PNG).Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        logo_jfc = wx.StaticBitmap(heading_panel, bitmap=wx.Bitmap(jfc_img))

        usyd_img = wx.Image("logo/usyd.png", wx.BITMAP_TYPE_PNG).Scale(50, 50, wx.IMAGE_QUALITY_HIGH)
        logo_usyd = wx.StaticBitmap(heading_panel, bitmap=wx.Bitmap(usyd_img))

        heading = wx.StaticText(heading_panel, label="Query Results")
        heading_font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "SF Pro Display")
        heading.SetFont(heading_font)
        heading.SetForegroundColour("#04547C")  # Dark blue text

        self.btn_help = CustomButton(heading_panel, "Help", wx.Size(60, 30), bg_color=wx.Colour("#564D7C"))
        self.btn_help.SetBackgroundColour("#FFFFFF")
        self.btn_help.SetFont(sfpro_font)

        # Layout to align Help button to the right and push heading right
        heading_sizer.AddSpacer(20)
        heading_sizer.Add(logo_vinsi, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        heading_sizer.Add(logo_usyd, 0, wx.ALIGN_CENTER_VERTICAL| wx.RIGHT, 10)
        heading_sizer.Add(logo_jfc, 0, wx.ALIGN_CENTER_VERTICAL| wx.RIGHT, 10)
        heading_sizer.AddSpacer(150) 
        heading_sizer.Add(heading, 0, wx.ALIGN_CENTER_VERTICAL | wx.CENTER)
        heading_sizer.AddSpacer(300)
        heading_sizer.Add(self.btn_help, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)  # Help button
        heading_panel.SetSizer(heading_sizer)

        rightSizer.Add(heading_panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)

        # RichTextCtrl for query results
        self.tc = wx.richtext.RichTextCtrl(self, wx.ID_ANY, "", wx.DefaultPosition, wx.DefaultSize,
                                        wx.richtext.RE_MULTILINE | wx.richtext.RE_READONLY)
        self.tc.SetBackgroundColour("#FFFFFF")  # White main workspace
        self.tc.SetFont(sfpro_font)
        rightSizer.Add(self.tc, 1, wx.ALL | wx.EXPAND, 10)

        # Adjust the bottom controls to push the query text right
        bottomControls = wx.BoxSizer(wx.HORIZONTAL)
        self.text_search_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(600, 36))
        self.text_search_panel.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.text_search_panel.Bind(wx.EVT_PAINT, self.on_text_search_paint)

        self.text_search = wx.TextCtrl(self.text_search_panel, wx.ID_ANY, "", wx.Point(3, 3), wx.Size(594, 30), wx.TE_PROCESS_ENTER | wx.BORDER_SIMPLE)
        self.text_search.SetBackgroundColour(wx.Colour(255, 255, 255))  # White background
        self.text_search.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
        self.text_search.SetFont(sfpro_font)

        self.placeholder_text = wx.StaticText(self.text_search_panel, wx.ID_ANY, "Ask me anything...", wx.Point(8, 3))
        self.placeholder_text.SetForegroundColour(wx.Colour(128, 128, 128))  # Greyish placeholder
        self.placeholder_text.SetFont(sfpro_font)
        self.placeholder_text.Show(not self.text_search.GetValue())

        self.text_search.Bind(wx.EVT_TEXT, self.on_text_search_change)
        self.text_search.Bind(wx.EVT_SET_FOCUS, self.on_text_search_focus)
        self.text_search.Bind(wx.EVT_KILL_FOCUS, self.on_text_search_focus)

        self.btn_search = CustomButton(self, "Search", wx.Size(100, 30))
        self.btn_settings = CustomButton(self, "⚙", wx.Size(40, 30))
        self.btn_clear = CustomButton(self, "X", wx.Size(40, 30))
        self.btn_settings.SetFont(sfpro_font)

        self.btn_search.SetBackgroundColour("#FFFFFF")
        self.btn_settings.SetBackgroundColour("#FFFFFF")
        self.btn_clear.SetBackgroundColour("#FFFFFF")

        # Push query box and buttons to the right
        bottomControls.AddStretchSpacer(prop=2)  # Increased left spacer to push right
        bottomControls.Add(self.text_search_panel, 0, wx.ALL, 5)
        bottomControls.Add(self.btn_search, 0, wx.ALL, 5)
        bottomControls.Add(self.btn_settings, 0, wx.ALL, 5)
        bottomControls.Add(self.btn_clear, 0, wx.ALL, 5)
        bottomControls.AddStretchSpacer(prop=1)  # Right spacer

        rightSizer.Add(bottomControls, 0, wx.EXPAND, 5)

        mainSizer.Add(rightSizer, 1, wx.EXPAND, 5)

        self.SetSizer(mainSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Bind Events
        self.dvc.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.pdf_delete)
        self.dvcBuild.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.delete_build)
        self.Bind(EVT_CUSTOM_BUTTON, self.pdf_add, self.btn_add)
        self.Bind(EVT_CUSTOM_BUTTON, self.pdf_add, self.btn_add_folder)
        self.Bind(EVT_CUSTOM_BUTTON, self.load_build, self.btn_load)
        self.Bind(EVT_CUSTOM_BUTTON, self.pdf_fetch, self.btn_refresh)
        self.text_search.Bind(wx.EVT_TEXT_ENTER, self.query_search)

        # self.btn_search.Bind(wx.EVT_BUTTON, self.query_search)
        # self.btn_help.Bind(wx.EVT_BUTTON, self.show_help)
        # self.btn_settings.Bind(wx.EVT_BUTTON, self.open_settings)
        # self.btn_clear.Bind(wx.EVT_BUTTON, self.clear_tc)
        self.Bind(wx.EVT_CLOSE, self.close_threads)

        self.Bind(EVT_CUSTOM_BUTTON, self.query_search, self.btn_search)
        self.Bind(EVT_CUSTOM_BUTTON, self.show_help, self.btn_help)
        self.Bind(EVT_CUSTOM_BUTTON, self.open_settings, self.btn_settings)
        self.Bind(EVT_CUSTOM_BUTTON, self.clear_tc, self.btn_clear)
        self.tc.Bind(wx.EVT_TEXT_URL, self.on_url_click)

    def on_text_search_paint(self, event):
        dc = wx.PaintDC(self.text_search_panel)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        width, height = self.text_search_panel.GetSize()
        r = 10  # Smaller radius for shadow
        path = gc.CreatePath()
        path.AddRoundedRectangle(0, 0, width, height, r)
        gc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))  # White background
        gc.SetPen(wx.Pen(wx.Colour(50, 50, 50), 2))  # Dark grey border
        gc.DrawPath(path)

        # Draw shadow
        gc.SetBrush(wx.Brush(wx.Colour(100, 100, 100, 120)))  # Grey shadow
        gc.DrawRectangle(3, 3, width - 6, height - 6)

    def on_text_search_change(self, event):
        self.placeholder_text.Show(not self.text_search.GetValue())
        event.Skip()

    def on_text_search_focus(self, event):
        self.placeholder_text.Show(not self.text_search.GetValue() and not self.text_search.HasFocus())
        event.Skip()

    def __del__(self):
        pass

    def pdf_delete(self, event): event.Skip()
    def pdf_add(self, event): event.Skip()
    def load_build(self, event): event.Skip()
    def pdf_fetch(self, event): event.Skip()
    def query_search(self, event): event.Skip()
    def show_help(self, event): event.Skip()
    def open_settings(self, event): event.Skip()
    def close_threads(self, event): event.Skip()
    def on_url_click(self, event): event.Skip()
    def clear_tc(self, event): event.Skip()

if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame1(None)
    frame.Show(True)
    app.MainLoop()
