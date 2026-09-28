"""
logger.py - tiny presentation-friendly logger.

    [01] Message received          <- numbered pipeline steps
    [ATTACK] Message modified      <- tagged events
"""


class Logger:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.lines = []
        self._n = 0

    def _emit(self, line):
        self.lines.append(line)
        if self.verbose:
            print(line)

    def step(self, text):
        """Numbered pipeline step: [01], [02], ..."""
        self._n += 1
        self._emit(f"[{self._n:02d}] {text}")

    def detail(self, text):
        """Indented sub-line under the last step."""
        self._emit(f"     - {text}")

    def tag(self, tag, text):
        """Tagged event such as [ATTACK], [DETECTION], [RESULT]."""
        self._emit(f"[{tag}] {text}")
