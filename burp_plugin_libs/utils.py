class Utils():
    def __init__(self, _print, _print_err, helpers):
        self._print = _print
        self._print_err = _print_err
        self._helpers = helpers

    def get_selected_url_and_response(self, invocation):
        messages = invocation.getSelectedMessages()

        if not messages or len(messages) == 0:
            self._print("No message selected.")
            return None, None

        message = messages[0]
        service = message.getHttpService()

        request = message.getRequest()
        analysed = self._helpers.analyzeRequest(
            service,
            request
        )

        url = str(analysed.getUrl())

        response = message.getResponse()

        if response is None:
            self._print_err(
                "Selected item has no HTTP response."
            )
            return url, None

        raw_http_response = self._helpers.bytesToString(
            response
        )

        return url, raw_http_response, message