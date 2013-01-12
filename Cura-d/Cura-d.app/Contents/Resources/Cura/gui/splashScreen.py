# coding=utf-8
from __future__ import absolute_import

import wx._core #We only need the core here, which speeds up the import. As we want to show the splashscreen ASAP.

from Cura.util.resources import getPathForImage

class splashScreen(wx.SplashScreen):
	def __init__(self, callback):
		self.callback = callback
		bitmap = wx.Bitmap(getPathForImage('splash.png'))
		super(splashScreen, self).__init__(bitmap, wx.SPLASH_CENTRE_ON_SCREEN, 0, None)
		wx.CallAfter(self.DoCallback)

	def DoCallback(self):
		self.callback()
		self.Destroy()
