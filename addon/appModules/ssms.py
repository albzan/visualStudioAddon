# App Module file for Object Explorer TreeView
# (c) 2017 Alberto Zanella - Fondazione Bruno Kessler (FBK)
import controlTypes
from NVDAObjects.IAccessible.sysTreeView32 import TreeViewItem
from NVDAObjects.IAccessible import IAccessible
import devenv
import api
from UIATextEditor import TextEditor
from NVDAObjects.UIA import UIA 
from logHandler import log


class AppModule(devenv.AppModule):
	def getObjExplorerItem(self,obj) :
		obj.invalidateCaches()
		parent = obj.IAccessibleObject.accParent
		# log.info("original child id "+str(obj.event_childID))
		childcount = int(parent.accChildCount)
		# log.info("child count "+str(childcount))
		child = 0
		accObj = None
		while ((child == 0) or (accObj)) :
			child = child + 1
			try :
				accObj = parent.accChild(child)
			except : pass
			if accObj and (accObj.accState() & 2):
				objr = IAccessible(windowHandle=obj.parent.windowHandle,IAccessibleObject=accObj)
				# log.info("correct child id "+str(child))
				return objr
		return None
	
	def event_NVDAObject_init(self,obj):
		super(AppModule, self).event_NVDAObject_init(obj)
		if (obj.role==controlTypes.ROLE_TREEVIEWITEM) and (controlTypes.STATE_SELECTED not in obj.states) and (obj.parent.name == "Object Explorer Hierarchy") :
			obj2 = self.getObjExplorerItem(obj)
			obj.name = obj2.name
			obj.parent = obj2.parent.parent
			obj.description = None
			obj.states = obj2.states
			obj.location = obj2.location
    
	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		super(AppModule,self).chooseNVDAObjectOverlayClasses(obj, clsList)
		if obj.role == controlTypes.ROLE_TREEVIEWITEM and isinstance(obj,IAccessible) and (obj.parent.name == "Object Explorer Hierarchy") :
			#clsList.insert(0,ObjectExplorerItem)
			clsList.remove(TreeViewItem)
		if devenv.FormsComponent in clsList : 
			clsList.remove(devenv.FormsComponent)
	
	def script_test(self,gesture) :
		pass
	
	__gestures = {
		"kb:control+.": "test",
	}