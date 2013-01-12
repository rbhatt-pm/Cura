# coding=utf-8
from __future__ import absolute_import

import webbrowser
import threading
import time
import math

import wx
import wx.wizard

from Cura.gui import firmwareInstall
from Cura.gui import printWindow
from Cura.util import machineCom
from Cura.util import profile
from Cura.util.resources import getPathForImage

class InfoBox(wx.Panel):
	def __init__(self, parent):
		super(InfoBox, self).__init__(parent)
		self.SetBackgroundColour('#FFFF80')

		self.sizer = wx.GridBagSizer(5, 5)
		self.SetSizer(self.sizer)

		self.attentionBitmap = wx.Bitmap(getPathForImage('attention.png'))
		self.errorBitmap = wx.Bitmap(getPathForImage('error.png'))
		self.readyBitmap = wx.Bitmap(getPathForImage('ready.png'))
		self.busyBitmap = [
			wx.Bitmap(getPathForImage('busy-0.png')),
			wx.Bitmap(getPathForImage('busy-1.png')),
			wx.Bitmap(getPathForImage('busy-2.png')),
			wx.Bitmap(getPathForImage('busy-3.png'))
		]

		self.bitmap = wx.StaticBitmap(self, -1, wx.EmptyBitmapRGBA(24, 24, red=255, green=255, blue=255, alpha=1))
		self.text = wx.StaticText(self, -1, '')
		self.extraInfoButton = wx.Button(self, -1, 'i', style=wx.BU_EXACTFIT)
		self.sizer.Add(self.bitmap, pos=(0, 0), flag=wx.ALL, border=5)
		self.sizer.Add(self.text, pos=(0, 1), flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=5)
		self.sizer.Add(self.extraInfoButton, pos=(0,2), flag=wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, border=5)
		self.sizer.AddGrowableCol(1)

		self.extraInfoButton.Show(False)

		self.extraInfoUrl = ''
		self.busyState = None
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.doBusyUpdate, self.timer)
		self.Bind(wx.EVT_BUTTON, self.doExtraInfo, self.extraInfoButton)
		self.timer.Start(100)

	def SetInfo(self, info):
		self.SetBackgroundColour('#FFFF80')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(False)
		self.Refresh()

	def SetError(self, info, extraInfoUrl):
		self.extraInfoUrl = extraInfoUrl
		self.SetBackgroundColour('#FF8080')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(True)
		self.Layout()
		self.SetErrorIndicator()
		self.Refresh()

	def SetAttention(self, info):
		self.SetBackgroundColour('#FFFF80')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(False)
		self.SetAttentionIndicator()
		self.Layout()
		self.Refresh()

	def SetBusy(self, info):
		self.SetInfo(info)
		self.SetBusyIndicator()

	def SetBusyIndicator(self):
		self.busyState = 0
		self.bitmap.SetBitmap(self.busyBitmap[self.busyState])

	def doExtraInfo(self, e):
		webbrowser.open(self.extraInfoUrl)

	def doBusyUpdate(self, e):
		if self.busyState is None:
			return
		self.busyState += 1
		if self.busyState >= len(self.busyBitmap):
			self.busyState = 0
		self.bitmap.SetBitmap(self.busyBitmap[self.busyState])

	def SetReadyIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.readyBitmap)

	def SetErrorIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.errorBitmap)

	def SetAttentionIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.attentionBitmap)


class InfoPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent, title):
		wx.wizard.WizardPageSimple.__init__(self, parent)

		sizer = wx.GridBagSizer(5, 5)
		self.sizer = sizer
		self.SetSizer(sizer)

		title = wx.StaticText(self, -1, title)
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		sizer.Add(title, pos=(0, 0), span=(1, 2), flag=wx.ALIGN_CENTRE | wx.ALL)
		sizer.Add(wx.StaticLine(self, -1), pos=(1, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		sizer.AddGrowableCol(1)

		self.rowNr = 2

	def AddText(self, info):
		text = wx.StaticText(self, -1, info)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return text

	def AddSeperator(self):
		self.GetSizer().Add(wx.StaticLine(self, -1), pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1

	def AddHiddenSeperator(self):
		self.AddText('')

	def AddInfoBox(self):
		infoBox = InfoBox(self)
		self.GetSizer().Add(infoBox, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
		self.rowNr += 1
		return infoBox

	def AddRadioButton(self, label, style=0):
		radio = wx.RadioButton(self, -1, label, style=style)
		self.GetSizer().Add(radio, pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1
		return radio

	def AddCheckbox(self, label, checked=False):
		check = wx.CheckBox(self, -1)
		text = wx.StaticText(self, -1, label)
		check.SetValue(checked)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(check, pos=(self.rowNr, 1), span=(1, 2), flag=wx.ALL)
		self.rowNr += 1
		return check

	def AddButton(self, label):
		button = wx.Button(self, -1, label)
		self.GetSizer().Add(button, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT)
		self.rowNr += 1
		return button

	def AddDualButton(self, label1, label2):
		button1 = wx.Button(self, -1, label1)
		self.GetSizer().Add(button1, pos=(self.rowNr, 0), flag=wx.RIGHT)
		button2 = wx.Button(self, -1, label2)
		self.GetSizer().Add(button2, pos=(self.rowNr, 1))
		self.rowNr += 1
		return button1, button2

	def AddTextCtrl(self, value):
		ret = wx.TextCtrl(self, -1, value)
		self.GetSizer().Add(ret, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT)
		self.rowNr += 1
		return ret

	def AddLabelTextCtrl(self, info, value):
		text = wx.StaticText(self, -1, info)
		ret = wx.TextCtrl(self, -1, value)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		self.GetSizer().Add(ret, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT)
		self.rowNr += 1
		return ret

	def AddTextCtrlButton(self, value, buttonText):
		text = wx.TextCtrl(self, -1, value)
		button = wx.Button(self, -1, buttonText)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		self.GetSizer().Add(button, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT)
		self.rowNr += 1
		return text, button

	def AddBitmap(self, bitmap):
		bitmap = wx.StaticBitmap(self, -1, bitmap)
		self.GetSizer().Add(bitmap, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return bitmap

	def AddCheckmark(self, label, bitmap):
		check = wx.StaticBitmap(self, -1, bitmap)
		text = wx.StaticText(self, -1, label)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(check, pos=(self.rowNr, 1), span=(1, 1), flag=wx.ALL)
		self.rowNr += 1
		return check

	def AllowNext(self):
		return True

	def StoreData(self):
		pass


class FirstInfoPage(InfoPage):
	def __init__(self, parent):
		super(FirstInfoPage, self).__init__(parent, "First time run wizard")
		self.AddText('Welcome, and thanks for trying Cura!')
		self.AddSeperator()
		self.AddText('This wizard will help you with the following steps:')
		self.AddText('* Configure Cura for your machine')
		self.AddText('* Upgrade your firmware')
		self.AddText('* Check if your machine is working safely')
		self.AddText('* Level your printer bed')

		#self.AddText('* Calibrate your machine')
		#self.AddText('* Do your first print')


class RepRapInfoPage(InfoPage):
	def __init__(self, parent):
		super(RepRapInfoPage, self).__init__(parent, "RepRap information")
		self.AddText(
			'RepRap machines are vastly different, and there is no\ndefault configuration in Cura for any of them.')
		self.AddText('If you like a default profile for your machine added,\nthen make an issue on github.')
		self.AddSeperator()
		self.AddText('You will have to manually install Marlin or Sprinter firmware.')
		self.AddSeperator()
		self.machineWidth = self.AddLabelTextCtrl('Machine width (mm)', '80')
		self.machineDepth = self.AddLabelTextCtrl('Machine depth (mm)', '80')
		self.machineHeight = self.AddLabelTextCtrl('Machine height (mm)', '60')
		self.nozzleSize = self.AddLabelTextCtrl('Nozzle size (mm)', '0.5')
		self.heatedBed = self.AddCheckbox('Heated bed')
		self.HomeAtCenter = self.AddCheckbox('Bed center is 0,0,0 (RoStock)')

	def StoreData(self):
		profile.putPreference('machine_width', self.machineWidth.GetValue())
		profile.putPreference('machine_depth', self.machineDepth.GetValue())
		profile.putPreference('machine_height', self.machineHeight.GetValue())
		profile.putProfileSetting('nozzle_size', self.nozzleSize.GetValue())
		profile.putProfileSetting('wall_thickness', float(profile.getProfileSettingFloat('nozzle_size')) * 2)
		profile.putPreference('has_heated_bed', str(self.heatedBed.GetValue()))
		profile.putPreference('machine_center_is_zero', str(self.HomeAtCenter.GetValue()))


class MachineSelectPage(InfoPage):
	def __init__(self, parent):
		super(MachineSelectPage, self).__init__(parent, "Select your machine")
		self.AddText('What kind of machine do you have:')

		self.UltimakerRadio = self.AddRadioButton("Ultimaker", style=wx.RB_GROUP)
		self.UltimakerRadio.SetValue(True)
		self.UltimakerRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimakerSelect)
		self.OtherRadio = self.AddRadioButton("Other (Ex: RepRap)")
		self.OtherRadio.Bind(wx.EVT_RADIOBUTTON, self.OnOtherSelect)

	def OnUltimakerSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().ultimakerFirmwareUpgradePage)

	def OnOtherSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().repRapInfoPage)

	def StoreData(self):
		if self.UltimakerRadio.GetValue():
			profile.putPreference('machine_width', '205')
			profile.putPreference('machine_depth', '205')
			profile.putPreference('machine_height', '200')
			profile.putPreference('machine_type', 'ultimaker')
			profile.putPreference('machine_center_is_zero', 'False')
			profile.putProfileSetting('nozzle_size', '0.4')
		else:
			profile.putPreference('machine_width', '80')
			profile.putPreference('machine_depth', '80')
			profile.putPreference('machine_height', '60')
			profile.putPreference('machine_type', 'reprap')
			profile.putPreference('startMode', 'Normal')
			profile.putProfileSetting('nozzle_size', '0.5')
		profile.putProfileSetting('wall_thickness', float(profile.getProfileSetting('nozzle_size')) * 2)


class SelectParts(InfoPage):
	def __init__(self, parent):
		super(SelectParts, self).__init__(parent, "Select upgraded parts you have")
		self.AddText('To assist you in having better default settings for your Ultimaker\nCura would like to know which upgrades you have in your machine.')
		self.AddSeperator()
		self.springExtruder = self.AddCheckbox('Extruder drive upgrade')
		self.heatedBed = self.AddCheckbox('Heated printer bed (self build)')
		self.dualExtrusion = self.AddCheckbox('Dual extrusion (experimental)')
		self.AddSeperator()
		self.AddText('If you have an Ultimaker bought after october 2012 you will have the\nExtruder drive upgrade. If you do not have this upgrade,\nit is highly recommended to improve reliablity.')
		self.AddText('This upgrade can be bought from the Ultimaker webshop shop\nor found on thingiverse as thing:26094')
		self.springExtruder.SetValue(True)

	def StoreData(self):
		profile.putPreference('ultimaker_extruder_upgrade', str(self.springExtruder.GetValue()))
		profile.putPreference('has_heated_bed', str(self.heatedBed.GetValue()))
		if self.dualExtrusion.GetValue():
			profile.putPreference('extruder_amount', '2')
		else:
			profile.putPreference('extruder_amount', '1')
		if profile.getPreference('ultimaker_extruder_upgrade') == 'True':
			profile.putProfileSetting('retraction_enable', 'True')
		else:
			profile.putProfileSetting('retraction_enable', 'False')


class FirmwareUpgradePage(InfoPage):
	def __init__(self, parent):
		super(FirmwareUpgradePage, self).__init__(parent, "Upgrade Ultimaker Firmware")
		self.AddText(
			'Firmware is the piece of software running directly on your 3D printer.\nThis firmware controls the step motors, regulates the temperature\nand ultimately makes your printer work.')
		self.AddHiddenSeperator()
		self.AddText(
			'The firmware shipping with new Ultimakers works, but upgrades\nhave been made to make better prints, and make calibration easier.')
		self.AddHiddenSeperator()
		self.AddText(
			'Cura requires these new features and thus\nyour firmware will most likely need to be upgraded.\nYou will get the chance to do so now.')
		upgradeButton, skipUpgradeButton = self.AddDualButton('Upgrade to Marlin firmware', 'Skip upgrade')
		upgradeButton.Bind(wx.EVT_BUTTON, self.OnUpgradeClick)
		skipUpgradeButton.Bind(wx.EVT_BUTTON, self.OnSkipClick)
		self.AddHiddenSeperator()
		self.AddText('Do not upgrade to this firmware if:')
		self.AddText('* You have an older machine based on ATMega1280')
		self.AddText('* Have other changes in the firmware')
		button = self.AddButton('Goto this page for a custom firmware')
		button.Bind(wx.EVT_BUTTON, self.OnUrlClick)

	def AllowNext(self):
		return False

	def OnUpgradeClick(self, e):
		if firmwareInstall.InstallFirmware():
			self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()

	def OnSkipClick(self, e):
		self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()

	def OnUrlClick(self, e):
		webbrowser.open('http://daid.mine.nu/~daid/marlin_build/')


class UltimakerCheckupPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCheckupPage, self).__init__(parent, "Ultimaker Checkup")

		self.checkBitmap = wx.Bitmap(getPathForImage('checkmark.png'))
		self.crossBitmap = wx.Bitmap(getPathForImage('cross.png'))
		self.unknownBitmap = wx.Bitmap(getPathForImage('question.png'))
		self.endStopNoneBitmap = wx.Bitmap(getPathForImage('endstop_none.png'))
		self.endStopXMinBitmap = wx.Bitmap(getPathForImage('endstop_xmin.png'))
		self.endStopXMaxBitmap = wx.Bitmap(getPathForImage('endstop_xmax.png'))
		self.endStopYMinBitmap = wx.Bitmap(getPathForImage('endstop_ymin.png'))
		self.endStopYMaxBitmap = wx.Bitmap(getPathForImage('endstop_ymax.png'))
		self.endStopZMinBitmap = wx.Bitmap(getPathForImage('endstop_zmin.png'))
		self.endStopZMaxBitmap = wx.Bitmap(getPathForImage('endstop_zmax.png'))

		self.AddText(
			'It is a good idea to do a few sanity checks now on your Ultimaker.\nYou can skip these if you know your machine is functional.')
		b1, b2 = self.AddDualButton('Run checks', 'Skip checks')
		b1.Bind(wx.EVT_BUTTON, self.OnCheckClick)
		b2.Bind(wx.EVT_BUTTON, self.OnSkipClick)
		self.AddSeperator()
		self.commState = self.AddCheckmark('Communication:', self.unknownBitmap)
		self.tempState = self.AddCheckmark('Temperature:', self.unknownBitmap)
		self.stopState = self.AddCheckmark('Endstops:', self.unknownBitmap)
		self.AddSeperator()
		self.infoBox = self.AddInfoBox()
		self.machineState = self.AddText('')
		self.temperatureLabel = self.AddText('')
		self.errorLogButton = self.AddButton('Show error log')
		self.errorLogButton.Show(False)
		self.AddSeperator()
		self.endstopBitmap = self.AddBitmap(self.endStopNoneBitmap)
		self.comm = None
		self.xMinStop = False
		self.xMaxStop = False
		self.yMinStop = False
		self.yMaxStop = False
		self.zMinStop = False
		self.zMaxStop = False

		self.Bind(wx.EVT_BUTTON, self.OnErrorLog, self.errorLogButton)

	def __del__(self):
		if self.comm != None:
			self.comm.close()

	def AllowNext(self):
		self.endstopBitmap.Show(False)
		return False

	def OnSkipClick(self, e):
		self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()

	def OnCheckClick(self, e=None):
		self.errorLogButton.Show(False)
		if self.comm is not None:
			self.comm.close()
			del self.comm
			self.comm = None
			wx.CallAfter(self.OnCheckClick)
			return
		self.infoBox.SetBusy('Connecting to machine.')
		self.commState.SetBitmap(self.unknownBitmap)
		self.tempState.SetBitmap(self.unknownBitmap)
		self.stopState.SetBitmap(self.unknownBitmap)
		self.checkupState = 0
		self.comm = machineCom.MachineCom(callbackObject=self)

	def OnErrorLog(self, e):
		printWindow.LogWindow('\n'.join(self.comm.getLog()))

	def mcLog(self, message):
		pass

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		if not self.comm.isOperational():
			return
		if self.checkupState == 0:
			self.tempCheckTimeout = 20
			if temp > 70:
				self.checkupState = 1
				wx.CallAfter(self.infoBox.SetInfo, 'Cooldown before temperature check.')
				self.comm.sendCommand('M104 S0')
				self.comm.sendCommand('M104 S0')
			else:
				self.startTemp = temp
				self.checkupState = 2
				wx.CallAfter(self.infoBox.SetInfo, 'Checking the heater and temperature sensor.')
				self.comm.sendCommand('M104 S200')
				self.comm.sendCommand('M104 S200')
		elif self.checkupState == 1:
			if temp < 60:
				self.startTemp = temp
				self.checkupState = 2
				wx.CallAfter(self.infoBox.SetInfo, 'Checking the heater and temperature sensor.')
				self.comm.sendCommand('M104 S200')
				self.comm.sendCommand('M104 S200')
		elif self.checkupState == 2:
			#print "WARNING, TEMPERATURE TEST DISABLED FOR TESTING!"
			if temp > self.startTemp + 40:
				self.checkupState = 3
				wx.CallAfter(self.infoBox.SetAttention, 'Please make sure none of the endstops are pressed.')
				wx.CallAfter(self.endstopBitmap.Show, True)
				wx.CallAfter(self.Layout)
				self.comm.sendCommand('M104 S0')
				self.comm.sendCommand('M104 S0')
				self.comm.sendCommand('M119')
				wx.CallAfter(self.tempState.SetBitmap, self.checkBitmap)
			else:
				self.tempCheckTimeout -= 1
				if self.tempCheckTimeout < 1:
					self.checkupState = -1
					wx.CallAfter(self.tempState.SetBitmap, self.crossBitmap)
					wx.CallAfter(self.infoBox.SetError, 'Temperature measurement FAILED!', 'http://wiki.ultimaker.com/Cura:_Temperature_measurement_problems')
					self.comm.sendCommand('M104 S0')
					self.comm.sendCommand('M104 S0')
		wx.CallAfter(self.temperatureLabel.SetLabel, 'Head temperature: %d' % (temp))

	def mcStateChange(self, state):
		if self.comm is None:
			return
		if self.comm.isOperational():
			wx.CallAfter(self.commState.SetBitmap, self.checkBitmap)
			wx.CallAfter(self.machineState.SetLabel, 'Communication State: %s' % (self.comm.getStateString()))
		elif self.comm.isError():
			wx.CallAfter(self.commState.SetBitmap, self.crossBitmap)
			wx.CallAfter(self.infoBox.SetError, 'Failed to establish connection with the printer.', 'http://wiki.ultimaker.com/Cura:_Connection_problems')
			wx.CallAfter(self.endstopBitmap.Show, False)
			wx.CallAfter(self.machineState.SetLabel, '%s' % (self.comm.getErrorString()))
			wx.CallAfter(self.errorLogButton.Show, True)
			wx.CallAfter(self.Layout)
		else:
			wx.CallAfter(self.machineState.SetLabel, 'Communication State: %s' % (self.comm.getStateString()))

	def mcMessage(self, message):
		if self.checkupState >= 3 and self.checkupState < 10 and 'x_min' in message:
			for data in message.split(' '):
				if ':' in data:
					tag, value = data.split(':', 2)
					if tag == 'x_min':
						self.xMinStop = (value == 'H')
					if tag == 'x_max':
						self.xMaxStop = (value == 'H')
					if tag == 'y_min':
						self.yMinStop = (value == 'H')
					if tag == 'y_max':
						self.yMaxStop = (value == 'H')
					if tag == 'z_min':
						self.zMinStop = (value == 'H')
					if tag == 'z_max':
						self.zMaxStop = (value == 'H')
			self.comm.sendCommand('M119')

			if self.checkupState == 3:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 4
					wx.CallAfter(self.infoBox.SetAttention, 'Please press the right X endstop.')
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopXMaxBitmap)
			elif self.checkupState == 4:
				if not self.xMinStop and self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 5
					wx.CallAfter(self.infoBox.SetAttention, 'Please press the left X endstop.')
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopXMinBitmap)
			elif self.checkupState == 5:
				if self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 6
					wx.CallAfter(self.infoBox.SetAttention, 'Please press the front Y endstop.')
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopYMinBitmap)
			elif self.checkupState == 6:
				if not self.xMinStop and not self.xMaxStop and self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 7
					wx.CallAfter(self.infoBox.SetAttention, 'Please press the back Y endstop.')
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopYMaxBitmap)
			elif self.checkupState == 7:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 8
					wx.CallAfter(self.infoBox.SetAttention, 'Please press the top Z endstop.')
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopZMinBitmap)
			elif self.checkupState == 8:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and self.zMinStop and not self.zMaxStop:
					self.checkupState = 9
					wx.CallAfter(self.infoBox.SetAttention, 'Please press the bottom Z endstop.')
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopZMaxBitmap)
			elif self.checkupState == 9:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and self.zMaxStop:
					self.checkupState = 10
					self.comm.close()
					wx.CallAfter(self.infoBox.SetInfo, 'Checkup finished')
					wx.CallAfter(self.infoBox.SetReadyIndicator)
					wx.CallAfter(self.endstopBitmap.Show, False)
					wx.CallAfter(self.stopState.SetBitmap, self.checkBitmap)
					wx.CallAfter(self.OnSkipClick, None)

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass


class UltimakerCalibrationPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCalibrationPage, self).__init__(parent, "Ultimaker Calibration")

		self.AddText("Your Ultimaker requires some calibration.")
		self.AddText("This calibration is needed for a proper extrusion amount.")
		self.AddSeperator()
		self.AddText("The following values are needed:")
		self.AddText("* Diameter of filament")
		self.AddText("* Number of steps per mm of filament extrusion")
		self.AddSeperator()
		self.AddText("The better you have calibrated these values, the better your prints\nwill become.")
		self.AddSeperator()
		self.AddText("First we need the diameter of your filament:")
		self.filamentDiameter = self.AddTextCtrl(profile.getProfileSetting('filament_diameter'))
		self.AddText(
			"If you do not own digital Calipers that can measure\nat least 2 digits then use 2.89mm.\nWhich is the average diameter of most filament.")
		self.AddText("Note: This value can be changed later at any time.")

	def StoreData(self):
		profile.putProfileSetting('filament_diameter', self.filamentDiameter.GetValue())


class UltimakerCalibrateStepsPerEPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCalibrateStepsPerEPage, self).__init__(parent, "Ultimaker Calibration")

		if profile.getPreference('steps_per_e') == '0':
			profile.putPreference('steps_per_e', '865.888')

		self.AddText("Calibrating the Steps Per E requires some manual actions.")
		self.AddText("First remove any filament from your machine.")
		self.AddText("Next put in your filament so the tip is aligned with the\ntop of the extruder drive.")
		self.AddText("We'll push the filament 100mm")
		self.extrudeButton = self.AddButton("Extrude 100mm filament")
		self.AddText("Now measure the amount of extruded filament:\n(this can be more or less then 100mm)")
		self.lengthInput, self.saveLengthButton = self.AddTextCtrlButton('100', 'Save')
		self.AddText("This results in the following steps per E:")
		self.stepsPerEInput = self.AddTextCtrl(profile.getPreference('steps_per_e'))
		self.AddText("You can repeat these steps to get better calibration.")
		self.AddSeperator()
		self.AddText(
			"If you still have filament in your printer which needs\nheat to remove, press the heat up button below:")
		self.heatButton = self.AddButton("Heatup for filament removal")

		self.saveLengthButton.Bind(wx.EVT_BUTTON, self.OnSaveLengthClick)
		self.extrudeButton.Bind(wx.EVT_BUTTON, self.OnExtrudeClick)
		self.heatButton.Bind(wx.EVT_BUTTON, self.OnHeatClick)

	def OnSaveLengthClick(self, e):
		currentEValue = float(self.stepsPerEInput.GetValue())
		realExtrudeLength = float(self.lengthInput.GetValue())
		newEValue = currentEValue * 100 / realExtrudeLength
		self.stepsPerEInput.SetValue(str(newEValue))
		self.lengthInput.SetValue("100")

	def OnExtrudeClick(self, e):
		threading.Thread(target=self.OnExtrudeRun).start()

	def OnExtrudeRun(self):
		self.heatButton.Enable(False)
		self.extrudeButton.Enable(False)
		currentEValue = float(self.stepsPerEInput.GetValue())
		self.comm = machineCom.MachineCom()
		if not self.comm.isOpen():
			wx.MessageBox(
				"Error: Failed to open serial port to machine\nIf this keeps happening, try disconnecting and reconnecting the USB cable",
				'Printer error', wx.OK | wx.ICON_INFORMATION)
			self.heatButton.Enable(True)
			self.extrudeButton.Enable(True)
			return
		while True:
			line = self.comm.readline()
			if line == '':
				return
			if 'start' in line:
				break
			#Wait 3 seconds for the SD card init to timeout if we have SD in our firmware but there is no SD card found.
		time.sleep(3)

		self.sendGCommand('M302') #Disable cold extrusion protection
		self.sendGCommand("M92 E%f" % (currentEValue))
		self.sendGCommand("G92 E0")
		self.sendGCommand("G1 E100 F600")
		time.sleep(15)
		self.comm.close()
		self.extrudeButton.Enable()
		self.heatButton.Enable()

	def OnHeatClick(self, e):
		threading.Thread(target=self.OnHeatRun).start()

	def OnHeatRun(self):
		self.heatButton.Enable(False)
		self.extrudeButton.Enable(False)
		self.comm = machineCom.MachineCom()
		if not self.comm.isOpen():
			wx.MessageBox(
				"Error: Failed to open serial port to machine\nIf this keeps happening, try disconnecting and reconnecting the USB cable",
				'Printer error', wx.OK | wx.ICON_INFORMATION)
			self.heatButton.Enable(True)
			self.extrudeButton.Enable(True)
			return
		while True:
			line = self.comm.readline()
			if line == '':
				self.heatButton.Enable(True)
				self.extrudeButton.Enable(True)
				return
			if 'start' in line:
				break
			#Wait 3 seconds for the SD card init to timeout if we have SD in our firmware but there is no SD card found.
		time.sleep(3)

		self.sendGCommand('M104 S200') #Set the temperature to 200C, should be enough to get PLA and ABS out.
		wx.MessageBox(
			'Wait till you can remove the filament from the machine, and press OK.\n(Temperature is set to 200C)',
			'Machine heatup', wx.OK | wx.ICON_INFORMATION)
		self.sendGCommand('M104 S0')
		time.sleep(1)
		self.comm.close()
		self.heatButton.Enable(True)
		self.extrudeButton.Enable(True)

	def sendGCommand(self, cmd):
		self.comm.sendCommand(cmd) #Disable cold extrusion protection
		while True:
			line = self.comm.readline()
			if line == '':
				return
			if line.startswith('ok'):
				break

	def StoreData(self):
		profile.putPreference('steps_per_e', self.stepsPerEInput.GetValue())


class configWizard(wx.wizard.Wizard):
	def __init__(self):
		super(configWizard, self).__init__(None, -1, "Configuration Wizard")

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

		self.firstInfoPage = FirstInfoPage(self)
		self.machineSelectPage = MachineSelectPage(self)
		self.ultimakerSelectParts = SelectParts(self)
		self.ultimakerFirmwareUpgradePage = FirmwareUpgradePage(self)
		self.ultimakerCheckupPage = UltimakerCheckupPage(self)
		self.ultimakerCalibrationPage = UltimakerCalibrationPage(self)
		self.ultimakerCalibrateStepsPerEPage = UltimakerCalibrateStepsPerEPage(self)
		self.bedLevelPage = bedLevelWizardMain(self)
		self.repRapInfoPage = RepRapInfoPage(self)

		wx.wizard.WizardPageSimple.Chain(self.firstInfoPage, self.machineSelectPage)
		wx.wizard.WizardPageSimple.Chain(self.machineSelectPage, self.ultimakerSelectParts)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerSelectParts, self.ultimakerFirmwareUpgradePage)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerFirmwareUpgradePage, self.ultimakerCheckupPage)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerCheckupPage, self.bedLevelPage)
		#wx.wizard.WizardPageSimple.Chain(self.ultimakerCalibrationPage, self.ultimakerCalibrateStepsPerEPage)

		self.FitToPage(self.firstInfoPage)
		self.GetPageAreaSizer().Add(self.firstInfoPage)

		self.RunWizard(self.firstInfoPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		self.FindWindowById(wx.ID_BACKWARD).Disable()

class bedLevelWizardMain(InfoPage):
	def __init__(self, parent):
		super(bedLevelWizardMain, self).__init__(parent, "Bed leveling wizard")

		self.AddText('This wizard will help you in leveling your printer bed')
		self.AddSeperator()
		self.AddText('It will do the following steps')
		self.AddText('* Move the printer head to each corner')
		self.AddText('  and let you adjust the height of the bed to the nozzle')
		self.AddText('* Print a line around the bed to check if it is level')
		self.AddSeperator()

		self.connectButton = self.AddButton('Connect to printer')
		self.comm = None

		self.infoBox = self.AddInfoBox()
		self.resumeButton = self.AddButton('Resume')
		self.resumeButton.Enable(False)

		self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connectButton)
		self.Bind(wx.EVT_BUTTON, self.OnResume, self.resumeButton)

	def OnConnect(self, e = None):
		if self.comm is not None:
			self.comm.close()
			del self.comm
			self.comm = None
			wx.CallAfter(self.OnConnect)
			return
		self.connectButton.Enable(False)
		self.comm = machineCom.MachineCom(callbackObject=self)
		self.infoBox.SetBusy('Connecting to machine.')
		self._wizardState = 0

	def AllowNext(self):
		return False

	def OnResume(self, e):
		feedZ = profile.getProfileSettingFloat('max_z_speed') * 60
		feedTravel = profile.getProfileSettingFloat('travel_speed') * 60
		if self._wizardState == 2:
			wx.CallAfter(self.infoBox.SetBusy, 'Moving head to back left corner...')
			self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
			self.comm.sendCommand('G1 X%d Y%d F%d' % (0, profile.getPreferenceFloat('machine_depth'), feedTravel))
			self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
			self.comm.sendCommand('M400')
			self._wizardState = 3
		elif self._wizardState == 4:
			wx.CallAfter(self.infoBox.SetBusy, 'Moving head to back right corner...')
			self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
			self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getPreferenceFloat('machine_width'), profile.getPreferenceFloat('machine_depth') - 20, feedTravel))
			self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
			self.comm.sendCommand('M400')
			self._wizardState = 5
		elif self._wizardState == 6:
			wx.CallAfter(self.infoBox.SetBusy, 'Moving head to front right corner...')
			self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
			self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getPreferenceFloat('machine_width'), 20, feedTravel))
			self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
			self.comm.sendCommand('M400')
			self._wizardState = 7
		elif self._wizardState == 8:
			wx.CallAfter(self.infoBox.SetBusy, 'Heating up printer...')
			self.comm.sendCommand('G1 Z15 F%d' % (feedZ))
			self.comm.sendCommand('M104 S%d' % (profile.getProfileSettingFloat('print_temperature')))
			self.comm.sendCommand('G1 X%d Y%d F%d' % (0, 0, feedTravel))
			self._wizardState = 9
		self.resumeButton.Enable(False)

	def mcLog(self, message):
		print 'Log:', message

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		if self._wizardState == 1:
			self._wizardState = 2
			wx.CallAfter(self.infoBox.SetAttention, 'Adjust the front left screw of your printer bed\nSo the nozzle just hits the bed.')
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 3:
			self._wizardState = 4
			wx.CallAfter(self.infoBox.SetAttention, 'Adjust the back left screw of your printer bed\nSo the nozzle just hits the bed.')
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 5:
			self._wizardState = 6
			wx.CallAfter(self.infoBox.SetAttention, 'Adjust the back right screw of your printer bed\nSo the nozzle just hits the bed.')
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 7:
			self._wizardState = 8
			wx.CallAfter(self.infoBox.SetAttention, 'Adjust the front right screw of your printer bed\nSo the nozzle just hits the bed.')
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 9:
			if temp < profile.getProfileSettingFloat('print_temperature') - 5:
				wx.CallAfter(self.infoBox.SetInfo, 'Heating up printer: %d/%d' % (temp, profile.getProfileSettingFloat('print_temperature')))
			else:
				self._wizardState = 10
				wx.CallAfter(self.infoBox.SetInfo, 'Printing a square on the printer bed at 0.3mm height.')
				feedZ = profile.getProfileSettingFloat('max_z_speed') * 60
				feedPrint = profile.getProfileSettingFloat('print_speed') * 60
				feedTravel = profile.getProfileSettingFloat('travel_speed') * 60
				w = profile.getPreferenceFloat('machine_width')
				d = profile.getPreferenceFloat('machine_depth')
				filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
				filamentArea = math.pi * filamentRadius * filamentRadius
				ePerMM = (profile.calculateEdgeWidth() * 0.3) / filamentArea
				eValue = 0.0

				gcodeList = [
					'G1 Z2 F%d' % (feedZ),
					'G92 E0',
					'G1 X%d Y%d F%d' % (5, 5, feedTravel),
					'G1 Z0.3 F%d' % (feedZ)]
				eValue += 5;
				gcodeList.append('G1 E%f F%d' % (eValue, profile.getProfileSettingFloat('retraction_speed') * 60))

				for i in xrange(0, 3):
					dist = 5.0 + 0.4 * i
					eValue += (d - 2*dist) * ePerMM
					gcodeList.append('G1 X%d Y%d E%f F%d' % (dist, d - dist, eValue, feedPrint))
					eValue += (w - 2*dist) * ePerMM
					gcodeList.append('G1 X%d Y%d E%f F%d' % (w - dist, d - dist, eValue, feedPrint))
					eValue += (d - 2*dist) * ePerMM
					gcodeList.append('G1 X%d Y%d E%f F%d' % (w - dist, dist, eValue, feedPrint))
					eValue += (w - 2*dist) * ePerMM
					gcodeList.append('G1 X%d Y%d E%f F%d' % (dist, dist, eValue, feedPrint))

				gcodeList.append('M400')
				self.comm.printGCode(gcodeList)

	def mcStateChange(self, state):
		if self.comm is None:
			return
		if self.comm.isOperational():
			if self._wizardState == 0:
				wx.CallAfter(self.infoBox.SetInfo, 'Homing printer...')
				self.comm.sendCommand('G28')
				self._wizardState = 1
			elif self._wizardState == 10 and not self.comm.isPrinting():
				self.comm.sendCommand('G1 Z15 F%d' % (profile.getProfileSettingFloat('max_z_speed') * 60))
				self.comm.sendCommand('G92 E0')
				self.comm.sendCommand('G1 E-10 F%d' % (profile.getProfileSettingFloat('retraction_speed') * 60))
				self.comm.sendCommand('M104 S0')
				wx.CallAfter(self.infoBox.SetInfo, 'Calibration finished.\nThe squares on the bed should slightly touch each other.')
				wx.CallAfter(self.infoBox.SetReadyIndicator)
				wx.CallAfter(self.GetParent().FindWindowById(wx.ID_FORWARD).Enable)
				wx.CallAfter(self.connectButton.Enable, True)
				self._wizardState = 11
		elif self.comm.isError():
			wx.CallAfter(self.infoBox.SetError, 'Failed to establish connection with the printer.', 'http://wiki.ultimaker.com/Cura:_Connection_problems')

	def mcMessage(self, message):
		pass

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass

class bedLevelWizard(wx.wizard.Wizard):
	def __init__(self):
		super(bedLevelWizard, self).__init__(None, -1, "Bed leveling wizard")

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

		self.mainPage = bedLevelWizardMain(self)

		self.FitToPage(self.mainPage)
		self.GetPageAreaSizer().Add(self.mainPage)

		self.RunWizard(self.mainPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		self.FindWindowById(wx.ID_BACKWARD).Disable()
