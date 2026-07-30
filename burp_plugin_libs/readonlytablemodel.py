from javax.swing.table import DefaultTableModel

class ReadOnlyTableModel(DefaultTableModel):
    """
    Prevent users from editing JTable cells.
    """

    def isCellEditable(self, row, column):
        return False