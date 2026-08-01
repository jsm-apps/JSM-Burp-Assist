from javax.swing.event import ListSelectionListener

class IntruderRowSelectionListener(ListSelectionListener):
    def __init__(
        self,
        table,
        table_model,
        request_textarea,
        response_textarea
    ):
        self._table = table
        self._table_model = table_model
        self._request_textarea = request_textarea
        self._response_textarea = response_textarea

    def valueChanged(self, event):
        # Ignore intermediate selection events.
        if event.getValueIsAdjusting():
            return

        selected_view_row = self._table.getSelectedRow()

        if selected_view_row == -1:
            return

        # Required because setAutoCreateRowSorter(True) is enabled.
        selected_model_row = self._table.convertRowIndexToModel(
            selected_view_row
        )

        request_value = self._table_model.getValueAt(
            selected_model_row,
            4
        )

        response_value = self._table_model.getValueAt(
            selected_model_row,
            5
        )

        if request_value is None:
            request_value = ""

        if response_value is None:
            response_value = ""

        self._request_textarea.setText(str(request_value))
        self._response_textarea.setText(str(response_value))

        self._request_textarea.setCaretPosition(0)
        self._response_textarea.setCaretPosition(0)