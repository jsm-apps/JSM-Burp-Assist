from java.lang import Runnable
from java.util.concurrent.locks import ReentrantLock
from javax.swing import SwingUtilities

from burp_plugin_libs.api_client import TaskApiClient, ApiClientError

class AddResultRow(Runnable):
    def __init__(self, table_model, row):
        self._table_model = table_model
        self._row = row

    def run(self):
        self._table_model.addRow(self._row)



class IntruderWorker(Runnable):
    def __init__(
        self,
        http_request_template,
        apply_payload,
        make_request,
        results_tablemodel
    ):
        self._http_request_template = http_request_template
        self.client = TaskApiClient()
        self._apply_payload = apply_payload
        self._make_request = make_request
        self._results_tablemodel = results_tablemodel

        self._lock = ReentrantLock()
        self._pause_condition = self._lock.newCondition()

        self._paused = False
        self._stopped = False

    def pause(self):
        self._lock.lock()

        try:
            self._paused = True
        finally:
            self._lock.unlock()

    def resume(self):
        self._lock.lock()

        try:
            self._paused = False
            self._pause_condition.signalAll()
        finally:
            self._lock.unlock()

    def stop(self):
        self._lock.lock()

        try:
            self._stopped = True
            self._paused = False
            self._pause_condition.signalAll()
        finally:
            self._lock.unlock()

    def _wait_if_paused(self):
        self._lock.lock()

        try:
            while self._paused and not self._stopped:
                self._pause_condition.await()

            return not self._stopped

        finally:
            self._lock.unlock()

    def run(self):
        try:
            all_payloads=[]
            while not self._stopped:
                if not self._wait_if_paused():
                    return

                payloads = self.client.generate_wordlist()

                score = 0
                score_lines=[]

                for index, payload in enumerate(payloads):
                    if not self._wait_if_paused():
                        return

                    if payload in all_payloads:
                        score = score - 2
                        score_lines.append(payload+" -2")
                    else:
                        try:
                            raw_request = self._apply_payload(
                                self._http_request_template,
                                payload
                            )

                            (
                                status_code,
                                response_length,
                                request_text,
                                response_text
                            ) = self._make_request(raw_request)

                            if status_code == 200:
                                score = score + 1
                                score_lines.append(payload+" +1")


                            row = [
                                index,
                                payload,
                                status_code,
                                response_length,
                                request_text,
                                response_text
                            ]

                            all_payloads.append(payload)

                        except Exception as ex:
                            row = [
                                index,
                                payload,
                                "Error",
                                0,
                                "",
                                str(ex)
                            ]

                        SwingUtilities.invokeLater(
                            AddResultRow(
                                self._results_tablemodel,
                                row
                            )
                        )
                print(score)
                print(score_lines)
        except Exception as ex:
            print("Intruder worker error: {0}".format(str(ex)))