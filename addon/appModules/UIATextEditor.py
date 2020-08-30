# App module file for the text editor
# (c) 2017 Alberto Zanella - Fondazione Bruno Kessler (FBK)
import textInfos
import braille
import UIAHandler
from NVDAObjects.UIA import UIA,UIATextInfo
import UIAUtils
import re
from NVDAObjects.UIA import UIA, WpfTextView

class TextEditorTextInfo(UIATextInfo) :
    def _getTextWithFields_text(self,textRange,formatConfig,UIAFormatUnits=None):
        unit=UIAHandler.TextUnit_Character
        text = self._getTextFromUIARange(textRange)
        if len(text) >= 2 :
            startRange = textRange.clone()
            startRange.ExpandToEnclosingUnit(UIAHandler.TextUnit_Line)
            line = self._getTextFromUIARange(startRange)
            start = re.findall("^[0-9]+ .",line)[0]
            reptxt = re.sub("^[0-9]+ ","",text) #  text.lstrip('0123456789 ')
            if start in text :
                text = reptxt
            if "empty line" == reptxt :
                    text = None #back to chars
                    rangeIter=UIAUtils.iterUIARangeByUnit(textRange,unit)
                    for tempRange in rangeIter:
                        txt = self._getTextFromUIARange(tempRange)
                        if len(txt) == 1 :
                            yield txt
        if text:
            yield text
        
        
        
class TextEditor(WpfTextView) :
    oldTether = None
    def _get_TextInfo(self):
        return TextEditorTextInfo
    def _get_description(self) :
        return None
    
    # def event_gainFocus(self) :
        # super(TextEditor,self).event_gainFocus()
        # if self.oldTether == None :
            # self.oldTether = braille.handler.tether
            # braille.handler.tether = braille.handler.TETHER_FOCUS
    
    
    
    # def event_loseFocus(self) :
        # #super(TextEditor,self).event_loseFocus()
        # braille.handler.tether = self.oldTether 
        # self.oldTether = None