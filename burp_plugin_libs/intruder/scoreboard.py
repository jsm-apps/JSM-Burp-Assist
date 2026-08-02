class ScoreBoard():
    def __init__(self):
        self.score = 0
        self.score_lines = []

    def increaseScore(self, payload):
        self.score = score + 1
        self.score_lines.append(payload+" (+1 point)")

    def decreaseScore(self, payload):
        self.score = score - 2
        # dont add to score lines as we want score lines to contain positive results

    def getScore(self):
        return self.score

    def getScorelines(self):
            return self.score_lines