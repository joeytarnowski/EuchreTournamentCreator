class Player:
    def __init__(self, name):
        self.name = name
        self.score = []
        self.partners = set()
        self.byes = 0

    def __repr__(self):
        return self.name

    def add_score(self, game, points):
        if len(self.score) >= game:
            print(game)
            self.score[game-1] = points
        else:
            self.score.append(points)