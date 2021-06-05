# Ordineu's twitch finder

# For grabbing screenshot / displaying GUI
import wx, win32api, win32gui, win32con, ctypes

# For computer vision
import cv2
import numpy as np

# For sound
from playsound import playsound

import datetime
import os

monitorToTrack = 0
if os.path.isfile("reward.cfg"):
    with open("reward.cfg", 'r') as f:
        monitorToTrack = int(f.read())

template = cv2.imread("RewardReady.png")

class Frame(wx.Frame):
    def __init__(self, *args, **kwargs):
        self.dll = ctypes.WinDLL('gdi32.dll')
        super(Frame, self).__init__(*args, **kwargs)
        self.InitUI()
        self.buf = None
        self.OnTimer()

    def InitUI(self):
        self.panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Monitor input
        monitorPanel = wx.Panel(self.panel)
        m_hbox = wx.BoxSizer(wx.HORIZONTAL)
        monitorLabel = wx.StaticText(monitorPanel, label="Monitor #: ")
        self.monitor = wx.SpinCtrl(monitorPanel, value=str(monitorToTrack))
        self.monitor.Bind(wx.EVT_TEXT, self.SetMonitor)
        m_hbox.Add(monitorLabel, wx.LEFT)
        m_hbox.Add(self.monitor, wx.EXPAND)
        monitorPanel.SetSizer(m_hbox)

        # Monitor preview
        self.preview = wx.StaticBitmap(self.panel, size=wx.Size(240, 180))

        self.results = wx.StaticText(self.panel, label="")
        vbox.Add(monitorPanel)
        vbox.Add(self.preview, wx.CENTER)
        vbox.Add(self.results)
        self.panel.SetSizer(vbox)

    def SetMonitor(self, e):
        global monitorToTrack

        newMonitorToTrack = int(e.GetString())
        maxMonitors = len(win32api.EnumDisplayMonitors(None, None)[monitorToTrack]) - 1
        if (newMonitorToTrack) > maxMonitors:
            self.monitor.SetValue(str(maxMonitors))
            return

        monitorToTrack = int(e.GetString())
        self.buf = None

        # Save it in the config
        with open("reward.cfg", 'w') as f:
            f.write(str(monitorToTrack))

    def OnTimer(self):
        now = datetime.datetime.now()
        (hMon, hDC, (left, top, right, bottom)) = win32api.EnumDisplayMonitors(None, None)[monitorToTrack]
        hDeskDC = win32gui.CreateDC(win32api.GetMonitorInfo(hMon)['Device'], None, None)
        bitmap = wx.Bitmap(right - left, bottom - top)
        hMemDC = wx.MemoryDC()
        hMemDC.SelectObject(bitmap)
        try:
            self.dll.BitBlt(hMemDC.GetHDC(), 0, 0, right - left, bottom - top, int(hDeskDC), 0, 0, win32con.SRCCOPY)
        finally:
            hMemDC.SelectObject(wx.NullBitmap)
        win32gui.ReleaseDC(win32gui.GetDesktopWindow(), hDeskDC)

        # Now that we have a screenshot in screenshot.bmp, load it up in cv2
        if self.buf is None:
            bufSize = tuple(bitmap.GetSize())
            self.buf = np.empty((bufSize[1], bufSize[0], 3), np.uint8)
        bitmap.CopyToBuffer(self.buf, format=wx.BitmapBufferFormat_RGB)

        # Note that wx bitmaps are in RGB format, whereas CV2 uses BGR, so we need to convert
        self.buf = cv2.cvtColor(self.buf, cv2.COLOR_BGR2RGB)
        result = cv2.matchTemplate(self.buf, template, cv2.TM_CCOEFF_NORMED)
        minScore, maxScore, minLoc, maxLoc = cv2.minMaxLoc(result)
        callDelay = 500
        if maxScore > 0.8:
            # This is good enough, play a sound
            playsound('SFX_-_coin_04.mp3', False)
            callDelay = 3000
        self.preview.SetBitmap(wx.BitmapFromImage(wx.ImageFromBitmap(bitmap).Scale(240, 180)))
        self.results.SetLabel("Processing time: " + str((datetime.datetime.now()-now).microseconds / 1000) + "ms")
        wx.CallLater(callDelay, self.OnTimer)

app = wx.App()
frame = Frame(None, title="OrdiNeu's Twitch Reward-finder", style=wx.CLOSE_BOX | wx.CAPTION | wx.RESIZE_BORDER | wx.MINIMIZE_BOX)
frame.Show()
app.MainLoop()
