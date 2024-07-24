#!/usr/bin/env python3

from functools import partial
import wx

from constants import XMARK_IMG

class TimeKeeperPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0)
        wx.Panel.__init__(self, *args, **kwds)

        self.sz = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Project"), wx.HORIZONTAL)

        self.button_off = wx.ToggleButton(self, wx.ID_ANY, "OFF")
        self.sz.Add(self.button_off, 0, wx.ALL, 5)

        self.SetSizer(self.sz)

        self.Layout()
class TimeKeeperFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Time Keeper")

        # Menu Bar
        self.frame_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        item = wxglade_tmp_menu.Append(wx.ID_ANY, "See times", "")
        self.Bind(wx.EVT_MENU, self.show_times, item)
        wxglade_tmp_menu.Append(wx.ID_EXIT, "Exit", "")
        self.Bind(wx.EVT_MENU, lambda evt: self.Close(), id=wx.ID_EXIT)
        self.frame_menubar.Append(wxglade_tmp_menu, "File")

        self.timemenu = wx.Menu()
        self.frame_menubar.Append(self.timemenu, "Times")
        self.SetMenuBar(self.frame_menubar)
        # Menu Bar end

        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusWidths([-1])
        # statusbar fields
        statusbar_fields = ["Ready"]
        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)

        framesizer = wx.BoxSizer(wx.VERTICAL)

        self.main_panel = TimeKeeperPanel(self, wx.ID_ANY)
        framesizer.Add(self.main_panel, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)

        self.SetSizer(framesizer)
        framesizer.Fit(self)

        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.on_close, self)

    def show_times(self, event):
        print("Event handler 'show_times' not implemented!")
        event.Skip()

    def on_close(self, event):
        print("Event handler 'on_close' not implemented!")
        event.Skip()

    def make_menuitem(self, task, callback):
        item = self.timemenu.Append(wx.ID_ANY, task, "")
        self.Bind(wx.EVT_MENU, partial(callback, task), item)

    def make_btn(self, name):
        btn = wx.ToggleButton(self.main_panel, wx.ID_ANY, name)
        self.main_panel.sz.Add(btn, 0, wx.ALL, 5)
        return btn

class ShowTimes(wx.Dialog):
    def __init__(self, *args, billed_callback=None, **kwds):
        self.billed_callback=billed_callback
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, *args, **kwds)
        self.SetSize((500, 600))
        self.SetTitle("Times by Month")

        sizer_1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Month total times"), wx.VERTICAL)

        self.data = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.HSCROLL | wx.TE_MULTILINE | wx.TE_READONLY)
        sizer_1.Add(self.data, 1, wx.EXPAND, 0)

        self.button_1 = wx.Button(self, wx.ID_ANY, "Close")
        sizer_1.Add(self.button_1, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 3)
        self.Bind(wx.EVT_BUTTON, lambda evt:self.Close(), self.button_1)

        if billed_callback:
            billed = wx.Button(self, wx.ID_ANY, "Set this as billed today.")
            sizer_1.Add(billed, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 3)
            billed.Bind(wx.EVT_BUTTON, self.on_billed)

        self.SetSizer(sizer_1)
        self.Layout()

    def on_billed(self, event=None):
        self.Close()
        callback, task = self.billed_callback
        callback(task)

class AlreadyRunningFrameCore(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((450, 200))
        self.SetTitle("Load error")

        self.panel_1 = wx.Panel(self, wx.ID_ANY)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(sizer_3, 1, wx.EXPAND, 0)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(sizer_2, 0, 0, 0)

        sizer_2.Add((20, 20), 1, wx.ALL, 0)

        bitmap_1 = wx.StaticBitmap(self.panel_1, wx.ID_ANY, wx.Bitmap(str(XMARK_IMG), wx.BITMAP_TYPE_ANY))
        sizer_2.Add(bitmap_1, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        self.error_text = wx.StaticText(self.panel_1, wx.ID_ANY, "Error!\nThe program is already running!")
        sizer_2.Add(self.error_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)

        sizer_2.Add((20, 20), 1, 0, 0)

        sizer_3.Add((20, 20), 1, 0, 0)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(sizer_4, 1, wx.EXPAND, 0)

        sizer_4.Add((20, 20), 1, 0, 0)

        self.continue_anyway = wx.Button(self.panel_1, wx.ID_ANY, "Hush, I know.")
        sizer_4.Add(self.continue_anyway, 0, 0, 0)

        sizer_4.Add((20, 20), 1, 0, 0)

        self.panel_1.SetSizer(sizer_1)

        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.continue_now, self.continue_anyway)

    def continue_now(self, event):
        print("Event handler 'continue_now' not implemented!")
        event.Skip()

class MyApp(wx.App):
    def OnInit(self):
        self.frame = TimeKeeperFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
