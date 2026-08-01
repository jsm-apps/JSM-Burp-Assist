from java.awt.event import ActionListener
from urlparse import urlparse
from java.lang import Thread

from burp_plugin_libs.intruder.intruderworker import IntruderWorker

MARKER = u"\u00A7"

class IntruderStartAction(ActionListener):
    def __init__(
        self,
        callbacks,
        helpers,
        results_tablemodel,
        target,
        http_request_template
    ):
        self.callbacks = callbacks
        self.helpers = helpers
        self.results_tablemodel = results_tablemodel
        self.target = target
        self.http_request_template = http_request_template

        self.worker = None
        self.worker_thread = None

    def actionPerformed(self, event):
        if (
            self.worker_thread is not None
            and self.worker_thread.isAlive()
        ):
            return

        raw_http_request_template = self.http_request_template.getText()

        self.worker = IntruderWorker(
            http_request_template=raw_http_request_template,
            apply_payload=self.apply_payload,
            make_request=self.makeRequest,
            results_tablemodel=self.results_tablemodel
        )

        self.worker_thread = Thread(
            self.worker,
            "JSM-Intruder-Worker"
        )

        self.worker_thread.start()

    def pause_worker(self):
        if self.worker is not None:
            self.worker.pause()

    def resume_worker(self):
        if self.worker is not None:
            self.worker.resume()

    def stop_worker(self):
        if self.worker is not None:
            self.worker.stop()

    def apply_payload(self, text_block, payload):
        """
        Replace every §...§ placeholder with the same payload.
        Compatible with Jython 2.7.
        """
        if text_block is None:
            return None

        result = []
        position = 0

        while True:
            start = text_block.find(MARKER, position)

            if start == -1:
                result.append(text_block[position:])
                break

            end = text_block.find(MARKER, start + len(MARKER))

            # Unmatched marker: preserve the rest unchanged.
            if end == -1:
                result.append(text_block[position:])
                break

            result.append(text_block[position:start])
            result.append(payload)

            position = end + len(MARKER)

        return u"".join(result)

    def makeRequest(self, http_request):
        baseurl = self.target.getText()
        if not baseurl:
            return

        parsed = urlparse(baseurl)
        protocol = parsed.scheme
        host = parsed.hostname

        if parsed.port:
            port = parsed.port
        elif protocol == "https":
            port = 443
        else:
            port = 80

        service = self.helpers.buildHttpService(host, port, protocol)
        request_bytes = self.helpers.stringToBytes(http_request)
        result = self.callbacks.makeHttpRequest(service, request_bytes)
        response_bytes = result.getResponse()
        if response_bytes is None:
            print("No response received.")
            return

        response_info = self.helpers.analyzeResponse(response_bytes)

        status_code = response_info.getStatusCode()
        response_length = len(response_bytes)

        return status_code, response_length, self.helpers.bytesToString(request_bytes), self.helpers.bytesToString(response_bytes)
