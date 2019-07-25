#!/usr/bin/env python3

import wx
import JSONManager
import wx.gizmos as gizmos
import wx.lib.agw.aui as aui
import wx.dataview as dv
import json
from qTreeManager import *
from TreeStuff import *
import wx.lib.agw.customtreectrl as ct
import wx.lib.agw.flatnotebook as fnb
import wx.grid as grid
import wx.lib.buttons as buttons
import copy

import wx.lib.agw.aui as aui
## Create by Jonathan Naylor - June 2019 - For the NUFEB project (Newcastle University) ##



import cPickle
class VarNodeDropData(wx.CustomDataObject):
	NAME = "VarNode"
	PICKLE_PROTOCOL = 2
   
	def __init__(self):
		wx.CustomDataObject.__init__(self, VarNodeDropData.NAME)
           
	def setNode(self, node):
		data = cPickle.dumps(node, VarNodeDropData.PICKLE_PROTOCOL)       
		self.SetData(data)
       
	def getNode(self):
		return cPickle.loads(self.GetData())
		
class VarNodeDropTarget(wx.PyDropTarget):
	def __init__(self, parent):
		wx.PyDropTarget.__init__(self)
		self.parent = parent
       
        # specify the type of data we will accept
		self.data = VarNodeDropData()
		self.SetDataObject(self.data)
                       
	def OnData(self, x, y, defaultResult):
		print "---OnData", self.GetData()
       
		if not self.GetData():
			return wx.DragNone
       
		jsondata = self.data.getNode()
		item = self.parent.HitTest(wx.Point(x, y))[0]
		self.parent.GetParent().GetParent().UnpackJSONModelIntoTree(jsondata, item, self.parent)
		#self.parent.AppendItem(item, "lol")
		return defaultResult
		
    
class MyComboBox(wx.ComboBox):
	def __init__(self, tree, path, choices=[]):
		wx.ComboBox.__init__(self, tree, choices=choices)
		self.path = path
    
	def SetChild(self, child):
		self.child = child

	def GetChild(self):
		return self.child
		
		
class TabPanel(wx.Panel):
	
	def __init__(self, parent, filename):
		wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
		self.filename = filename
		
	def SetTree(self, tree):
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(tree, 1, wx.EXPAND)
		self.SetSizer(sizer) 
		self.tree = tree
	
class OtherFrame(wx.Frame):
 
	def __init__(self, title, parent=None):
		wx.Frame.__init__(self, parent=parent, title=title)
		
		width, height = wx.GetDisplaySize()
			
		self.SetDimensions(0, 0, width/3, height/3)
		self.Show()
        

########################################################################
class TestPopup(wx.PopupWindow):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, parent, style):
        """Constructor"""
        wx.PopupWindow.__init__(self, parent, style)

        panel = wx.Panel(self)
        self.panel = panel
       # panel.SetBackgroundColour("CADET BLUE")

        st = wx.StaticText(panel, -1,
                           "This is a special kind of top level\n"
                           "window that can be used for\n"
                           "popup menus, combobox popups\n"
                           "and such.\n\n"
                           "Try positioning the demo near\n"
                           "the bottom of the screen and \n"
                           "hit the button again.\n\n"
                           "In this demo this window can\n"
                           "be dragged with the left button\n"
                           "and closed with the right."
                           ,
                           pos=(10,10))
        sz = st.GetBestSize()
        self.SetSize( (sz.width+20, sz.height+20) )
        panel.SetSize( (sz.width+20, sz.height+20) )

        panel.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        panel.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        panel.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        panel.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        st.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        st.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        st.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        st.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        wx.CallAfter(self.Refresh)    

    def OnMouseLeftDown(self, evt):
        self.Refresh()
        self.ldPos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
        self.wPos = self.ClientToScreen((0,0))
        self.panel.CaptureMouse()

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            dPos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
            nPos = (self.wPos.x + (dPos.x - self.ldPos.x),
                    self.wPos.y + (dPos.y - self.ldPos.y))
            self.Move(nPos)

    def OnMouseLeftUp(self, evt):
        if self.panel.HasCapture():
            self.panel.ReleaseMouse()

    def OnRightUp(self, evt):
        self.Show(False)
        self.Destroy()
        
		   
## GUI object inherits wxFrame
class GUI(wx.Frame):


	# Construct the GUI object
	def __init__(self, *args, **kw):
		super(GUI, self).__init__(*args, **kw)
		width, height = wx.GetDisplaySize()
		
		# create a panel manager with a new panel
		self.mainPanel = wx.Panel(self)
		self.pManager = aui.AuiManager()
		self.pManager.SetManagedWindow(self.mainPanel)
		
		self.notebook = fnb.FlatNotebook(self.mainPanel, style=fnb.FNB_X_ON_TAB)
		self.notebook.Layout()
		
		self.updateFlag = False
		
		self.tabs = {}		
		self.models = {}		
		self.trees = {}		
		self.roots = {}		
		self.errors = {}
		self.substrateLists = {}
		
		self.DefineConstants()
		self.LoadLibrary("library.json")
		
		# create the widgets
		self.CreateMenuBar()
		#self.CreateLibraryTree(self.mainPanel)
		
		self.CreateStatusBar()
		
		
		# create the timer
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.Update, self.timer)
		#self.Bind(wx.EVT_MOTION, self.OnMouseMotion )
		self.timer.Start(2000)
 
		# create the panes
		self.modulePanel = wx.Panel(self.mainPanel)
		
		bmp = wx.Bitmap("new_domain.png", wx.BITMAP_TYPE_ANY)
		newDomainButton = buttons.GenBitmapButton(self.modulePanel, bitmap=bmp)
		newDomainButton.Bind(wx.EVT_BUTTON, self.NewDomain)
		
		
		bmp = wx.Bitmap("new_bacteria.png", wx.BITMAP_TYPE_ANY)
		newBacteriaButton = buttons.GenBitmapButton(self.modulePanel, bitmap=bmp)
		newBacteriaButton.Bind(wx.EVT_BUTTON, self.NewBacteria)
		
		
		bmp = wx.Bitmap("new_growth.png", wx.BITMAP_TYPE_ANY)
		newGrowthButton = buttons.GenBitmapButton(self.modulePanel, bitmap=bmp)
		newGrowthButton.Bind(wx.EVT_BUTTON, self.NewGrowth)
		
		
		bmp = wx.Bitmap("new_permeation.png", wx.BITMAP_TYPE_ANY)
		newPermeationButton = buttons.GenBitmapButton(self.modulePanel, bitmap=bmp)
		newPermeationButton.Bind(wx.EVT_BUTTON, self.NewPermeation)
 
		button = wx.ToggleButton(self.modulePanel, label="Press Me")
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(newDomainButton, 0, wx.ALL, 5)
		sizer.Add(newBacteriaButton, 0, wx.ALL, 5)
		sizer.Add(newGrowthButton, 0, wx.ALL, 5)
		sizer.Add(newPermeationButton, 0, wx.ALL, 5)
		#sizer.Add(button, 0, wx.ALL, 5)
		
		
		self.modulePanel.SetSizer(sizer)
        
		self.propertyPanel = wx.TextCtrl(self.mainPanel, style=wx.TE_MULTILINE)
		
		
        
        
		# add the widgets to the panel as individual panes
		self.pManager.AddPane(self.notebook, aui.AuiPaneInfo().CenterPane().CloseButton(False).MinimizeButton(False).MaximizeButton(False))   
		#self.pManager.AddPane(self.modulePanel, aui.AuiPaneInfo().Left().Name("Modelling features").MinimizeButton(True).MaximizeButton(True).CloseButton(True).BestSize((width/10, height)).Caption("Models"))
		self.pManager.AddPane(self.modulePanel, aui.AuiPaneInfo().Left().Name("Modelling features").CloseButton(False).BestSize((width/10, height)).Caption("Modelling features"))
		#self.pManager.AddPane(self.library_tree, aui.AuiPaneInfo().Left().Name("Library").MinimizeButton(True).MaximizeButton(True).CloseButton(True).BestSize((width/10, height/2)).Caption("Library"))
		self.pManager.AddPane(self.propertyPanel, aui.AuiPaneInfo().Right().Name("Property Viewer").MinimizeButton(True).MaximizeButton(True).CloseButton(True).BestSize((width/3, height)).Caption("Property Viewer"))
		self.pManager.Update()

	def DefineConstants(self):	
		self.T_ENERGY = ["not-hydrated", "fully-protonated", "1st-deprotonated", "2nd-deprotonated", "3rd-deprotonated"]
		self.T_STATUS = ["liquid", "gas"]
		self.T_BOUNDARY = ["periodic", "fixed"]
		self.T_DIF_BOUNDARY = ["periodic", "neumann", "dirithlet"]
		self.userDefinedKeys = ["T_SUBSTRATE", "T_SUBSTRATE_ID", "T_BACTERIA", "T_BACTERIA_ID", "T_ENERGY", "T_FORM"]
		
		self.colour_white = wx.Colour(255, 255, 255, 255)
		self.colour_red = wx.Colour(150, 0, 0, 200)

     
	#######################################################################################
	########					TABBED PANELS									  #########
	#######################################################################################   
		
	def OpenTab(self, filename):

		# if there already exists a tab for this file, just focus on that tab
		for i in range(self.notebook.GetPageCount()):

			if self.notebook.GetPageText(i) == filename:
				self.notebook.SetSelection(i)
				self.tree = self.notebook.GetCurrentPage().tree
				self.model = self.models[filename]
				return None
			
        # otherwise create, store and return the new tab 
		newTab = TabPanel(self.notebook, filename)
		self.tabs[filename] = newTab
		return newTab
		
	def LoadTab(self, filename, tab=None):
		if not tab:
			tab = self.tabs[filename]
			if not tab:
				return 
		
		self.notebook.AddPage(tab, filename)
		self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.ChangeTab)
		self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.CloseTab)
		self.notebook.SetSelection(self.notebook.GetPageCount()-1)

		
		
	def ChangeTab(self, event):
		page = self.notebook.GetCurrentPage()
		self.tree = page.tree
		self.filename = page.filename
		
	def CloseTab(self, event):
		key = self.filename
		self.models.pop(key, None)
		self.errors.pop(key, None)
		self.tabs.pop(key, None)
		
		     
	#######################################################################################
	########				GUI INITIALISATION									  #########
	#######################################################################################   
		
	# Create the menubar (file, edit, etc.)
	def CreateMenuBar(self):
		
		# create file menu
		mFile = wx.Menu()
		mFile.Append(1, "&New model", "Create a new model")
		mFile.Append(2, "&Open model", "Open an existing model")
		mFile.Append(3, "&Save", "Save the current model")
		mFile.Append(4, "&Save as", "Save the current model as a new file")
		mFile.AppendSeparator()
		mFile.Append(5, "&Close model", "Close the model")

		# create edit menu
		mEdit = wx.Menu()
		mEdit.Append(6, "&Fonts", "Set the font for the interface")
		
		# create edit menu
		mView = wx.Menu()
		mView.Append(9, "&Affinity constants", "Set the affinity constants for the model")
		mView.Append(10, "&Chemical species energy", "Set the chemical species energy coefficients for the model")
		
		
		# create run menu
		mRun = wx.Menu()
		mRun.Append(8, "&Run simulation", "Run a simulation of the model")
	

		# create menubar and attach the menus defined above, then set it to this frame
		menuBar = wx.MenuBar()
		menuBar.Append(mFile, "&File")
		menuBar.Append(mEdit, "&Edit")
		menuBar.Append(mView, "&View")
		menuBar.Append(mRun, "&Run")
		self.SetMenuBar(menuBar)

		# bind the events to their functions
		self.Bind(wx.EVT_MENU, self.NewModel, id=1)
		self.Bind(wx.EVT_MENU, self.OpenModel, id=2)
		self.Bind(wx.EVT_MENU, self.Save, id=3)
		self.Bind(wx.EVT_MENU, self.SaveAs, id=4)
		self.Bind(wx.EVT_MENU, self.CloseModel, id=5)
		self.Bind(wx.EVT_MENU, self.SetAffinityConstants, id=9)
		self.Bind(wx.EVT_MENU, self.SetChemicalSpeciesEnergy, id=10)
		self.Bind(wx.EVT_MENU, self.RunModel, id=8)
		self.Bind(wx.EVT_MENU, self.SetInterfaceFont, id=6)
		self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.OnMenuHighlight)	

		
	## Create the tree viewer (where the model overview is visualised)
	def CreatePropertyView(self):
		panel = wx.Panel(self)
		
		width, height = wx.GetDisplaySize()
		self.property_view = wx.TextCtrl(panel, pos=(width/2, 10), size=(width/2, height))

     
     
	#######################################################################################
	########					MODEL TREE										  #########
	#######################################################################################   
		
	## Create the tree viewer (where the model overview is visualised)
	def CreateTreeView(self, filename, panel):
		width, height = wx.GetDisplaySize()
		
		self.tree = tree = ct.CustomTreeCtrl(panel, -1, style =
										wx.TR_HAS_BUTTONS 
										| wx.TR_HAS_VARIABLE_ROW_HEIGHT
										| wx.TR_HIDE_ROOT
										| wx.TR_SINGLE
										| ct.TR_AUTO_CHECK_CHILD 
										| ct.TR_AUTO_CHECK_PARENT
										#| wx.TR_EDIT_LABELS
										#| wx.TR_HAS_BUTTONS
                                        #| wx.TR_TWIST_BUTTONS
                                        #| wx.TR_ROW_LINES
                                        #| wx.TR_COLUMN_LINES
                                        #| wx.TR_NO_LINES 
										#| wx.TR_FULL_ROW_HIGHLIGHT
					
		)
		#root = custom_tree.AddRoot("The Root Item")
    
		self.tree.SetBackgroundColour(self.colour_white)

		# bind events to their functions (right-clicking or double-clicking on a tree item)
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivate)
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelection)
		self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
		self.tree.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnCollapse)
		#self.tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnDrag)
		self.tree.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEditCompletion)
		
		panel.SetTree(tree)
		self.trees[filename] = tree
		return tree
		

	## Open a model (trigger by 'File -> Open Model')
	def OpenModel(self, event):
		dlg = wx.FileDialog(self, message="Choose a file", defaultDir="/home/jonny",  defaultFile="", style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)
		
		if dlg.ShowModal() == wx.ID_OK:
			paths = dlg.GetPaths()
			print "You chose the following file(s):"
			for path in paths:
				self.OpenModelFile(path)
				
			filename = path
		
		dlg.Destroy()
			

	def OpenModelFile(self, filename):	
		self.filename = filename
		newTab = self.OpenTab(filename)
		if not newTab:
			return
			
		tree = self.CreateTreeView(filename, newTab)
		
		self.LoadTab(filename, newTab)
		
		dropTarget = VarNodeDropTarget(tree)
		tree.SetDropTarget(dropTarget)
		
		# open the file 
		with open(filename) as data_file:
			
			# set the root node of the tree to be the file name (with blank column values)
			self.roots[filename] = tree.AddRoot(filename)
			
			# recursively unpack the JSON data into the tree viewer
			self.models[filename] = json.load(data_file)
			self.errors[filename] = []
			self.substrateLists[filename] = []
			self.UnpackJSONModelIntoTree(self.models[filename], self.roots[filename], tree)
		
		# expand the root node of the tree so the main model features are visible
		tree.Expand(self.roots[filename])	



	#######################################################################################
	########				LIBRARY TREE										  #########
	#######################################################################################
   
	# Load the library
	def LoadLibrary(self, file):
		with open(file) as data_file:
			self.library = json.load(data_file)
			
	def CreateLibraryTree(self, panel):
		width, height = wx.GetDisplaySize()
		
		self.library_tree = gizmos.TreeListCtrl(panel, -1, style =
										wx.TR_DEFAULT_STYLE
										| wx.TR_HAS_VARIABLE_ROW_HEIGHT
										| wx.TR_EDIT_LABELS
										#| wx.TR_HAS_BUTTONS
                                        #| wx.TR_TWIST_BUTTONS
                                        #| wx.TR_ROW_LINES
                                        #| wx.TR_COLUMN_LINES
                                        #| wx.TR_NO_LINES 
										#| wx.TR_FULL_ROW_HIGHLIGHT
									)
   
        # create the columns and set their properties
		self.library_tree.AddColumn("Library")
		self.library_tree.SetMainColumn(0)
		self.library_tree.SetColumnWidth(0, width/2)

		self.library_root = self.library_tree.AddRoot("NUFEB")
		
		self.library_tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnDrag)
		
		self.UnpackJSONModelIntoLibraryTree(self.library, self.library_root, self.library_tree)
			
	def Update(self, event):
		if self.updateFlag:
			self.ValidateModel()
			self.updateFlag = False
		
	def CheckPropType(self, propertyType):
		cbox = False
		values = []
		isSubstrateList = False
		
		if propertyType == "T_ENERGY":
			values = self.T_ENERGY
			cbox = True
		if propertyType == "T_STATUS":
			values = self.T_STATUS
			cbox = True
		if propertyType == "T_BOUNDARY":
			values = self.T_BOUNDARY
			cbox = True
		if propertyType == "T_DIF_BOUNDARY":
			values = self.T_DIF_BOUNDARY
			cbox = True
		if propertyType == "T_SUBSTRATE":
			values = self.GetSubstrateList()
			isSubstrateList = True
			cbox = True	
		
		return cbox, values, isSubstrateList
			
	## Recursive function to unpack JSON data into the tree viewer
	def UnpackJSONModelIntoTree(self, jsonData, node, tree, path=None, appendPath=True):
		
		itemName = tree.GetItemText(node)
		if path == "":
			path = itemName
		elif not path:
			path = ""
		else:
			if appendPath:
				path = path + "." + itemName
			
		#if len(itemName) == 0:
		#	return
			
		# Base case - if the data is base type (string, integer, etc.) then set the node's text to be this value
		if(self.IsBaseType(jsonData)):
			#self.tree.SetItemText(node, str(jsondata), 1)
			self.BuildTreeWidget(tree, node, jsonData)

			return
			
		# Case 1 - the data is in a list form
		if isinstance(jsonData, list):
					
			for item in jsonData:
				# if the items in list are of the base type, use this array as the node's value
				if(self.IsBaseType(item)):
					#self.tree.SetItemText(node, str([str(value) for value in jsondata]), 1)
					self.BuildTreeWidget(tree, node, jsonData)
					return		
			
				# otherwise unpack each array item individually (incase the array contains more complex items
				#child = tree.AppendItem(node, itemText)
				#self.UnpackJSONModelIntoTree(jsondata[item], child, tree)	
				self.UnpackJSONModelIntoTree(item, node, tree, path, False)	
				#print "item: " + itemText
			return
				
			
		# Case 2 - the data must be in a dictionary form
		for item in jsonData:	
					
			#print "THE ITEM: " + str(item)
			keyType = None
			#print "STUFFF: " + str(jsonData[item])
			
			thePath = path+"."+item
				
			propertyData = self.GetPropertyData(self.library, thePath)
			propertyType = propertyData[0]
			wasKey = propertyData[1]
			
			#print "AYY: " + itemName + "\t" + str(propertyType)
			if propertyType and wasKey:
				if propertyType in self.userDefinedKeys and not "_ID" in propertyType:
					keyType = propertyType
					#print "PATH: " + path + "\tkeytype: " + keyType
	
					
					tree.SetAGWWindowStyleFlag(ct.TR_HAS_VARIABLE_ROW_HEIGHT | ct.TR_HAS_BUTTONS | ct.TR_DEFAULT_STYLE)
								
					cbox, values, isSubstrateList = self.CheckPropType(propertyType)
					combo = MyComboBox(tree, path, values)
					combo.SetValue("")
					
					self.tree.Bind(wx.EVT_COMBOBOX, self.EditUserDefinedKey, combo)
				
					child = tree.AppendItem(node, item, wnd=combo)
					
					combo.SetChild(child)
					
					if isSubstrateList:
						self.substrateLists[self.filename].append(combo)
			
					
			if not keyType:
				# create a child node attached to the parent node with the items name
				child = tree.AppendItem(node, item)
			
			# get and unpack the item's dictionary data (passing the new child node as the parent node)
			data = jsonData[item]
			self.UnpackJSONModelIntoTree(data, child, tree, path)
			
	
			
	def BuildTreeWidget(self, tree, node, jsondata):
			
		key = tree.GetItemText(node)
		path = self.GetItemPath(node) + "." + key
		
		propertyData = self.GetPropertyData(self.library, path)
		propertyType = propertyData[0]
		
		cbox, values, isSubstrateList = self.CheckPropType(propertyType)
					
		if cbox:
			#print values
			tree.SetAGWWindowStyleFlag(ct.TR_HAS_VARIABLE_ROW_HEIGHT | ct.TR_HAS_BUTTONS | ct.TR_DEFAULT_STYLE)
						
			self.combo = wx.ComboBox(tree, choices=values)
			self.combo.SetValue(str(jsondata))
			child = tree.AppendItem(node, "", wnd=self.combo)
								
			if isSubstrateList:
				self.substrateLists[self.filename].append(self.combo)
		else:
			tree.SetAGWWindowStyleFlag(ct.TR_HAS_VARIABLE_ROW_HEIGHT | ct.TR_HAS_BUTTONS | ct.TR_DEFAULT_STYLE)
		
		
			#arrayAsText = str([str(value) for value in jsondata]).translate(None, "'")
			child = tree.AppendItem(node, str(jsondata))		
						
	## Recursive function to unpack JSON data into the tree viewer
	def UnpackJSONModelIntoLibraryTree(self, jsondata, node, tree):
		
		# Base case - if the data is base type (string, integer, etc.) then set the node's text to be this value
		if(self.IsBaseType(jsondata)):
			#self.tree.SetItemText(node, str(jsondata), 1)
			child = tree.AppendItem(node, str(jsondata))
			return
			
		# Case 1 - the data is in a list form
		if isinstance(jsondata, list):
			for item in jsondata:
				
				# if the items in list are of the base type, use this array as the node's value
				if(self.IsBaseType(item)):
					#self.tree.SetItemText(node, str([str(value) for value in jsondata]), 1)
					arrayAsText = str([str(value) for value in jsondata]).translate(None, "[]'")
					child = tree.AppendItem(node, arrayAsText)
					return		
			
				# otherwise unpack each array item individually (incase the array contains more complex items, but this probably isn't needed)
				self.UnpackJSONModelIntoLibraryTree(item, node, tree)	
			return
				
		# Case 2 - the data must be in a dictionary form
		for item in jsondata:
			
			# create a child node attached to the parent node with the items name
			child = tree.AppendItem(node, item)
			
			# get and unpack the item's dictionary data (passing the new child node as the parent node)
			data = jsondata[item]
			self.UnpackJSONModelIntoLibraryTree(data, child, tree)
			
			
	def GetCurrentModel(self):
		print self.filename
		return self.models[self.filename]
		
	def GetCurrentModelErrors(self):
		return self.errors[self.filename]
		
	def GetSubstrateList(self):
		substrates = self.GetCurrentModel()["substrates"]
		
		self.results = []
		for substrate in substrates:
			for key in substrate.keys():
				self.results.append(key)
			
		try:
			for cbox in self.substrateLists[self.filename]:
				for n in range(cbox.GetCount()):
					cbox.SetString(n, self.results[n])
		except Exception, e:
			print e 		
			
		return self.results
		
	## Returns true if the value is a base type (stng, integer or float)
	def IsBaseType(self, value):
		return isinstance(value, basestring) or isinstance(value, int) or isinstance(value, float)
		 

	def OnMouseMotion(self, event):
		ameClientPos = event.GetPosition()
		desktopPos = self.ClientToScreen( frameClientPos )  # Current cursor desktop coord
		print '----  MyFrame::OnMouseMotion()     mouse is at: ', desktopPos

	def OnDrag(self, event):
		print "Starting to drag"
		event.Allow()
		item = event.GetItem()
		dataObject = VarNodeDropData()
		
		dataObject.setNode(self.GetJSONTemplate(item))       
       
		dropSource = wx.DropSource(self)
		dropSource.SetData(dataObject)
		result = dropSource.DoDragDrop(wx.Drag_DefaultMove)
		
		print "Finshed", result
		event.Skip()
       
	def GetJSONTemplate(self, item):
		return {"New module": [{"A":"a", "B": "b", "C":"c"}]}
		
	## User has hovered a menubar item
	def OnMenuHighlight(self, event):
		id = event.GetMenuId()
		item = self.GetMenuBar().FindItemById(id)
		if item:
			text = item.GetText()
			help = item.GetHelp()
			self.SetStatusText(help)
		event.Skip() 
		
		
	## User has right-clicked a tree item
	def OnRightClick(self, event):
		if not hasattr(self, "popup_add"):
			self.popup_add = wx.NewId()
			self.popup_copy = wx.NewId()
			self.popup_paste = wx.NewId()
			self.popup_delete = wx.NewId()
			self.popup_import = wx.NewId()
			self.popup_export = wx.NewId()
			self.popup_parameters = wx.NewId()
				
		self.menu = wx.Menu()
		
		item1 = wx.MenuItem(self.menu, self.popup_add,"Add")
		self.menu.AppendItem(item1)
		item2 = wx.MenuItem(self.menu, self.popup_copy,"Copy")
		self.menu.AppendItem(item2)
		item3 = wx.MenuItem(self.menu, self.popup_paste,"Paste")
		self.menu.AppendItem(item3)
		item4 = wx.MenuItem(self.menu, self.popup_delete,"Delete")
		self.menu.AppendItem(item4)
		
        # submenu
		sm = wx.Menu()
		
		item5 = wx.MenuItem(self.menu, self.popup_import,"Import")
		sm.AppendItem(item5)
		item6 = wx.MenuItem(self.menu, self.popup_export,"Export")
		sm.AppendItem(item6)
		
		self.menu.AppendMenu(self.popup_parameters, "Parameters", sm)
		
		self.Bind(wx.EVT_MENU, self.Add, item1)
		self.Bind(wx.EVT_MENU, self.Copy, item2)
		self.Bind(wx.EVT_MENU, self.Paste, item3)
		self.Bind(wx.EVT_MENU, self.Delete, item4)
		self.Bind(wx.EVT_MENU, self.Import, item5)
		self.Bind(wx.EVT_MENU, self.Export, item6)
		
		# Post the event
		wx.PostEvent(self.GetEventHandler(), wx.PyCommandEvent(wx.EVT_LEFT_DOWN.typeId, self.GetId()))
		item = self.tree.HitTest(event.GetPoint())[0]
		self.tree.Unselect()
		self.tree.SelectItem(item)
		#itemText = self.tree.GetItemText(item)
		
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
		self.PopupMenu(self.menu)
		self.menu.Destroy()
	


	#######################################################################################
	########				RIGHT CLICK FUNCTIONS								  #########
	#######################################################################################
	
	def Add(self, event):
		item = self.menu.FindItemById(event.GetId())
		print "Add"
		
		win = OtherFrame(title="Add module")
		
		modules = ['Module 1', 'Module 2', 'Module 3', 'Module 4', 'Module 5', 'Module 6', 'Module 7'] 
		listView = wx.ListBox(win, size=(100,-1), choices=modules, style=wx.LB_SINGLE)


		
		win.Show(True)
   
		
	def Copy(self, event):
		item = self.menu.FindItemById(event.GetId())
		print "Copy"
		
	def Paste(self, event):
		item = self.menu.FindItemById(event.GetId())
		print "Paste"
		
	def Delete(self, event):
		item = self.menu.FindItemById(event.GetId())
		print "Delete"
		
	def Import(self, event):
		item = self.menu.FindItemById(event.GetId())
		print "Import"
		
	def Export(self, event):
		item = self.menu.FindItemById(event.GetId())
		popup = TestPopup(self.GetTopLevelParent(), wx.SIMPLE_BORDER)
		popup.Show()
		
		print "Export"
		

	#######################################################################################
	########				MODEL TREE EVENTS									  #########
	#######################################################################################
		 
	## User has double-clicked a tree item
	def OnActivate(self, event):
		self.tree.EditLabel(self.tree.GetSelection())
	
	## User has single-clicked a tree item
	def OnSelection(self, event):
		selected = self.tree.GetSelection()
		self.propertyPanel.SetValue(str(self.tree.GetItemText(selected)) + "\t" + str(self.GetItemPath(selected)) + "\t" + str(self.GetPropertyDataByItem(selected)[0]) + "\n\n" + str(self.GetPropertyDataByItem(selected)[2]))
	
	def OnCollapse(self, event):
		pass
		
	def OnEditCompletion(self, event):
		
		self.ValidateModel()
		
		item = event.GetItem()
		old_value = self.tree.GetItemText(item)
		new_value = event.GetLabel()
		
		self.UpdateCoreModel(item, new_value, old_value)
		self.updateFlag = True
		
	def EditUserDefinedKey(self, event):
		item = event.GetClientObject()
		self.tree.SetItemText(item.GetChild(), event.GetString())
		item.SetValue("")
		self.ValidateModel()
	
	def UpdateErrorPaths(self, path, newValue, oldValue):
		
		for error in self.errors[self.filename]:
			if path in error:
				
				newError = error.replace(oldValue, newValue)
				print "SUBED: " + error + " \tfor:\t"+ newError
				self.errors[self.filename].remove(error)
				self.errors[self.filename].append(newError)
			
		
	def UpdateCoreModel(self, item, new_value, old_value):
		path = self.GetItemPath(item)
		
		
		if not new_value or new_value == "":
			new_value = old_value
			
		self.UpdateErrorPaths(path, new_value, old_value)
		
		self.UpdateCoreModelRecursively(item, new_value, old_value, path, self.GetCurrentModel())
		
	def UpdateCoreModelRecursively(self, item, new_value, old_value, path, data, parent=None, old_path=None):
		itemText = self.tree.GetItemText(item)
		print "ITEM: " + str(itemText) + "\t NEW VALUE: " + str(new_value) + "\t OLD VALUE: " + str(old_value) + "\tPATH: " + str(path)
		if not old_path:
			old_path = path
			
		if not path:
			path = old_path
			
		if not parent:
			parent = self.GetCurrentModel()
			
		tokens = path.split(".")
		target = tokens[0]

		
			
		if isinstance(data, list):
			for entry in data:
			#	print "NTRY: " + str(entry)
				if self.IsBaseType(entry):
					if entry == target:
						print "YES " + entry + " is equal to " + target
						#print str(len(path.split(".")))
						if len(tokens) > 1:
							if self.UpdateCoreModelRecursively(item, new_value, old_value, ".".join(tokens[1:]), data[entry], data, old_path):
								return True
							continue
						#print("FOUND! ["+ entry +" = " +new_value+"] target = " + str(target) + "\told val: " + str(old_value)) 
						#print "PATH: " + path
						#print "fPATH: " + old_path
						
						if not target == old_value:
							data[target] = new_value
							return True
							
						data[new_value] = data.pop(key)
						
						return True
				
					continue
				
				if self.UpdateCoreModelRecursively(item, new_value, old_value, ".".join(tokens), entry, data, old_path):
					return True
			return False
			
		for key in data.keys():
			if key == target:
				print "YES " + key + " is equal to " + target
				#print str(len(path.split(".")))
				if len(tokens) > 1:
					if self.UpdateCoreModelRecursively(item, new_value, old_value, ".".join(tokens[1:]), data[key], data, old_path):
						return True
					continue
				#print("FOUND! ["+ key +" = " +new_value+"] target = " + str(target) + "\told val: " + str(old_value)) 
				#print "PATH: " + path
				#print "fPATH: " + old_path
				
				if not target == old_value:
					data[target] = new_value
					return True
					
				data[new_value] = data.pop(key)
				
				return True
			
			value = data[key]
			if self.IsBaseType(value):
				continue
				
			if isinstance(value, list):
				for entry in value:
					if self.IsBaseType(entry):
						continue
					if self.UpdateCoreModelRecursively(item, new_value, old_value, ".".join(tokens[1:]), entry, value, old_path):
						return True
				continue
						
						
	def NewDomain(self, event):
		win = OtherFrame(title="New domain")
		

		width, height = wx.GetDisplaySize()
		width = width / 15
		innerPanel = wx.Panel(win)
		
		xLower = wx.StaticText(innerPanel, label="xLower: ")
		xLowerInput = wx.TextCtrl(innerPanel, size=(width, -1), value="-100")
		xUpper = wx.StaticText(innerPanel, label="xUpper: ")
		xUpperInput = wx.TextCtrl(innerPanel, size=(width, -1), value="100")
		
		yLower = wx.StaticText(innerPanel, label="yLower: ")
		yLowerInput = wx.TextCtrl(innerPanel, size=(width, -1), value="-100")
		yUpper = wx.StaticText(innerPanel, label="yUpper: ")
		yUpperInput = wx.TextCtrl(innerPanel, size=(width, -1), value="100")
		
		zLower = wx.StaticText(innerPanel, label="zLower: ")
		zLowerInput = wx.TextCtrl(innerPanel, size=(width, -1), value="-100")
		zUpper = wx.StaticText(innerPanel, label="zUpper: ")
		zUpperInput = wx.TextCtrl(innerPanel, size=(width, -1), value="100")
		

		button = wx.Button(innerPanel, label="Add domain to model")
		
		windowSizer = wx.BoxSizer()
		windowSizer.Add(innerPanel, 1, wx.ALL | wx.EXPAND)   
        
		border = 5
        
		sizer = wx.GridBagSizer(7, 7)
		sizer.Add(xLower, (0, 0), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(xLowerInput, (0, 1), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(xUpper, (1, 0), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(xUpperInput, (1, 1), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(yLower, (2, 0), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(yLowerInput, (2, 1), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(yUpper, (3, 0), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(yUpperInput, (3, 1), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(zLower, (4, 0), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(zLowerInput, (4, 1), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(zUpper, (5, 0), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(zUpperInput, (5, 1), flag=wx.TOP|wx.BOTTOM, border=border)
		sizer.Add(button, (6, 0), (1, 2), flag=wx.EXPAND)

 
        # Set simple sizer for a nice border
		border = wx.BoxSizer()
		border.Add(sizer, 0, wx.ALL | wx.EXPAND, 5)

		innerPanel.SetSizerAndFit(border)  
		win.SetSizerAndFit(windowSizer)  
		
	def NewBacteria(self, event):
		win = OtherFrame(title="New bacteria")
		

		width, height = wx.GetDisplaySize()
		width = width / 5
		innerPanel = wx.Panel(win)
		
		modelName = wx.StaticText(innerPanel, label="Bacteria name: ")
		modelNameInput = wx.TextCtrl(innerPanel, size=(width, -1))

		button = wx.Button(innerPanel, label="Add bacteria to model")
		
		windowSizer = wx.BoxSizer()
		windowSizer.Add(innerPanel, 1, wx.ALL | wx.EXPAND)   
        
		sizer = wx.GridBagSizer(5, 5)
		sizer.Add(modelName, (0, 0), flag=wx.TOP|wx.BOTTOM, border=10)
		sizer.Add(modelNameInput, (0, 1), flag=wx.TOP|wx.BOTTOM, border=10)
		sizer.Add(button, (2, 0), (1, 3), flag=wx.EXPAND)

 
        # Set simple sizer for a nice border
		border = wx.BoxSizer()
		border.Add(sizer, 0, wx.ALL | wx.EXPAND, 5)

		innerPanel.SetSizerAndFit(border)  
		win.SetSizerAndFit(windowSizer)  
	
	
	def NewGrowth(self, event):
		win = OtherFrame(title="New growth kinetic")

		
	def NewPermeation(self, event):
		win = OtherFrame(title="New permeation")
		
		
	
	#######################################################################################
	########				MODEL CREATION										  #########
	#######################################################################################
		
	def NewModel(self, event):
		win = OtherFrame(title="New model")
		

		width, height = wx.GetDisplaySize()
		width = width / 5
		innerPanel = wx.Panel(win)
		
		modelName = wx.StaticText(innerPanel, label="Name: ")
		modelNameInput = wx.TextCtrl(innerPanel, size=(width, -1))
		
		modelType = wx.StaticText(innerPanel, label="Type: ")
		modelTypes = ['Case study 1', 'Case study 2', 'Fast biofilm', 'Slow biofilm'] 
		modelTypeInput = wx.ListBox(innerPanel, size=(width, 100), choices=modelTypes, style=wx.LB_SINGLE)
     



		button = wx.Button(innerPanel, label="Create model")
		
		windowSizer = wx.BoxSizer()
		windowSizer.Add(innerPanel, 1, wx.ALL | wx.EXPAND)   
        
		sizer = wx.GridBagSizer(5, 5)
		sizer.Add(modelName, (0, 0), flag=wx.TOP|wx.BOTTOM, border=10)
		sizer.Add(modelNameInput, (0, 1), flag=wx.TOP|wx.BOTTOM, border=10)
		sizer.Add(modelType, (1, 0), flag=wx.TOP|wx.BOTTOM, border=10)
		sizer.Add(modelTypeInput, (1, 1), flag=wx.TOP|wx.BOTTOM, border=10)
		sizer.Add(button, (2, 0), (1, 3), flag=wx.EXPAND)

 
        # Set simple sizer for a nice border
		border = wx.BoxSizer()
		border.Add(sizer, 0, wx.ALL | wx.EXPAND, 5)

		innerPanel.SetSizerAndFit(border)  
		win.SetSizerAndFit(windowSizer)  

		
	def CloseModel(self, event):
		self.substrateLists[self.filename] = []
		print("Close model")
					
	def SetAffinityConstants(self, event):
		win = OtherFrame(title="Affinity constants")#TestPopup(self.GetTopLevelParent(), wx.SIMPLE_BORDER)
		
		table = grid.Grid(win)
		table.CreateGrid(3, 3)
		
		table.SetCellValue(1, 1, "lol1")
				
	def SetChemicalSpeciesEnergy(self, event):
		win = OtherFrame(title="Chemical species energy coefficients")#TestPopup(self.GetTopLevelParent(), wx.SIMPLE_BORDER)
		
		table = grid.Grid(win)
		table.CreateGrid(3, 3)
		
		table.SetCellValue(1, 1, "lol2")
				
	def RunModel(self, event):
		win = OtherFrame(title="Run model")
		
	def SetInterfaceFont(self, event): 
		dlg = wx.FontDialog(self,wx.FontData()) 
		
		#data = wx.FontData()
		#data.EnableEffects(True)
		#data.SetColour(self.curClr)         # set colour
		#data.SetInitialFont(self.curFont)
 
		#dlg = wx.FontDialog(self, data)
        
		try:
			if dlg.ShowModal() == wx.ID_OK: 
				data = dlg.GetFontData() 
				font = data.GetChosenFont() 
				colour = data.GetColour()
				
				self.curFont = font
				self.curClr = colour
				
				self.SetAllWidgetFonts(font)
			
		finally:
			print "HMM"
			dlg.Destroy()
		
	def SetAllWidgetFonts(self, font):
		self.SetWidgetFontRecursively(self, font)
		
	def SetWidgetFontRecursively(self, widget, font):
		try:
			widget.SetFont(font)
		except Exception:
			print "Failed to set font"
		
		for child in widget.GetChildren():
			self.SetWidgetFontRecursively(child, font)
		
	def Save(self, event):
		print("Save")
		dlg = wx.FileDialog(self, message="Save file as ...", defaultDir="/home/jonny", defaultFile="", style=wx.FD_SAVE)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			print "You chose the following filename: %s" % path
			self.SaveFile(path)
		dlg.Destroy()
 
 
			
	def SaveFile(self, filename):
		try:
			with open(filename, 'w') as outfile:
				json.dump(self.GetCurrentModel(), outfile)
		except:
			print "ERROR SAVING!"
			
		
	def SaveAs(self, event):
		print("Save as")
		
	def ValidateModel(self):
		
		model = self.GetCurrentModel()
		errors = self.GetCurrentModelErrors()
		
		# update the substrate list
		self.GetSubstrateList()
		self.LoopModel(model)
		
		
				
		for err in errors:
			print "ValidateModel() - error: " + err
			self.SetModelItemBackgroundColour(err, self.colour_red)	
				
		self.errors[self.filename] = list(set(errors))
				
	def LoopModel(self, jsondata, parent=None, path=None):
		
		# Base case - if the data is base type (string, integer, etc.) then set the node's text to be this value
		if(self.IsBaseType(jsondata)):
			self.ValidateProperty(parent, jsondata)
			return
			
		# Case 1 - the data is in a list form
		if isinstance(jsondata, list):
			for item in jsondata:
				
				if(self.IsBaseType(item)):
					self.ValidateProperty(parent, jsondata)
					
		
					return		
			
				self.LoopModel(item, parent)	
				return
				
		# Case 2 - the data must be in a dictionary form
		for item in jsondata:
			
			
			data = jsondata[item]
			if parent:
				item = str(parent) + "." + str(item)
			self.LoopModel(data, item)
	
	def ValidateProperty(self, propertyName, value):
		#print "Validating: " + str(propertyName) + ", " + str(value)
		propertyData = self.GetPropertyData(self.library, propertyName, None)
		propertyType = propertyData[0]
		wasKey = propertyData[1]
		
		#print "- should be type: " + str(propertyType)
		
		if not propertyType:
			return
			
		if "_ARRAY_" in propertyType:
			#print "HEREEE"+propertyName
			length = propertyType.split("_")[len(propertyType.split("_"))-1]
			propertyType = "_".join(propertyType.split("_")[:-2])
		#	print "LNE: "+ str(length)
			if not isinstance(value, list):
				return False
			#print "LNEddddd: " + str(value)
				
			if not len(value) == int(length):
				self.errors[self.filename].append[propertyName]
				return
				
			for entry in value:
				self.ValidatePropertyIndividually(propertyName, entry, propertyType)
			return
			
		self.ValidatePropertyIndividually(propertyName, value, propertyType)
			
	def ValidatePropertyIndividually(self, propertyName, value, propertyType):
		
		error = False
		if propertyType == "T_INT":
			if not isinstance(value, int) and not self.isint(value):
				error = True
				#print "NOT INT ["+str(propertyName)+"]"
				
		if propertyType == "T_NUM":
			if not isinstance(value, float) and not self.isfloat(value):
				error = True
				
		if propertyType == "T_STRING":
			if not isinstance(value, basestring):
				error = True
				#print "NOT STRING"
		
		if propertyType == "T_BOUNDARY":
			if not value in self.T_BOUNDARY:
				error = True
				#print "NOT BOUNDARY"
				
		if propertyType == "T_DIF_BOUNDARY":
			if not value in self.T_DIF_BOUNDARY:
				error = True
				#print "NOT DIF BOUNDARY"
				
		if propertyType == "T_ENERGY":
			if not value in self.T_ENERGY:
				error = True
				#print "NOT ENERGY FORM"
				
		if propertyType == "T_STATUS":
			if not value in self.T_STATUS:
				error = True
				#print "NOT STATUS FORM"
				
		if not error and propertyName in self.GetCurrentModelErrors(): 
			print propertyName + " IS FINE"
			self.SetModelItemBackgroundColour(propertyName, self.colour_white)
			self.errors[self.filename].remove(propertyName)
				
		if error:
			print "new" + str(propertyName)
			if not propertyName in self.GetCurrentModelErrors():
				self.errors[self.filename].append(propertyName)
			else:
				print "HERE" + str(propertyName)
		
		
	
	def isfloat(self, value):
		try:
			float(value)
			return True
		except ValueError:
			return False
    	
	def isint(self, value):
		try:
			int(value)
			return True
		except ValueError:
			return False

			
	def SetModelItemBackgroundColour(self, propertyName, colour):
		items = self.GetModelItemAndParentsRecursively(propertyName, self.tree.GetRootItem(), [])
		for item in items:
			self.tree.SetItemBackgroundColour(item, colour)
			
	
	def GetModelItem(self, propertyFullPath):
		return self.GetModelItemRecursively(propertyFullPath, self.tree.GetRootItem())
	
	def GetModelItemRecursively(self, propertyFullPath, node, full_path=None):
		if not full_path:
			full_path = propertyFullPath
			
		tokens = propertyFullPath.split(".")
			
		if not "." in propertyFullPath:
			item, cookie = self.tree.GetFirstChild(node)
			
			while item.IsOk():
				if self.tree.GetItemText(item) == propertyFullPath:
					return item
				item, cookie = self.tree.GetNextChild(node, cookie)
			return node
			
		target = tokens[0]

		item, cookie = self.tree.GetFirstChild(node)

		try:
			while item.IsOk():
				if self.tree.GetItemText(item) == target:
					return self.GetModelItemRecursively(".".join(tokens[1:]), item, full_path)
				item, cookie = self.tree.GetNextChild(node, cookie)
		except Exception:
			print "FAILED: " + propertyFullPath
			
		return False
			
	def GetModelItemAndParentsRecursively(self, propertyFullPath, node, parents=[]):
		parents.append(node)
		tokens = propertyFullPath.split(".")
		print "try: " + propertyFullPath	
		
		if not "." in propertyFullPath:
			item, cookie = self.tree.GetFirstChild(node)
			while item.IsOk():
				if self.tree.GetItemText(item) == propertyFullPath:
					parents.append(item)
					return parents
				item, cookie = self.tree.GetNextChild(node, cookie)
		
			
		target = tokens[0]
		
		try:
			item, cookie = self.tree.GetFirstChild(node)
				
			while item.IsOk():
				print "IS OK: " +  self.tree.GetItemText(item)
				if self.tree.GetItemText(item) == target:
					return self.GetModelItemAndParentsRecursively(".".join(tokens[1:]), item, parents)
				item, cookie = self.tree.GetNextChild(node, cookie)
		except Exception:
			print "FAILED: " + propertyFullPath
			
		return False
		
	def DoesItemExist(self, tree, match, root):
		item, cookie = tree.GetFirstChild(root)

		while item.IsOk():
			if tree.GetItemText(item) == match:
				return True
			if tree.ItemHasChildren(item):
				if self.DoesItemExist(tree, match, item):
					return True
			item, cookie = tree.GetNextChild(root, cookie)
		return False
	
			
	def GetItemPath(self, item, currentPath=None):
		parent = self.tree.GetItemParent(item)
		if not parent:
			return currentPath
			
		itemText = self.tree.GetItemText(item)

		if not self.tree.ItemHasChildren(item):
			itemText = ""
		
		if currentPath:
			if not self.tree.ItemHasChildren(item):
				newPath = currentPath
			else:
				newPath = itemText + "." + currentPath
		else:
			newPath = itemText
		return self.GetItemPath(parent, newPath)
		
	def GetPropertyDescriptionByItem(self, item):
		path = self.GetItemPath(item) + ".description"
		return self.GetPropertyDescription(self.library, path)
		
	def GetPropertyDescription(self, jsonData, fullPath, item=None, parentDescription=""):
		tokens = fullPath.split(".")
		newPath = ".".join(tokens[1:])
		print jsonData
		print "A"
		description = parentDescription
		if self.IsBaseType(jsonData):
			print "AB"
			return description
		
		if isinstance(jsonData, dict):	
			print tokens
			
			print "B"
			if "description" in jsonData.keys():
				description = jsonData["description"]
				print "LOL"
				
			if len(tokens) == 1:
				print "C"
				if item == tokens[0]:
					print "YO"
					return description
				return description
			
				
			print "D"
			for item in jsonData:
				if item == tokens[0] or item in self.userDefinedKeys:
					print "E: " + item
					return self.GetPropertyDescription(jsonData[item], newPath, item, description)
		
			print "F"
			return ""
			
		if isinstance(jsonData, list):
			for item in jsonData:
				if not item:
					continue
				if self.IsBaseType(item):
					return parentDescription
				else:
					return self.GetPropertyDescription(item, newPath, item, description)	
					
	def GetPropertyDataByItem(self, item):
		path = self.GetItemPath(item)
		propertyData = self.GetPropertyData(self.library, path, item)
		return propertyData
	
	def GetPropertyData(self, jsonData, fullPath, item=None, description=""):
		tokens = []
		
		try:
			tokens = fullPath.split(".")
		except Exception:
			pass
			
		if self.IsBaseType(jsonData):
			return [jsonData, False, description]
		
		if isinstance(jsonData, dict):	
			
			if "description" in jsonData.keys():
				description = jsonData["description"]
				
			keyType = None
			
			if len(jsonData) == 0:
				return [None, False, description]
				
			key = jsonData.keys()[0]
			
			if key:
				if key in self.userDefinedKeys:
					keyType = key
			
			
			index = tokens[0]
			if index == "":
				return [None, False, description]
		
			
			# this is not a recognised modelling component
			if not index in jsonData:
				if not keyType:
					return [None, False, description]
				
			if keyType:
				newJsonData = jsonData[keyType]
				newPath = ".".join(tokens[1:])
				
				if len(newPath) == 0:
					if "description" in newJsonData:
						description = newJsonData["description"]
					return [keyType, True, description]
			else:
				newJsonData = jsonData[index]
				newPath = ".".join(tokens[1:])
				
			return self.GetPropertyData(newJsonData, newPath, item)
		
		if isinstance(jsonData, list):
			for item in jsonData:
				if not item:
					continue
				if self.IsBaseType(item):
					return [str(item) + "_ARRAY_"+str(len(jsonData)), False, description]
				else:
					return self.GetPropertyData(item, fullPath, item)
                    
## Main function
if __name__ == '__main__':
	from wx.lib.mixins.inspection import InspectionMixin
   
	class TestApp(wx.App, InspectionMixin): 
		def OnInit(self): 
			self.Init() 
			frame = GUI(None)
               

			width, height = wx.GetDisplaySize()
			frame.SetTitle("NUFEB Modelling Environment")
			frame.SetDimensions(0, 0, width, height)
			frame.Centre()
			self.SetTopWindow(frame)
               
			#frame.SetMinSize((1024,768))
			frame.Show()
               
			return 1 
           
	app = TestApp()
    
	app.MainLoop()
