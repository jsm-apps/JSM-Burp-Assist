from java.lang import Runnable

class SwingCallback(Runnable):
    """
    Wraps a Python callable so it can safely be passed to
    SwingUtilities.invokeLater().
    """

    def __init__(self, callback):
        self.callback = callback

    def run(self):
        self.callback()