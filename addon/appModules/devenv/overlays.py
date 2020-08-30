# appModule for visual studio
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2016-2019 Mohammad Suliman, Leonard de Ruijter,
# and Francisco R. Del Roio (https://github.com/leonardder/visualStudioAddon)


import os
import re

import comtypes
import scriptHandler
import eventHandler
import speech
import ui
import braille
import api
from logHandler import log
import UIAHandler
from NVDAObjects import NVDAObject
from NVDAObjects.UIA import Toast_win8 as Toast
from NVDAObjects.UIA import UIA, UIATextInfo, WpfTextView
import controlTypes
from NVDAObjects.behaviors import EditableTextWithSuggestions


def getAddonFolder() -> str:
	"""
	Returns the add-on root folder.

	This would be useful to pick materials from add-on folder, for example sound files.
	"""

	return os.path.abspath(
		os.path.join(__file__, "..", "..", "..")
	)


def playWaveFile(waveFile: str) -> bool:
	"""
	Plays a wave file relative to the root add-on folder.
	"""
	import nvwave

	waveFullPath = os.path.join(
		getAddonFolder(), waveFile
	)

	if not os.path.exists(waveFullPath):
		return False

	nvwave.playWaveFile(waveFullPath)
	return True


class BrailleAwareTextEditorTextInfo(UIATextInfo) :
	def _getTextWithFields_text(self,textRange,formatConfig,UIAFormatUnits=None):
		unit=UIAHandler.TextUnit_Character
		text = self._getTextFromUIARange(textRange)
		if len(text) >= 2 :
			startRange = textRange.clone()
			startRange.ExpandToEnclosingUnit(UIAHandler.TextUnit_Line)
			line = self._getTextFromUIARange(startRange)
			start = re.findall("^[0-9]+ ",line)[0]
			reptxt = re.sub("^[0-9]+ ","",text) #  text.lstrip('0123456789 ')
			if start in text :
				text = reptxt
			
		if text:
			yield text


class TextEditor(WpfTextView):
	def _get_TextInfo(self):
		if braille.handler.display.name != "noBraille" :
			return BrailleAwareTextEditorTextInfo
		return UIATextInfo
	
	def _get_description(self) :
		return None


class IgnoredFocusEntered(NVDAObject):
	def event_focusEntered(self):
		# We should ignore this...
		pass


class DocumentGroup(IgnoredFocusEntered, UIA):
	pass


class DocumentTab(IgnoredFocusEntered, UIA):
	pass


class ToolTabGroup(IgnoredFocusEntered, UIA):
	pass


class ToolTab(IgnoredFocusEntered, UIA):
	pass


class DocumentContent(NVDAObject):

	def _get_documentTab(self) -> UIA:
		currentObj = self

		while currentObj:
			currentObj = currentObj.parent
			if isinstance(currentObj, DocumentTab):
				break

		if currentObj:
			return currentObj

	def _get_name(self):
		return self.documentTab.name

	def _get_positionInfo(self):
		return self.documentTab.positionInfo


class CodeEditor(DocumentContent, EditableTextWithSuggestions, TextEditor):
	"""
	The code editor overlay class.
	"""
	typedCharacter = False

	def event_typedCharacter(self, ch):
		super().event_typedCharacter(ch)
		if self.appModule.openedIntellisensePopup:
			self.typedCharacter = True
		else:
			self.typedCharacter = False

	def event_gainFocus(self):
		if self.appModule.openedIntellisensePopup:
			self.event_suggestionsClosed()
		else:
			super().event_gainFocus()

	def event_suggestionsClosed(self):
		if self.appModule.openedIntellisensePopup:
			self.appModule.openedIntellisensePopup = False
			self.appModule.selectedIntellisenseItem = None
			self.appModule.readIntellisenseHelp = False
			self.appModule.readIntellisenseItem = False
			super().event_suggestionsClosed()

	def event_suggestionsOpened(self):
		if not self.appModule.openedIntellisensePopup:
			self.appModule.openedIntellisensePopup = True
			super().event_suggestionsOpened()

	def event_loseFocus(self):
		self.event_suggestionsClosed()

	@scriptHandler.script(
		gesture="kb:NVDA+d",
		# Translators: Help message for read documentation script
		description=_("Tries to read documentation.")
	)
	def script_readDocumentation(self, gesture):
		firstChild = api.getForegroundObject().firstChild
		documentationObject: UIA = None

		if (
			isinstance(firstChild, UIA)
			and firstChild.UIAElement.CachedClassName == "Popup"
		):
			popupChild = firstChild.firstChild

			if isinstance(popupChild, ParameterInfo):
				# This is the parameter info object
				documentationObject = popupChild

			elif (
				isinstance(popupChild, UIA)
				and popupChild.UIAElement.CachedClassName == "Popup"
				and isinstance(popupChild.firstChild, DocumentationToolTip)
			):
				# Documentation about keywords, classes, interfaces and
				# methods are inside a tooltip container.
				documentationObject = popupChild.firstChild

		if documentationObject:
			helpText: str = ""

			if isinstance(documentationObject, ParameterInfo):
				textInfo = documentationObject.firstChild.next.next.next.makeTextInfo(
					textInfos.POSITION_ALL
				)
				helpText = f"{textInfo.text}\n{documentationObject.firstChild.next.name}"

			elif isinstance(documentationObject, DocumentationToolTip):
				for child in documentationObject.children:
					helpText += f"{child.name}\n"

			if len(helpText) > 0:
				if scriptHandler.getLastScriptRepeatCount() > 0:
					ui.browseableMessage(helpText)
				else:
					ui.message(helpText, speech.Spri.NOW)
		else:
			ui.message(
				# Translators: Announced when documentation cannot be found.
				_("Cannot find documentation."),
				speechPriority=speech.Spri.NOW
			)


class ToolContent(NVDAObject):

	def _get_toolTab(self):
		currentObj = self

		while currentObj:
			currentObj = currentObj.parent

			if isinstance(currentObj, ToolTab):
				break

		if currentObj:
			return currentObj

	def _get_positionInfo(self):
		return self.toolTab.positionInfo if self.toolTab else {}

	def _get_name(self):
		return self.parent.parent.name

	def _get_description(self):
		if "similarItemsInGroup" in self.positionInfo and self.positionInfo["similarItemsInGroup"] > 1:
			# Translators: Help message to indicate that you can switch to another view
			return _("Press CTRL+Page Up to switch to the previous window in this group, and CTRL+Page Down to switch to the next.")


class OutputEditor(ToolContent, TextEditor):
	pass


class ErrorsListView(ToolContent, UIA):
	pass

class ParameterInfo (Toast):
	role = controlTypes.ROLE_TOOLTIP

	def _get_description(self):
		return ""


class DocumentationToolTip(Toast):
	announced = False

	def event_UIA_toolTipOpened(self):
		if not self.announced:
			playWaveFile("sounds/doc.wav")
			self.announced = True


class IntellisenseMenuItem(UIA):

	def _get_editor(self):
		focus = api.getFocusObject()

		if isinstance(focus, CodeEditor):
			return focus

	def _isHighlighted(self):
		try:
			return "[HIGHLIGHTED]=True" in self.UIAElement.CurrentItemStatus
		except comtypes.COMError:
			try:
				return "[HIGHLIGHTED]=True" in self.UIAElement.CachedItemStatus
			except comtypes.COMError:
				return False

	def event_UIA_elementSelected(self):
		if self.editor and not self.appModule.openedIntellisensePopup:
			eventHandler.executeEvent("suggestionsOpened", api.getFocusObject())

		if self.appModule.selectedIntellisenseItem != self:
			# Prepare to read the item when it's name changes:
			self.appModule.readIntellisenseItem = True
			speech.cancelSpeech()
			ui.message(self.name)
			self.appModule.selectedIntellisenseItem = self

	def event_nameChange(self):
		if self.appModule.selectedIntellisenseItem == self and (
			self.editor
			and self.editor.typedCharacter
		):
			self.editor.typedCharacter = False
			speech.cancelSpeech()
			ui.message(self.name)


class IntellisenseLabel(UIA):

	def event_liveRegionChange(self):
		# This is a placeholder.
		if self.appModule.openedIntellisensePopup and not self.appModule.readIntellisenseHelp:
			super().event_liveRegionChange()
			self.appModule.readIntellisenseHelp = True
