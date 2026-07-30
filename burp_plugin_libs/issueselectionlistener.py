from javax.swing.event import ListSelectionListener

class IssueSelectionListener(ListSelectionListener):

    def __init__(self, issue_manager):
        self.issue_manager = issue_manager

    def valueChanged(self, event):
        if event.getValueIsAdjusting():
            return

        self.issue_manager.show_selected_issue()