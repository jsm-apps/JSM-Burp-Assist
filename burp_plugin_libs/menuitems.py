from java.util import ArrayList
from javax.swing import JMenuItem

class MenuItems():
    def __init__(self, invocation):
        self.invocation = invocation

    def getMenuItems(self, _handle_tech_detect, _handle_xss_detection, _handle_question):
        menu = ArrayList()
        item = JMenuItem(
            "Technology Detect",
            actionPerformed=lambda event:
                _handle_tech_detect(self.invocation)
        )
        menu.add(item)

        item2 = JMenuItem(
            "XSS Detection",
            actionPerformed=lambda event:
                _handle_xss_detection(self.invocation)
        )  
        menu.add(item2)

        item3 = JMenuItem(
            "Ask Question...",
            actionPerformed=lambda event:
                _handle_question(self.invocation)
        )        
        menu.add(item3)
        return menu