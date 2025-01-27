from __future__ import absolute_import

import wx
import os
import webbrowser

from Cura.gui import configBase
from Cura.gui import expertConfig
from Cura.gui import preview3d
from Cura.gui import sliceProgessPanel
from Cura.gui import alterationPanel
from Cura.gui import pluginPanel
from Cura.gui import preferencesDialog
from Cura.gui import configWizard
from Cura.gui import firmwareInstall
from Cura.gui import printWindow
from Cura.gui import simpleMode
from Cura.gui import projectPlanner
from Cura.gui.tools import batchRun
from Cura.gui import flatSlicerWindow
from Cura.gui.util import dropTarget
from Cura.gui.tools import minecraftImport
from Cura.util import validators
from Cura.util import profile
from Cura.util import version
from Cura.util import sliceRun
from Cura.util import meshLoader

class mainWindow(wx.Frame):
	def __init__(self):
		super(mainWindow, self).__init__(None, title='Cura - ' + version.getVersion())

		self.extruderCount = int(profile.getPreference('extruder_amount'))

		wx.EVT_CLOSE(self, self.OnClose)

		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles, meshLoader.supportedExtensions()))

		self.normalModeOnlyItems = []

		self.menubar = wx.MenuBar()
		self.fileMenu = wx.Menu()
		i = self.fileMenu.Append(-1, 'Load model file...\tCTRL+L')
		self.Bind(wx.EVT_MENU, lambda e: self._showModelLoadDialog(1), i)
		i = self.fileMenu.Append(-1, 'Prepare print...\tCTRL+R')
		self.Bind(wx.EVT_MENU, self.OnSlice, i)
		i = self.fileMenu.Append(-1, 'Print...\tCTRL+P')
		self.Bind(wx.EVT_MENU, self.OnPrint, i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Open Profile...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfile, i)
		i = self.fileMenu.Append(-1, 'Save Profile...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnSaveProfile, i)
		i = self.fileMenu.Append(-1, 'Load Profile from GCode...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfileFromGcode, i)
		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Reset Profile to default')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnResetProfile, i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, 'Preferences...\tCTRL+,')
		self.Bind(wx.EVT_MENU, self.OnPreferences, i)
		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(wx.ID_EXIT, 'Quit')
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		self.menubar.Append(self.fileMenu, '&File')

		toolsMenu = wx.Menu()
		i = toolsMenu.Append(-1, 'Switch to quickprint...')
		self.switchToQuickprintMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnSimpleSwitch, i)
		i = toolsMenu.Append(-1, 'Switch to full settings...')
		self.switchToNormalMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnNormalSwitch, i)
		toolsMenu.AppendSeparator()
		i = toolsMenu.Append(-1, 'Batch run...')
		self.Bind(wx.EVT_MENU, self.OnBatchRun, i)
		i = toolsMenu.Append(-1, 'Project planner...')
		self.Bind(wx.EVT_MENU, self.OnProjectPlanner, i)
		#		i = toolsMenu.Append(-1, 'Open SVG (2D) slicer...')
		#		self.Bind(wx.EVT_MENU, self.OnSVGSlicerOpen, i)
		if minecraftImport.hasMinecraft():
			i = toolsMenu.Append(-1, 'Minecraft import...')
			self.Bind(wx.EVT_MENU, self.OnMinecraftImport, i)
		self.menubar.Append(toolsMenu, 'Tools')

		expertMenu = wx.Menu()
		i = expertMenu.Append(-1, 'Open expert settings...')
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnExpertOpen, i)
		expertMenu.AppendSeparator()
		if firmwareInstall.getDefaultFirmware() is not None:
			i = expertMenu.Append(-1, 'Install default Marlin firmware')
			self.Bind(wx.EVT_MENU, self.OnDefaultMarlinFirmware, i)
		i = expertMenu.Append(-1, 'Install custom firmware')
		self.Bind(wx.EVT_MENU, self.OnCustomFirmware, i)
		expertMenu.AppendSeparator()
		i = expertMenu.Append(-1, 'Run first run wizard...')
		self.Bind(wx.EVT_MENU, self.OnFirstRunWizard, i)
		i = expertMenu.Append(-1, 'Run bed leveling wizard...')
		self.Bind(wx.EVT_MENU, self.OnBedLevelWizard, i)
		self.menubar.Append(expertMenu, 'Expert')

		helpMenu = wx.Menu()
		i = helpMenu.Append(-1, 'Online documentation...')
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('http://daid.github.com/Cura'), i)
		i = helpMenu.Append(-1, 'Report a problem...')
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('https://github.com/daid/Cura/issues'), i)
		self.menubar.Append(helpMenu, 'Help')
		self.SetMenuBar(self.menubar)

		if profile.getPreference('lastFile') != '':
			self.filelist = profile.getPreference('lastFile').split(';')
			self.SetTitle('Cura - %s - %s' % (version.getVersion(), self.filelist[-1]))
		else:
			self.filelist = []
		self.progressPanelList = []

		##Gui components##
		self.simpleSettingsPanel = simpleMode.simpleModePanel(self)
		self.normalSettingsPanel = normalSettingsPanel(self)

		#Preview window
		self.preview3d = preview3d.previewPanel(self)

		# load and slice buttons.
		loadButton = wx.Button(self, -1, '&Load model')
		sliceButton = wx.Button(self, -1, 'P&repare print')
		printButton = wx.Button(self, -1, '&Print')
		self.Bind(wx.EVT_BUTTON, lambda e: self._showModelLoadDialog(1), loadButton)
		self.Bind(wx.EVT_BUTTON, self.OnSlice, sliceButton)
		self.Bind(wx.EVT_BUTTON, self.OnPrint, printButton)

		if self.extruderCount > 1:
			loadButton2 = wx.Button(self, -1, 'Load Dual')
			self.Bind(wx.EVT_BUTTON, lambda e: self._showModelLoadDialog(2), loadButton2)
		if self.extruderCount > 2:
			loadButton3 = wx.Button(self, -1, 'Load Triple')
			self.Bind(wx.EVT_BUTTON, lambda e: self._showModelLoadDialog(3), loadButton3)
		if self.extruderCount > 3:
			loadButton4 = wx.Button(self, -1, 'Load Quad')
			self.Bind(wx.EVT_BUTTON, lambda e: self._showModelLoadDialog(4), loadButton4)

		#Also bind double clicking the 3D preview to load an STL file.
		self.preview3d.glCanvas.Bind(wx.EVT_LEFT_DCLICK, lambda e: self._showModelLoadDialog(1), self.preview3d.glCanvas)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.GridBagSizer()
		self.SetSizer(sizer)
		sizer.Add(self.preview3d, (0,1), span=(1,2+self.extruderCount), flag=wx.EXPAND)
		sizer.AddGrowableCol(2 + self.extruderCount)
		sizer.AddGrowableRow(0)
		sizer.Add(loadButton, (1,1), flag=wx.RIGHT|wx.BOTTOM|wx.TOP, border=5)
		if self.extruderCount > 1:
			sizer.Add(loadButton2, (1,2), flag=wx.RIGHT|wx.BOTTOM|wx.TOP, border=5)
		if self.extruderCount > 2:
			sizer.Add(loadButton3, (1,3), flag=wx.RIGHT|wx.BOTTOM|wx.TOP, border=5)
		if self.extruderCount > 3:
			sizer.Add(loadButton4, (1,4), flag=wx.RIGHT|wx.BOTTOM|wx.TOP, border=5)
		sizer.Add(sliceButton, (1,1+self.extruderCount), flag=wx.RIGHT|wx.BOTTOM|wx.TOP, border=5)
		sizer.Add(printButton, (1,2+self.extruderCount), flag=wx.RIGHT|wx.BOTTOM|wx.TOP, border=5)
		self.sizer = sizer

		if len(self.filelist) > 0:
			self.preview3d.loadModelFiles(self.filelist)

		self.updateProfileToControls()

		self.SetBackgroundColour(self.normalSettingsPanel.GetBackgroundColour())

		self.simpleSettingsPanel.Show(False)
		self.normalSettingsPanel.Show(False)
		self.updateSliceMode()

		if wx.Display().GetClientArea().GetWidth() < self.GetSize().GetWidth():
			f = self.GetSize().GetWidth() - wx.Display().GetClientArea().GetWidth()
			self.preview3d.SetMinSize(self.preview3d.GetMinSize().DecBy(f, 0))
			self.Fit()
		self.preview3d.Fit()
		#self.SetMinSize(self.GetSize())

		self.Centre()
		self.Show(True)

		self.Centre()

	def updateSliceMode(self):
		isSimple = profile.getPreference('startMode') == 'Simple'

		self.normalSettingsPanel.Show(not isSimple)
		self.simpleSettingsPanel.Show(isSimple)

		self.GetSizer().Detach(self.simpleSettingsPanel)
		self.GetSizer().Detach(self.normalSettingsPanel)
		if isSimple:
			self.GetSizer().Add(self.simpleSettingsPanel, (0,0), span=(1,1), flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=6)
		else:
			self.GetSizer().Add(self.normalSettingsPanel, (0,0), span=(1,1), flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=6)

		for i in self.normalModeOnlyItems:
			i.Enable(not isSimple)
		self.switchToQuickprintMenuItem.Enable(not isSimple)
		self.switchToNormalMenuItem.Enable(isSimple)

		self.normalSettingsPanel.Layout()
		self.simpleSettingsPanel.Layout()
		self.GetSizer().Layout()
		self.Fit()
		self.Refresh()

	def OnPreferences(self, e):
		prefDialog = preferencesDialog.preferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show(True)

	def _showOpenDialog(self, title, wildcard = meshLoader.wildcardFilter()):
		dlg=wx.FileDialog(self, title, os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard(wildcard)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			dlg.Destroy()
			if not(os.path.exists(filename)):
				return False
			profile.putPreference('lastFile', filename)
			return filename
		dlg.Destroy()
		return False

	def _showModelLoadDialog(self, amount):
		filelist = []
		for i in xrange(0, amount):
			filelist.append(self._showOpenDialog("Open file to print"))
			if filelist[-1] == False:
				return
		self._loadModels(filelist)

	def _loadModels(self, filelist):
		self.filelist = filelist
		self.SetTitle(filelist[-1] + ' - Cura - ' + version.getVersion())
		profile.putPreference('lastFile', ';'.join(self.filelist))
		self.preview3d.loadModelFiles(self.filelist, True)
		self.preview3d.setViewMode("Normal")

	def OnDropFiles(self, files):
		self._loadModels(files)

	def OnLoadModel(self, e):
		self._showModelLoadDialog(1)

	def OnLoadModel2(self, e):
		self._showModelLoadDialog(2)

	def OnLoadModel3(self, e):
		self._showModelLoadDialog(3)

	def OnLoadModel4(self, e):
		self._showModelLoadDialog(4)

	def OnSlice(self, e):
		if len(self.filelist) < 1:
			wx.MessageBox('You need to load a file before you can prepare it.', 'Print error', wx.OK | wx.ICON_INFORMATION)
			return
		isSimple = profile.getPreference('startMode') == 'Simple'
		if isSimple:
			#save the current profile so we can put it back latter
			oldProfile = profile.getGlobalProfileString()
			self.simpleSettingsPanel.setupSlice()
		#Create a progress panel and add it to the window. The progress panel will start the Skein operation.
		spp = sliceProgessPanel.sliceProgessPanel(self, self, self.filelist)
		self.sizer.Add(spp, (len(self.progressPanelList)+2,0), span=(1, 3 + self.extruderCount), flag=wx.EXPAND)
		self.sizer.Layout()
		newSize = self.GetSize()
		newSize.IncBy(0, spp.GetSize().GetHeight())
		if newSize.GetWidth() < wx.GetDisplaySize()[0]:
			self.SetSize(newSize)
		self.progressPanelList.append(spp)
		if isSimple:
			profile.loadGlobalProfileFromString(oldProfile)

	def OnPrint(self, e):
		if len(self.filelist) < 1:
			wx.MessageBox('You need to load a file and prepare it before you can print.', 'Print error', wx.OK | wx.ICON_INFORMATION)
			return
		if not os.path.exists(sliceRun.getExportFilename(self.filelist[0])):
			wx.MessageBox('You need to prepare a print before you can run the actual print.', 'Print error', wx.OK | wx.ICON_INFORMATION)
			return
		printWindow.printFile(sliceRun.getExportFilename(self.filelist[0]))

	def removeSliceProgress(self, spp):
		self.progressPanelList.remove(spp)
		newSize = self.GetSize()
		newSize.IncBy(0, -spp.GetSize().GetHeight())
		if newSize.GetWidth() < wx.GetDisplaySize()[0]:
			self.SetSize(newSize)
		spp.Show(False)
		self.sizer.Detach(spp)
		for spp in self.progressPanelList:
			self.sizer.Detach(spp)
		i = 2
		for spp in self.progressPanelList:
			self.sizer.Add(spp, (i,0), span=(1,3 + self.extruderCount), flag=wx.EXPAND)
			i += 1
		self.sizer.Layout()

	def updateProfileToControls(self):
		self.preview3d.updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()
		self.simpleSettingsPanel.updateProfileToControls()

	def OnLoadProfile(self, e):
		dlg=wx.FileDialog(self, "Select profile file to load", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.loadGlobalProfile(profileFile)
			self.updateProfileToControls()
		dlg.Destroy()

	def OnLoadProfileFromGcode(self, e):
		dlg=wx.FileDialog(self, "Select gcode file to load profile from", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("gcode files (*.gcode)|*.gcode;*.g")
		if dlg.ShowModal() == wx.ID_OK:
			gcodeFile = dlg.GetPath()
			f = open(gcodeFile, 'r')
			hasProfile = False
			for line in f:
				if line.startswith(';CURA_PROFILE_STRING:'):
					profile.loadGlobalProfileFromString(line[line.find(':')+1:].strip())
					hasProfile = True
			if hasProfile:
				self.updateProfileToControls()
			else:
				wx.MessageBox('No profile found in GCode file.\nThis feature only works with GCode files made by Cura 12.07 or newer.', 'Profile load error', wx.OK | wx.ICON_INFORMATION)
		dlg.Destroy()

	def OnSaveProfile(self, e):
		dlg=wx.FileDialog(self, "Select profile file to save", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.saveGlobalProfile(profileFile)
		dlg.Destroy()

	def OnResetProfile(self, e):
		dlg = wx.MessageDialog(self, 'This will reset all profile settings to defaults.\nUnless you have saved your current profile, all settings will be lost!\nDo you really want to reset?', 'Profile reset', wx.YES_NO | wx.ICON_QUESTION)
		result = dlg.ShowModal() == wx.ID_YES
		dlg.Destroy()
		if result:
			profile.resetGlobalProfile()
			self.updateProfileToControls()

	def OnBatchRun(self, e):
		br = batchRun.batchRunWindow(self)
		br.Centre()
		br.Show(True)

	def OnSimpleSwitch(self, e):
		profile.putPreference('startMode', 'Simple')
		self.updateSliceMode()

	def OnNormalSwitch(self, e):
		profile.putPreference('startMode', 'Normal')
		self.updateSliceMode()

	def OnDefaultMarlinFirmware(self, e):
		firmwareInstall.InstallFirmware()

	def OnCustomFirmware(self, e):
		if profile.getPreference('machine_type') == 'ultimaker':
			wx.MessageBox('Warning: Installing a custom firmware does not garantee that you machine will function correctly, and could damage your machine.', 'Firmware update', wx.OK | wx.ICON_EXCLAMATION)
		dlg=wx.FileDialog(self, "Open firmware to upload", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("HEX file (*.hex)|*.hex;*.HEX")
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			if not(os.path.exists(filename)):
				return
			#For some reason my Ubuntu 10.10 crashes here.
			firmwareInstall.InstallFirmware(filename)

	def OnFirstRunWizard(self, e):
		configWizard.configWizard()
		self.updateProfileToControls()

	def OnBedLevelWizard(self, e):
		configWizard.bedLevelWizard()

	def OnExpertOpen(self, e):
		ecw = expertConfig.expertConfigWindow()
		ecw.Centre()
		ecw.Show(True)

	def OnProjectPlanner(self, e):
		pp = projectPlanner.projectPlanner()
		pp.Centre()
		pp.Show(True)

	def OnMinecraftImport(self, e):
		mi = minecraftImport.minecraftImportWindow(self)
		mi.Centre()
		mi.Show(True)

	def OnSVGSlicerOpen(self, e):
		svgSlicer = flatSlicerWindow.flatSlicerWindow()
		svgSlicer.Centre()
		svgSlicer.Show(True)

	def OnClose(self, e):
		profile.saveGlobalProfile(profile.getDefaultProfilePath())
		self.Destroy()

	def OnQuit(self, e):
		self.Close()

class normalSettingsPanel(configBase.configPanelBase):
	"Main user interface window"
	def __init__(self, parent):
		super(normalSettingsPanel, self).__init__(parent)

		#Main tabs
		nb = wx.Notebook(self)
		self.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.GetSizer().Add(nb, 1)

		(left, right) = self.CreateConfigTab(nb, 'Print config')

		configBase.TitleRow(left, "Quality")
		c = configBase.SettingRow(left, "Layer height (mm)", 'layer_height', '0.2', 'Layer height in millimeters.\n0.2 is a good value for quick prints.\n0.1 gives high quality prints.')
		validators.validFloat(c, 0.0001)
		validators.warningAbove(c, lambda : (float(profile.getProfileSetting('nozzle_size')) * 80.0 / 100.0), "Thicker layers then %.2fmm (80%% nozzle size) usually give bad results and are not recommended.")
		c = configBase.SettingRow(left, "Wall thickness (mm)", 'wall_thickness', '0.8', 'Thickness of the walls.\nThis is used in combination with the nozzle size to define the number\nof perimeter lines and the thickness of those perimeter lines.')
		validators.validFloat(c, 0.0001)
		validators.wallThicknessValidator(c)
		c = configBase.SettingRow(left, "Enable retraction", 'retraction_enable', False, 'Retract the filament when the nozzle is moving over a none-printed area. Details about the retraction can be configured in the advanced tab.')

		configBase.TitleRow(left, "Fill")
		c = configBase.SettingRow(left, "Bottom/Top thickness (mm)", 'solid_layer_thickness', '0.6', 'This controls the thickness of the bottom and top layers, the amount of solid layers put down is calculated by the layer thickness and this value.\nHaving this value a multiply of the layer thickness makes sense. And keep it near your wall thickness to make an evenly strong part.')
		validators.validFloat(c, 0.0)
		c = configBase.SettingRow(left, "Fill Density (%)", 'fill_density', '20', 'This controls how densily filled the insides of your print will be. For a solid part use 100%, for an empty part use 0%. A value around 20% is usually enough')
		validators.validFloat(c, 0.0, 100.0)

		configBase.TitleRow(right, "Speed && Temperature")
		c = configBase.SettingRow(right, "Print speed (mm/s)", 'print_speed', '50', 'Speed at which printing happens. A well adjusted Ultimaker can reach 150mm/s, but for good quality prints you want to print slower. Printing speed depends on a lot of factors. So you will be experimenting with optimal settings for this.')
		validators.validFloat(c, 1.0)
		validators.warningAbove(c, 150.0, "It is highly unlikely that your machine can achieve a printing speed above 150mm/s")
		validators.printSpeedValidator(c)

		#configBase.TitleRow(right, "Temperature")
		c = configBase.SettingRow(right, "Printing temperature", 'print_temperature', '0', 'Temperature used for printing. Set at 0 to pre-heat yourself')
		validators.validFloat(c, 0.0, 340.0)
		validators.warningAbove(c, 260.0, "Temperatures above 260C could damage your machine, be careful!")
		if profile.getPreference('has_heated_bed') == 'True':
			c = configBase.SettingRow(right, "Bed temperature", 'print_bed_temperature', '0', 'Temperature used for the heated printer bed. Set at 0 to pre-heat yourself')
			validators.validFloat(c, 0.0, 340.0)

		configBase.TitleRow(right, "Support structure")
		c = configBase.SettingRow(right, "Support type", 'support', ['None', 'Exterior Only', 'Everywhere'], 'Type of support structure build.\n"Exterior only" is the most commonly used support setting.\n\nNone does not do any support.\nExterior only only creates support where the support structure will touch the build platform.\nEverywhere creates support even on the insides of the model.')
		c = configBase.SettingRow(right, "Add raft", 'enable_raft', False, 'A raft is a few layers of lines below the bottom of the object. It prevents warping. Full raft settings can be found in the expert settings.\nFor PLA this is usually not required. But if you print with ABS it is almost required.')
		if int(profile.getPreference('extruder_amount')) > 1:
			c = configBase.SettingRow(right, "Support dual extrusion", 'support_dual_extrusion', False, 'Print the support material with the 2nd extruder in a dual extrusion setup. The primary extruder will be used for normal material, while the second extruder is used to print support material.')

		configBase.TitleRow(right, "Filament")
		c = configBase.SettingRow(right, "Diameter (mm)", 'filament_diameter', '2.89', 'Diameter of your filament, as accurately as possible.\nIf you cannot measure this value you will have to callibrate it, a higher number means less extrusion, a smaller number generates more extrusion.')
		validators.validFloat(c, 1.0)
		validators.warningAbove(c, 3.5, "Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm.")
		c = configBase.SettingRow(right, "Packing Density", 'filament_density', '1.00', 'Packing density of your filament. This should be 1.00 for PLA and 0.85 for ABS')
		validators.validFloat(c, 0.5, 1.5)

		(left, right) = self.CreateConfigTab(nb, 'Advanced config')

		configBase.TitleRow(left, "Machine size")
		c = configBase.SettingRow(left, "Nozzle size (mm)", 'nozzle_size', '0.4', 'The nozzle size is very important, this is used to calculate the line width of the infill, and used to calculate the amount of outside wall lines and thickness for the wall thickness you entered in the print settings.')
		validators.validFloat(c, 0.1, 10.0)

		configBase.TitleRow(left, "Skirt")
		c = configBase.SettingRow(left, "Line count", 'skirt_line_count', '1', 'The skirt is a line drawn around the object at the first layer. This helps to prime your extruder, and to see if the object fits on your platform.\nSetting this to 0 will disable the skirt. Multiple skirt lines can help priming your extruder better for small objects.')
		validators.validInt(c, 0, 10)
		c = configBase.SettingRow(left, "Start distance (mm)", 'skirt_gap', '6.0', 'The distance between the skirt and the first layer.\nThis is the minimal distance, multiple skirt lines will be put outwards from this distance.')
		validators.validFloat(c, 0.0)

		configBase.TitleRow(left, "Retraction")
		c = configBase.SettingRow(left, "Minimum travel (mm)", 'retraction_min_travel', '5.0', 'Minimum amount of travel needed for a retraction to happen at all. To make sure you do not get a lot of retractions in a small area')
		validators.validFloat(c, 0.0)
		c = configBase.SettingRow(left, "Speed (mm/s)", 'retraction_speed', '40.0', 'Speed at which the filament is retracted, a higher retraction speed works better. But a very high retraction speed can lead to filament grinding.')
		validators.validFloat(c, 0.1)
		c = configBase.SettingRow(left, "Distance (mm)", 'retraction_amount', '0.0', 'Amount of retraction, set at 0 for no retraction at all. A value of 2.0mm seems to generate good results.')
		validators.validFloat(c, 0.0)
		c = configBase.SettingRow(left, "Extra length on start (mm)", 'retraction_extra', '0.0', 'Extra extrusion amount when restarting after a retraction, to better "Prime" your extruder after retraction.')
		validators.validFloat(c, 0.0)

		configBase.TitleRow(right, "Speed")
		c = configBase.SettingRow(right, "Travel speed (mm/s)", 'travel_speed', '150', 'Speed at which travel moves are done, a high quality build Ultimaker can reach speeds of 250mm/s. But some machines might miss steps then.')
		validators.validFloat(c, 1.0)
		validators.warningAbove(c, 300.0, "It is highly unlikely that your machine can achieve a travel speed above 300mm/s")
		c = configBase.SettingRow(right, "Max Z speed (mm/s)", 'max_z_speed', '1.0', 'Speed at which Z moves are done. When you Z axis is properly lubercated you can increase this for less Z blob.')
		validators.validFloat(c, 0.5)
		c = configBase.SettingRow(right, "Bottom layer speed (mm/s)", 'bottom_layer_speed', '25', 'Print speed for the bottom layer, you want to print the first layer slower so it sticks better to the printer bed.')
		validators.validFloat(c, 0.0)

		configBase.TitleRow(right, "Cool")
		c = configBase.SettingRow(right, "Minimal layer time (sec)", 'cool_min_layer_time', '10', 'Minimum time spend in a layer, gives the layer time to cool down before the next layer is put on top. If the layer will be placed down too fast the printer will slow down to make sure it has spend atleast this amount of seconds printing this layer.')
		validators.validFloat(c, 0.0)
		c = configBase.SettingRow(right, "Enable cooling fan", 'fan_enabled', True, 'Enable the cooling fan during the print. The extra cooling from the cooling fan is essensial during faster prints.')

		configBase.TitleRow(right, "Quality")
		c = configBase.SettingRow(right, "Initial layer thickness (mm)", 'bottom_thickness', '0.0', 'Layer thickness of the bottom layer. A thicker bottom layer makes sticking to the bed easier. Set to 0.0 to have the bottom layer thickness the same as the other layers.')
		validators.validFloat(c, 0.0)
		validators.warningAbove(c, lambda : (float(profile.getProfileSetting('nozzle_size')) * 3.0 / 4.0), "A bottom layer of more then %.2fmm (3/4 nozzle size) usually give bad results and is not recommended.")
		c = configBase.SettingRow(right, "Duplicate outlines", 'enable_skin', False, 'Skin prints the outer lines of the prints twice, each time with half the thickness. This gives the illusion of a higher print quality.')

		#Plugin page
		self.pluginPanel = pluginPanel.pluginPanel(nb)
		if len(self.pluginPanel.pluginList) > 0:
			nb.AddPage(self.pluginPanel, "Plugins")
		else:
			self.pluginPanel.Show(False)

		#Alteration page
		self.alterationPanel = alterationPanel.alterationPanel(nb)
		nb.AddPage(self.alterationPanel, "Start/End-GCode")

	def updateProfileToControls(self):
		super(normalSettingsPanel, self).updateProfileToControls()
		self.alterationPanel.updateProfileToControls()
		self.pluginPanel.updateProfileToControls()
