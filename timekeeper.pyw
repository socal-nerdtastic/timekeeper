#!/usr/bin/env python3

import json
from pathlib import Path
import platform
import getpass
import os
import time
from functools import partial

import moduleinstaller
moduleinstaller.gui_check_and_prompt({"wx":"wxpython"})
import wx

from timekeeper_wxg import ShowTimes, TimeKeeperFrame, AlreadyRunningFrameCore
from timeclock import Timeclock

from constants import SETTING_FILE, LOGO_FILE, SENTINEL_FILE, STAY_ON_TOP, SETTING_DEFAULT

def id_yourself():
    return f"User {getpass.getuser()!r} on {platform.node()} ({platform.system()}) @ {time.strftime('%Y-%m-%d_%H:%M')}"

def load_settings():
    try:
        with open(SETTING_FILE) as f:
            settings = json.load(f)
        print("Loaded", SETTING_FILE)
    except FileNotFoundError:
        settings = SETTING_DEFAULT
    except Exception as e:
        print("unexpected load error:", e)
        settings = SETTING_DEFAULT
    return settings

def save_settings(settings):
    with open(SETTING_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def set_position(frame, old_position):
    """restore the last screen position if it fits on the current screen"""
    BUFFER = 30 # min px from right, bottom
    oldx, oldy = old_position
    # ~ screen_w, screen_h = wx.DisplaySize() # does not work on python3.9 / wx 4.1.1
    screen_w, screen_h = 0,0
    for i in range(wx.Display.GetCount()):
        x, y, w, h = wx.Display(i).GetGeometry()
        if x+w > screen_w:
            screen_w = x+w
        if y+h > screen_h:
            screen_h = y+h

    if (oldx-BUFFER < screen_w) and (oldy-BUFFER < screen_h):
        frame.SetPosition(old_position)
        print('restored')
    # else wx python will choose

class TimeKeeperGUI(TimeKeeperFrame):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.SetIcon(wx.Icon(str(LOGO_FILE)))
        SENTINEL_FILE.write_text(id_yourself())

        self.buttons = [self.main_panel.button_off]
        self.buttons += [self.make_btn(name) for name in settings["tasks"]]
        for name in settings["tasks"]:
            self.make_menuitem(name, self.show_specific_time)
        self.timeclock = Timeclock()
        self.Bind(wx.EVT_TOGGLEBUTTON, self.btn_toggle)
        if STAY_ON_TOP:
            self.ToggleWindowStyle(wx.STAY_ON_TOP)
        set_position(self,settings['position'])
        self.main_panel.button_off.SetValue(True)

        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self.update_statusbar)
        self.timer.Start(1000*10) # update every 10 seconds

    def update_statusbar(self, event=None):
        self.statusbar.SetStatusText(self.timeclock.report())

    def btn_toggle(self, event=None):
        clicked = event.EventObject
        for btn in self.buttons:
            if clicked is btn:
                btn.SetValue(True)
                self.timeclock.clock_in(btn.GetLabel())
            else:
                btn.SetValue(False)
        self.timeclock.save()
        self.update_statusbar()

    def on_close(self, event:wx.Event=None):
        print(f"CLOSING. Size:{self.GetSize()}, Position: {self.GetPosition()}")
        self.timeclock.save()
        settings['position'] = tuple(self.GetPosition())
        save_settings(settings)
        SENTINEL_FILE.write_text("")
        event.Skip()

    def show_specific_time(self, task, event=None):
        try:
            dlg = ShowTimes(self, billed_callback=(self.timeclock.clock_billpoint, task))
            dlg.data.SetValue(self.timeclock.taskreport(task))
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    def show_times(self, event=None):
        try:
            dlg = ShowTimes(self)
            dlg.data.SetValue(self.timeclock.monthreport())
            dlg.ShowModal()
        finally:
            dlg.Destroy()

class AlreadyRunningFrame(AlreadyRunningFrameCore):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        old = self.error_text.GetLabel()
        new = f"\nby:\n{SENTINEL_FILE.read_text().strip()}"
        self.error_text.SetLabel(old + new)
        wx.CallLater(10000, self.Destroy)
        self.Layout()

    def continue_now(self, event):
        self.frm = TimeKeeperGUI(None, wx.ID_ANY, "")
        wx.App.Get().SetTopWindow(self.frm)
        self.frm.Show()
        self.Destroy()
        event.Skip()

class MyApp(wx.App):
    def OnInit(self):
        self.frm = TimeKeeperGUI(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frm)
        self.frm.Show()
        return True

class AlreadyRunnigApp(wx.App):
    def OnInit(self):
        self.frm = AlreadyRunningFrame(None, wx.ID_ANY)
        self.frm.Show()
        return True

def normal_run():
    app = MyApp(0)
    app.MainLoop()

def error_run():
    app = AlreadyRunnigApp(0)
    app.MainLoop()

def main():
    global settings
    settings = load_settings()
    if SENTINEL_FILE.exists() and SENTINEL_FILE.read_text().strip():
        error_run()
    else:
        normal_run()

if __name__ == "__main__":
    main()
